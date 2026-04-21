"""Journal auditable des interactions avec l'IA (conformité LPD).

Chaque appel module/IA est logué dans un fichier quotidien horodaté.
Format JSONL (une ligne = un événement JSON) pour exploitation facile.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from _app.core.config import get_config


class Logger:
    """Logger applicatif + journal métier JSONL."""

    def __init__(self, log_dir: Path | None = None):
        cfg = get_config()
        self.log_dir: Path = log_dir or cfg.chemin_logs
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Logger technique (erreurs, warnings, info debug)
        self._tech = logging.getLogger("swisshr")
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
        """Écrit un événement auditable (module exécuté, prompt, réponse, sources)."""
        record = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "event": event,
            **payload,
        }
        with self._audit_path().open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

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
