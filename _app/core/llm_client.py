"""Client LM Studio.

LM Studio expose une API compatible OpenAI sur http://localhost:1234/v1
par défaut. On utilise requests pour :
    - tester la disponibilité du serveur (ping),
    - lister les modèles chargés,
    - générer du texte (chat/completions), avec ou sans streaming,
    - interrompre proprement une génération en cours.

Aucune dépendance au SDK OpenAI : on reste minimaliste pour que le
packaging PyInstaller soit plus léger, et on refuse toute connexion
sortante (garde-fou contre une fuite accidentelle hors poste).
"""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from urllib.parse import urlparse

import requests

from _app.core.config import get_config
from _app.core.logger import get_logger

# Hôtes considérés comme locaux. Toute autre URL est refusée au démarrage,
# pour honorer l'engagement "air-gapped / hors ligne" du cahier des charges.
_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1", "0.0.0.0"})


class LLMStatus(StrEnum):
    READY = "ready"              # serveur détecté + au moins un modèle chargé
    NO_MODEL = "no_model"        # serveur détecté mais aucun modèle chargé
    UNREACHABLE = "unreachable"  # serveur absent / LM Studio non démarré
    ERROR = "error"              # autre erreur


@dataclass
class LLMStatusInfo:
    status: LLMStatus
    message: str
    models: list[str]
    active_model: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "message": self.message,
            "models": self.models,
            "active_model": self.active_model,
        }


class GenerationCancelled(Exception):
    """Levée quand un appel au cancel_event interrompt un stream en cours."""


class LLMClient:
    """Client HTTP vers LM Studio."""

    def __init__(self, base_url: str | None = None, model: str | None = None):
        cfg = get_config()
        self.base_url = (base_url or cfg.lm_studio_url).rstrip("/")
        self._ensure_local(self.base_url)
        self._configured_model = model if model is not None else cfg.lm_studio_model
        self._detected_model: str | None = None
        self.timeout = cfg.lm_studio_timeout
        self.connect_timeout = cfg.lm_studio_connect_timeout
        self._log = get_logger()

    # --- Garde-fou hors ligne ---------------------------------------------

    @staticmethod
    def _ensure_local(url: str) -> None:
        host = (urlparse(url).hostname or "").lower()
        if host not in _LOCAL_HOSTS:
            raise RuntimeError(
                f"URL LM Studio refusée : {url!r}. Seuls les hôtes locaux "
                f"({', '.join(sorted(_LOCAL_HOSTS))}) sont autorisés pour "
                f"garantir le fonctionnement hors ligne."
            )

    # --- Modèle actif ------------------------------------------------------

    @property
    def model(self) -> str:
        """Modèle effectivement utilisé : config > dernier détecté > chaîne vide."""
        return self._configured_model or self._detected_model or ""

    # --- Détection serveur -------------------------------------------------

    def status(self) -> LLMStatusInfo:
        """Vérifie que LM Studio répond et qu'un modèle est chargé."""
        try:
            r = requests.get(
                f"{self.base_url}/models",
                timeout=(self.connect_timeout, 5),
            )
        except requests.exceptions.ConnectionError:
            return LLMStatusInfo(
                LLMStatus.UNREACHABLE,
                "LM Studio n'est pas détecté. Lancez LM Studio puis "
                "cliquez sur \"Start Server\" dans l'onglet Developer.",
                [],
            )
        except requests.exceptions.Timeout:
            return LLMStatusInfo(
                LLMStatus.UNREACHABLE,
                "LM Studio ne répond pas dans les temps.",
                [],
            )
        except Exception as exc:
            self._log.error(f"LM Studio /models a levé : {exc!r}")
            return LLMStatusInfo(LLMStatus.ERROR, f"Erreur inattendue : {exc}", [])

        if r.status_code != 200:
            return LLMStatusInfo(
                LLMStatus.ERROR,
                f"LM Studio a répondu avec le code {r.status_code}.",
                [],
            )

        try:
            data = r.json()
        except ValueError:
            return LLMStatusInfo(LLMStatus.ERROR, "Réponse /models non-JSON.", [])

        models = [m.get("id", "?") for m in data.get("data", [])]
        if not models:
            return LLMStatusInfo(
                LLMStatus.NO_MODEL,
                "LM Studio tourne mais aucun modèle n'est chargé. "
                "Chargez un modèle puis cliquez sur \"Start Server\".",
                [],
            )

        # Mise à jour du modèle actif (auto-détection si non-configuré).
        if self._configured_model and self._configured_model in models:
            active = self._configured_model
        else:
            active = models[0]
        self._detected_model = active

        return LLMStatusInfo(
            LLMStatus.READY,
            f"IA prête — modèle actif : {active}",
            models,
            active_model=active,
        )

    # --- Génération --------------------------------------------------------

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
        stream: bool = False,
        cancel_event: threading.Event | None = None,
    ) -> str | Iterator[str]:
        """Appelle /v1/chat/completions. Retourne une string ou un itérateur de tokens.

        Si `cancel_event` est fourni et déclenché pendant un stream, la
        génération s'arrête proprement et lève GenerationCancelled.
        """
        if not self.model:
            # Dernière tentative d'auto-détection avant d'abandonner.
            info = self.status()
            if info.status is not LLMStatus.READY:
                raise RuntimeError(info.message)

        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        if stream:
            return self._generate_stream(payload, cancel_event)
        return self._generate_once(payload)

    def _generate_once(self, payload: dict[str, Any]) -> str:
        r = requests.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            timeout=(self.connect_timeout, self.timeout),
        )
        r.raise_for_status()
        data = r.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise RuntimeError(f"Réponse LM Studio inattendue : {data}") from exc

    def _generate_stream(
        self,
        payload: dict[str, Any],
        cancel_event: threading.Event | None,
    ) -> Iterator[str]:
        with requests.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            timeout=(self.connect_timeout, self.timeout),
            stream=True,
        ) as r:
            r.raise_for_status()
            for line in r.iter_lines(decode_unicode=True):
                if cancel_event is not None and cancel_event.is_set():
                    raise GenerationCancelled()
                if not line or not line.startswith("data:"):
                    continue
                chunk = line[len("data:"):].strip()
                if chunk == "[DONE]":
                    return
                try:
                    obj = json.loads(chunk)
                except json.JSONDecodeError:
                    continue
                delta = (
                    obj.get("choices", [{}])[0]
                    .get("delta", {})
                    .get("content")
                )
                if delta:
                    yield delta

    # --- Helper pour les modules -----------------------------------------

    def time_generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> tuple[str, int]:
        """Génération non-stream qui retourne (réponse, durée_ms).

        Utilisée par les modules qui veulent renseigner un journal d'audit.
        """
        t0 = time.monotonic()
        text = self.generate(
            prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )
        duration_ms = int((time.monotonic() - t0) * 1000)
        assert isinstance(text, str)
        return text, duration_ms
