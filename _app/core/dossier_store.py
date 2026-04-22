"""Gestion du dossier collaborateur.

Un dossier = une arborescence locale, une par collaborateur-rice pour
lequel un certificat (ou une autre pièce RH) est en préparation. Cf.
§16-17 de l'analyse fonctionnelle certificats.

Arborescence créée :

    Dossiers/
      [NOM_prenom_YYYY]/
        dossier.json                ← métadonnées + état wizard
        01_donnees_contractuelles/
        02_documents_sources/
        03_questionnaires_managers/
          vierges/
          remplis/
        04_donnees_consolidees/
        05_brouillons/
        06_certificat_final/
        07_audit/

Le nom de dossier reste lisible à l'œil nu : un RH qui fouille
l'Explorateur Windows à 3 ans doit reconnaître instantanément de qui
il s'agit, sans hash obfusqué.

Les données sensibles ne sortent jamais de ce dossier. Tout est JSON
pour rester grep-able et auditable.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from _app.core.config import get_config
from _app.core.logger import get_logger
from _app.core.paths import safe_within

# Sous-dossiers standards d'un dossier collaborateur.
SUBFOLDERS: tuple[str, ...] = (
    "01_donnees_contractuelles",
    "02_documents_sources",
    "03_questionnaires_managers/vierges",
    "03_questionnaires_managers/remplis",
    "04_donnees_consolidees",
    "05_brouillons",
    "06_certificat_final",
    "07_audit",
)

META_FILENAME = "dossier.json"

_SLUG_RE = re.compile(r"[^A-Za-z0-9]+")


def _slug_collab(nom: str, prenom: str, annee: int) -> str:
    """Nom de dossier lisible : NOM_prenom_YYYY, sans caractères spéciaux."""
    def clean(text: str) -> str:
        norm = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
        return _SLUG_RE.sub("_", norm).strip("_")

    nom_c = clean(nom).upper() or "COLLAB"
    prenom_c = clean(prenom).lower() or "inconnu"
    return f"{nom_c}_{prenom_c}_{annee}"[:96]


@dataclass
class Collaborateur:
    """Identité minimale d'un-e collaborateur-rice (cf. §4 champs obligatoires)."""

    nom: str = ""
    prenom: str = ""
    date_naissance: str = ""      # ISO yyyy-mm-dd
    lieu_origine: str = ""         # spécificité suisse

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Dossier:
    """Un dossier collaborateur persisté sur le disque."""

    id: str                        # = nom de sous-dossier
    racine: Path
    collaborateur: Collaborateur
    entite_id: str = ""             # id de l'entité employeur (EntityManager)
    type_document: str = ""         # "certificat_final" | "certificat_intermediaire" | "attestation"
    langue: str = "fr"              # "fr" | "de" | "en"
    cree_le: str = ""
    maj_le: str = ""
    wizard_state: dict[str, Any] = field(default_factory=dict)
    # Champ libre pour tout module qui veut persister des données par dossier.
    # Ex: {"certificats": {"evaluations": {...}}}
    modules: dict[str, Any] = field(default_factory=dict)

    # --- Chemins ---------------------------------------------------------

    @property
    def path_meta(self) -> Path:
        return self.racine / META_FILENAME

    def subfolder(self, name: str) -> Path:
        """Accès sûr à un sous-dossier standard (empêche ../)."""
        if name not in SUBFOLDERS:
            raise ValueError(f"Sous-dossier inconnu : {name!r}")
        target = self.racine / name
        resolved = safe_within(target, self.racine)
        if resolved is None:
            raise ValueError(f"Chemin refusé (hors dossier) : {name!r}")
        return target

    # --- Sérialisation ---------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "collaborateur": self.collaborateur.as_dict(),
            "entite_id": self.entite_id,
            "type_document": self.type_document,
            "langue": self.langue,
            "cree_le": self.cree_le,
            "maj_le": self.maj_le,
            "wizard_state": self.wizard_state,
            "modules": self.modules,
        }

    def save(self) -> None:
        self.maj_le = datetime.now().isoformat(timespec="seconds")
        self.path_meta.write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    @classmethod
    def from_disk(cls, racine: Path) -> Dossier | None:
        meta = racine / META_FILENAME
        if not meta.exists():
            return None
        try:
            data = json.loads(meta.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        collab = Collaborateur(**data.get("collaborateur", {}))
        return cls(
            id=data.get("id", racine.name),
            racine=racine,
            collaborateur=collab,
            entite_id=data.get("entite_id", ""),
            type_document=data.get("type_document", ""),
            langue=data.get("langue", "fr"),
            cree_le=data.get("cree_le", ""),
            maj_le=data.get("maj_le", ""),
            wizard_state=data.get("wizard_state", {}),
            modules=data.get("modules", {}),
        )


class DossierStore:
    """CRUD sur Dossiers/. Un seul store par process."""

    def __init__(self, racine: Path | None = None):
        cfg = get_config()
        self._log = get_logger()
        self._racine: Path = racine or cfg.chemin_dossiers
        self._racine.mkdir(parents=True, exist_ok=True)

    # --- CRUD ------------------------------------------------------------

    def create(
        self,
        *,
        nom: str,
        prenom: str,
        entite_id: str = "",
        type_document: str = "",
        langue: str = "fr",
        date_naissance: str = "",
        lieu_origine: str = "",
    ) -> Dossier:
        if not nom.strip() or not prenom.strip():
            raise ValueError("Nom et prénom sont obligatoires pour créer un dossier.")
        if langue not in {"fr", "de", "en"}:
            raise ValueError(f"Langue non supportée : {langue!r}")

        annee = datetime.now().year
        base_id = _slug_collab(nom, prenom, annee)
        dossier_id = base_id
        i = 2
        while (self._racine / dossier_id).exists():
            dossier_id = f"{base_id}_{i}"
            i += 1

        target = self._racine / dossier_id
        if safe_within(target, self._racine) is None:
            raise ValueError("Chemin de dossier invalide.")
        target.mkdir(parents=True, exist_ok=False)

        for sub in SUBFOLDERS:
            (target / sub).mkdir(parents=True, exist_ok=True)

        now = datetime.now().isoformat(timespec="seconds")
        dossier = Dossier(
            id=dossier_id,
            racine=target,
            collaborateur=Collaborateur(
                nom=nom.strip(),
                prenom=prenom.strip(),
                date_naissance=date_naissance.strip(),
                lieu_origine=lieu_origine.strip(),
            ),
            entite_id=entite_id.strip(),
            type_document=type_document.strip(),
            langue=langue,
            cree_le=now,
            maj_le=now,
        )
        dossier.save()
        self._log.info(f"Dossier créé : {dossier_id}")
        return dossier

    def get(self, dossier_id: str) -> Dossier | None:
        target = self._racine / dossier_id
        if safe_within(target, self._racine) is None or not target.is_dir():
            return None
        return Dossier.from_disk(target)

    def list(self) -> list[dict[str, Any]]:
        """Liste synthétique (un dict par dossier) pour l'UI."""
        out: list[dict[str, Any]] = []
        for sub in sorted(self._racine.iterdir(), key=lambda p: p.name):
            if not sub.is_dir():
                continue
            dossier = Dossier.from_disk(sub)
            if dossier is None:
                continue
            out.append({
                "id": dossier.id,
                "collaborateur": f"{dossier.collaborateur.prenom} {dossier.collaborateur.nom}".strip(),
                "entite_id": dossier.entite_id,
                "type_document": dossier.type_document,
                "langue": dossier.langue,
                "cree_le": dossier.cree_le,
                "maj_le": dossier.maj_le,
                "wizard_step": dossier.wizard_state.get("step", ""),
            })
        return out

    def delete(self, dossier_id: str) -> bool:
        """Suppression à la demande (art. 32 nLPD). Soft-delete via rename.

        On déplace vers `Dossiers/_supprimes/` plutôt que d'effacer définitivement :
        - conservation 10 ans possible côté archive/audit,
        - récupération en cas d'erreur de clic.
        """
        src = self._racine / dossier_id
        if safe_within(src, self._racine) is None or not src.is_dir():
            return False
        trash = self._racine / "_supprimes"
        trash.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = trash / f"{dossier_id}__{stamp}"
        src.rename(dst)
        self._log.info(f"Dossier déplacé en corbeille : {dossier_id} → {dst.name}")
        return True

    @property
    def racine(self) -> Path:
        return self._racine
