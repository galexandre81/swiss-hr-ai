"""Gestion des entités (sociétés clientes) avec leurs logos et signatures."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from _app.core.config import get_config
from _app.core.logger import get_logger


@dataclass
class Entity:
    id: str
    nom: str
    dossier: Path
    forme_juridique: str = ""
    adresse: str = ""
    telephone: str = ""
    email: str = ""
    signataire_nom: str = ""
    signataire_fonction: str = ""
    logo_fichier: str = "logo.png"
    signature_fichier: str = "signature.png"
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def logo_path(self) -> Path:
        return self.dossier / self.logo_fichier

    @property
    def signature_path(self) -> Path:
        return self.dossier / self.signature_fichier

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "nom": self.nom,
            "forme_juridique": self.forme_juridique,
            "adresse": self.adresse,
            "telephone": self.telephone,
            "email": self.email,
            "signataire_nom": self.signataire_nom,
            "signataire_fonction": self.signataire_fonction,
            "logo_present": self.logo_path.exists(),
            "signature_presente": self.signature_path.exists(),
        }


class EntityManager:
    """Scanne Entities/ et expose les entités disponibles + celle active."""

    def __init__(self):
        cfg = get_config()
        self._log = get_logger()
        self._entities_dir: Path = cfg.chemin_entities
        self._entities: dict[str, Entity] = {}
        self._active_id: str | None = None
        self.rescan()
        # Choix de l'entité active : config, sinon première en ordre alphabétique
        if cfg.entite_active and cfg.entite_active in self._entities:
            self._active_id = cfg.entite_active
        elif self._entities:
            self._active_id = sorted(self._entities)[0]

    def rescan(self) -> None:
        """Relit le dossier Entities/ (utile si l'utilisateur en a ajouté une)."""
        self._entities.clear()
        if not self._entities_dir.exists():
            return
        for sub in sorted(self._entities_dir.iterdir()):
            if not sub.is_dir():
                continue
            cfg_file = sub / "config.json"
            if not cfg_file.exists():
                self._log.warning(f"Entité ignorée (pas de config.json) : {sub.name}")
                continue
            try:
                raw = json.loads(cfg_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                self._log.error(f"config.json invalide dans {sub.name} : {exc}")
                continue
            entity = Entity(
                id=raw.get("id", sub.name),
                nom=raw.get("nom", sub.name),
                dossier=sub,
                forme_juridique=raw.get("forme_juridique", ""),
                adresse=raw.get("adresse", ""),
                telephone=raw.get("telephone", ""),
                email=raw.get("email", ""),
                signataire_nom=raw.get("signataire", {}).get("nom", ""),
                signataire_fonction=raw.get("signataire", {}).get("fonction", ""),
                logo_fichier=raw.get("logo_fichier", "logo.png"),
                signature_fichier=raw.get("signature_fichier", "signature.png"),
                raw=raw,
            )
            self._entities[entity.id] = entity

    def all(self) -> list[Entity]:
        return list(self._entities.values())

    @property
    def active(self) -> Entity | None:
        if self._active_id is None:
            return None
        return self._entities.get(self._active_id)

    def set_active(self, entity_id: str) -> Entity | None:
        if entity_id in self._entities:
            self._active_id = entity_id
            self._log.info(f"Entité active changée : {entity_id}")
            return self._entities[entity_id]
        return None
