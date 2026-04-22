"""Journal d'audit par dossier collaborateur (append-only).

Distinct du `logger.py` applicatif : ici on ne trace QUE ce qui concerne
un certificat donné. Un fichier par certificat émis, horodaté :

    Dossiers/<id>/07_audit/trace_YYYYMMDD_HHMMSS.json

Contenu (cf. §13 + §21 analyse fonctionnelle) :
- inputs bruts consolidés
- version de l'outil / bibliothèques / modèle LLM
- identité auteur RH + horodatage
- décisions RH sur zones grises
- versions successives du brouillon
- alertes déclenchées + décisions prises pour chacune
- hash SHA-256 du certificat final

Immuable : on écrit des entrées en append, jamais on n'édite une entrée
existante. La reprise (ex: même dossier à un nouveau passage du wizard)
ouvre une nouvelle trace — on n'écrase pas l'historique.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from _app.core.logger import get_logger
from _app.core.paths import safe_within

TRACE_SUBFOLDER = "07_audit"


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _stamp_filename() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def sha256_of(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class AuditEvent:
    """Une ligne du journal."""

    kind: str
    at: str = field(default_factory=_now)
    payload: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "at": self.at, **self.payload}


class AuditTrail:
    """Trace d'audit liée à un dossier — une par certificat en cours.

    On utilise du **JSONL** côté fichier (une ligne = un événement), ce
    qui permet l'append immédiat et la tolérance aux interruptions. À la
    finalisation, on peut exporter le JSONL en un JSON consolidé si
    besoin (lisible par un avocat).
    """

    def __init__(self, dossier_racine: Path, *, filename: str | None = None):
        subdir = dossier_racine / TRACE_SUBFOLDER
        subdir.mkdir(parents=True, exist_ok=True)
        if safe_within(subdir, dossier_racine) is None:
            raise ValueError("Chemin d'audit invalide.")
        name = filename or f"trace_{_stamp_filename()}.jsonl"
        self._file: Path = subdir / name
        if safe_within(self._file, dossier_racine) is None:
            raise ValueError("Chemin d'audit invalide.")
        self._log = get_logger()
        # Header implicite : création
        if not self._file.exists():
            self.append("trail_opened", meta={"file": self._file.name})

    # --- Écriture --------------------------------------------------------

    def append(self, kind: str, **payload: Any) -> None:
        event = AuditEvent(kind=kind, payload=payload)
        with self._file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event.as_dict(), ensure_ascii=False) + "\n")

    def record_decision(self, zone: str, choix: str, *, justification: str = "",
                        auteur: str = "") -> None:
        """Décision RH sur une zone grise (§7)."""
        self.append(
            "zone_grise_decision",
            zone=zone,
            choix=choix,
            justification=justification,
            auteur=auteur,
        )

    def record_alert(self, code: str, message: str, *, resolution: str = "") -> None:
        """Alerte déclenchée par un garde-fou + réponse du RH."""
        self.append("alerte", code=code, message=message, resolution=resolution)

    def record_draft(self, version: int, texte: str) -> None:
        self.append(
            "brouillon",
            version=version,
            sha256=sha256_of(texte),
            length=len(texte),
        )

    def record_llm_call(self, *, module: str, temperature: float,
                        duration_ms: int, status: str,
                        prompt_hash: str, response_hash: str,
                        error: str = "") -> None:
        self.append(
            "llm_call",
            module=module,
            temperature=temperature,
            duration_ms=duration_ms,
            status=status,
            prompt_sha256_16=prompt_hash[:16],
            response_sha256_16=response_hash[:16],
            error=error,
        )

    def seal(self, certificate_text: str, *, outputs: list[str] | None = None) -> dict[str, Any]:
        """Écrit l'empreinte du certificat final. Le trail reste ouvert
        (append-only) mais l'événement `seal` marque la finalisation.

        Retourne la dernière entrée pour info UI.
        """
        digest = sha256_of(certificate_text)
        payload = {
            "sha256": digest,
            "length": len(certificate_text),
            "outputs": outputs or [],
        }
        self.append("seal", **payload)
        return payload

    # --- Lecture ---------------------------------------------------------

    @property
    def path(self) -> Path:
        return self._file

    def events(self) -> list[dict[str, Any]]:
        if not self._file.exists():
            return []
        out: list[dict[str, Any]] = []
        for line in self._file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                self._log.warning(f"Ligne trace non-JSON ignorée : {line[:80]!r}")
        return out

    def export_consolidated(self) -> dict[str, Any]:
        """Regroupe toutes les entrées en un seul JSON (utile pour un avocat)."""
        return {
            "file": self._file.name,
            "events": self.events(),
            "exported_at": _now(),
        }
