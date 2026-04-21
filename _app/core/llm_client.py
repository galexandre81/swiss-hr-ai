"""Client LM Studio.

LM Studio expose une API compatible OpenAI sur http://localhost:1234/v1
par défaut. On utilise donc simplement requests pour :
    - tester la disponibilité du serveur (ping),
    - lister les modèles chargés,
    - générer du texte (chat/completions), avec ou sans streaming.

Aucune dépendance au SDK OpenAI : on reste minimaliste pour que le
packaging PyInstaller soit plus léger et que rien ne tente de parler
à un serveur distant.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterator

import requests

from _app.core.config import get_config
from _app.core.logger import get_logger


class LLMStatus(str, Enum):
    READY = "ready"            # serveur détecté + au moins un modèle chargé
    NO_MODEL = "no_model"      # serveur détecté mais aucun modèle chargé
    UNREACHABLE = "unreachable"  # serveur absent / LM Studio non démarré
    ERROR = "error"            # autre erreur


@dataclass
class LLMStatusInfo:
    status: LLMStatus
    message: str
    models: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "message": self.message,
            "models": self.models,
        }


class LLMClient:
    """Client HTTP vers LM Studio."""

    def __init__(self, base_url: str | None = None, model: str | None = None):
        cfg = get_config()
        self.base_url = (base_url or cfg.lm_studio_url).rstrip("/")
        self.model = model or cfg.lm_studio_model
        self.timeout = cfg.lm_studio_timeout
        self._log = get_logger()

    # --- Détection serveur -------------------------------------------------

    def status(self) -> LLMStatusInfo:
        """Vérifie que LM Studio répond et qu'un modèle est chargé."""
        try:
            r = requests.get(f"{self.base_url}/models", timeout=3)
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

        data = r.json()
        models = [m.get("id", "?") for m in data.get("data", [])]
        if not models:
            return LLMStatusInfo(
                LLMStatus.NO_MODEL,
                "LM Studio tourne mais aucun modèle n'est chargé. "
                "Chargez Qwen 3.5 9B dans LM Studio.",
                [],
            )
        return LLMStatusInfo(
            LLMStatus.READY,
            f"IA prête — modèle actif : {models[0]}",
            models,
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
    ) -> str | Iterator[str]:
        """Appelle /v1/chat/completions. Retourne une string ou un itérateur de tokens."""
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
            return self._generate_stream(payload)
        return self._generate_once(payload)

    def _generate_once(self, payload: dict[str, Any]) -> str:
        r = requests.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            timeout=self.timeout,
        )
        r.raise_for_status()
        data = r.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise RuntimeError(f"Réponse LM Studio inattendue : {data}") from exc

    def _generate_stream(self, payload: dict[str, Any]) -> Iterator[str]:
        with requests.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            timeout=self.timeout,
            stream=True,
        ) as r:
            r.raise_for_status()
            for line in r.iter_lines(decode_unicode=True):
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
