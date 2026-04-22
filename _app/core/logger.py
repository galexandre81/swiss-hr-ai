"""Journal auditable des interactions avec l'IA (conformité LPD).

Chaque appel module/IA est logué dans un fichier quotidien horodaté.
Format JSONL (une ligne = un événement JSON) pour exploitation facile.

Par défaut, le contenu des prompts et des réponses n'est PAS stocké —
on garde seulement un hash SHA-256 tronqué + la longueur, ce qui suffit
à prouver qu'une génération a eu lieu sans recopier de données personnelles.
Pour un audit légal plus poussé, passer `audit_log_prompts=true` dans
config.json (à décider avec le DPO du client).
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from _app.core.config import get_config


def _fingerprint(text: str) -> dict[str, Any]:
    """Empreinte non-réversible d'un texte : hash tronqué + longueur."""
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    return {"sha256_16": digest, "length": len(text)}


class Logger:
    """Logger applicatif + journal métier JSONL."""

    def __init__(self, log_dir: Path | None = None):
        cfg = get_config()
        self.log_dir: Path = log_dir or cfg.chemin_logs
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._log_full_content: bool = bool(cfg.audit_log_prompts)

        # Logger technique (erreurs, warnings, info debug).
        self._tech = logging.getLogger("arhiane")
        if not self._tech.handlers:
            self._tech.setLevel(logging.INFO)
            handler = logging.FileHandler(
                self.log_dir / f"app_{datetime.now():%Y-%m-%d}.log",
                encoding="utf-8",
            )
            handler.setFormatter(
                logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
            )
            self._tech.addHandler(handler)

    # --- Journal métier (audit LPD) ---------------------------------------

    def _audit_path(self) -> Path:
        return self.log_dir / f"audit_{datetime.now():%Y-%m-%d}.jsonl"

    def audit(self, event: str, **payload: Any) -> None:
        """Écrit un événement auditable (ligne JSON)."""
        record = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "event": event,
            **payload,
        }
        with self._audit_path().open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def audit_llm_call(
        self,
        *,
        module: str,
        entity: str | None,
        temperature: float,
        duration_ms: int,
        status: str,
        prompt: str,
        response: str,
        sources: list[dict[str, Any]] | None = None,
        error: str | None = None,
    ) -> None:
        """Événement standardisé pour tout appel IA, minimal par défaut.

        Si audit_log_prompts=false, on n'enregistre que les empreintes.
        Si true, on stocke aussi le texte intégral (à activer uniquement
        sur accord explicite du DPO du client).
        """
        payload: dict[str, Any] = {
            "module": module,
            "entity": entity,
            "temperature": temperature,
            "duration_ms": duration_ms,
            "status": status,
            "prompt": _fingerprint(prompt),
            "response": _fingerprint(response),
        }
        if sources:
            payload["sources"] = sources
        if error:
            payload["error"] = error
        if self._log_full_content:
            payload["prompt_full"] = prompt
            payload["response_full"] = response
        self.audit("llm_call", **payload)

    # --- Logs techniques --------------------------------------------------

    def info(self, msg: str) -> None:
        self._tech.info(msg)

    def warning(self, msg: str) -> None:
        self._tech.warning(msg)

    def error(self, msg: str) -> None:
        self._tech.error(msg)


_cached_logger: Logger | None = None


def get_logger() -> Logger:
    """Singleton — un seul Logger pour toute l'application."""
    global _cached_logger
    if _cached_logger is None:
        _cached_logger = Logger()
    return _cached_logger


def reset_cache() -> None:
    """Utile pour les tests."""
    global _cached_logger
    _cached_logger = None
