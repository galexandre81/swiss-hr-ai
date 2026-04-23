"""Gestion des entités (sociétés clientes) avec leurs logos et signatures."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from _app.core.config import get_config
from _app.core.logger import get_logger
from _app.core.paths import safe_within

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(text: str, *, fallback: str = "entite") -> str:
    """Nom de dossier neutre : ASCII minuscule, underscores, longueur bornée."""
    norm = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    slug = _SLUG_RE.sub("_", norm.lower()).strip("_")
    return (slug or fallback)[:48]


# Politiques d'écriture inclusive supportées (module Cahier des charges + autres).
POLITIQUES_INCLUSIF = frozenset({"doublets", "neutre", "point_median", "desactive"})
# Langues principales supportées.
LANGUES_PRINCIPALES = frozenset({"fr", "de"})


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
    # Champs transverses utilisés par plusieurs modules.
    # Introduits pour le module Cahier des charges, rétrocompatibles.
    langue_principale: str = "fr"  # "fr" | "de"
    politique_inclusif: str = "neutre"  # "doublets" | "neutre" | "point_median" | "desactive"
    cct_applicable: str = ""  # identifiant CCT (ex: "hotellerie_restauration"), vide si aucune
    competences_socles: list[str] = field(default_factory=list)
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
            "langue_principale": self.langue_principale,
            "politique_inclusif": self.politique_inclusif,
            "cct_applicable": self.cct_applicable,
            "competences_socles": list(self.competences_socles),
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
            # Garde-fou : ignore tout dossier qui sortirait de Entities/ via un lien.
            if safe_within(sub, self._entities_dir) is None:
                self._log.warning(f"Entité ignorée (chemin suspect) : {sub.name}")
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
            # Normalisation des champs transverses optionnels (rétrocompat :
            # une config.json antérieure ne contient rien pour ces clés).
            langue = raw.get("langue_principale", "fr")
            if langue not in LANGUES_PRINCIPALES:
                self._log.warning(
                    f"Langue principale inconnue dans {sub.name} : {langue!r}. "
                    f"Repli sur 'fr'."
                )
                langue = "fr"
            politique = raw.get("politique_inclusif", "neutre")
            if politique not in POLITIQUES_INCLUSIF:
                self._log.warning(
                    f"Politique inclusif inconnue dans {sub.name} : {politique!r}. "
                    f"Repli sur 'neutre'."
                )
                politique = "neutre"
            socles = raw.get("competences_socles", [])
            if not isinstance(socles, list):
                self._log.warning(
                    f"competences_socles non-liste dans {sub.name} — ignoré."
                )
                socles = []
            socles = [str(s).strip() for s in socles if str(s).strip()]

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
                langue_principale=langue,
                politique_inclusif=politique,
                cct_applicable=str(raw.get("cct_applicable", "") or "").strip(),
                competences_socles=socles,
                raw=raw,
            )
            self._entities[entity.id] = entity

    def create(self, data: dict[str, Any]) -> Entity:
        """Crée une nouvelle entité à partir des champs du formulaire UI.

        Génère un dossier `Entities/<slug>/` contenant un `config.json`.
        Lève ValueError si le nom est vide ou si le slug entre en conflit.
        """
        nom = (data.get("nom") or "").strip()
        if not nom:
            raise ValueError("Le nom de l'entité est obligatoire.")

        base_slug = slugify(nom)
        slug = base_slug
        i = 2
        while (self._entities_dir / slug).exists():
            slug = f"{base_slug}_{i}"
            i += 1

        target = self._entities_dir / slug
        if safe_within(target, self._entities_dir) is None:
            raise ValueError("Chemin d'entité invalide.")
        target.mkdir(parents=True, exist_ok=False)

        # Champs transverses optionnels à la création. Valeurs par défaut si absents.
        langue = (data.get("langue_principale") or "fr").strip()
        if langue not in LANGUES_PRINCIPALES:
            langue = "fr"
        politique = (data.get("politique_inclusif") or "neutre").strip()
        if politique not in POLITIQUES_INCLUSIF:
            politique = "neutre"
        socles_in = data.get("competences_socles") or []
        if not isinstance(socles_in, list):
            socles_in = []
        socles = [str(s).strip() for s in socles_in if str(s).strip()]

        config = {
            "id": slug,
            "nom": nom,
            "forme_juridique": (data.get("forme_juridique") or "").strip(),
            "adresse": (data.get("adresse") or "").strip(),
            "telephone": (data.get("telephone") or "").strip(),
            "email": (data.get("email") or "").strip(),
            "signataire": {
                "nom": (data.get("signataire_nom") or "").strip(),
                "fonction": (data.get("signataire_fonction") or "").strip(),
            },
            "logo_fichier": "logo.png",
            "signature_fichier": "signature.png",
            "langue_principale": langue,
            "politique_inclusif": politique,
            "cct_applicable": (data.get("cct_applicable") or "").strip(),
            "competences_socles": socles,
        }
        (target / "config.json").write_text(
            json.dumps(config, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        (target / "LISEZ-MOI.txt").write_text(
            "Déposez ici votre logo (logo.png) et votre signature (signature.png).\n"
            "Vous pouvez modifier config.json à la main pour ajuster les informations.\n",
            encoding="utf-8",
        )
        self._log.info(f"Entité créée : {slug} ({nom})")
        self.rescan()
        if self._active_id is None:
            self._active_id = slug
        return self._entities[slug]

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

    def set_asset(self, entity_id: str, kind: str, source_path: Path) -> Entity:
        """Copie un fichier image vers le dossier entité comme logo/signature.

        `kind` ∈ {"logo", "signature"}. L'extension du fichier source est
        préservée, et le champ `logo_fichier` / `signature_fichier` du
        config.json est mis à jour en conséquence.
        """
        if kind not in {"logo", "signature"}:
            raise ValueError(f"Type d'asset inconnu : {kind!r}")
        entity = self._entities.get(entity_id)
        if entity is None:
            raise ValueError(f"Entité inconnue : {entity_id!r}")
        if not source_path.is_file():
            raise ValueError("Fichier source introuvable.")
        ext = source_path.suffix.lower()
        if ext not in {".png", ".jpg", ".jpeg", ".webp"}:
            raise ValueError(
                f"Format non supporté ({ext}). Utilisez PNG, JPG ou WEBP."
            )
        # Cible : <entity>/<kind>.<ext>. On écrase l'éventuel ancien fichier.
        target = entity.dossier / f"{kind}{ext}"
        if safe_within(target, entity.dossier) is None:
            raise ValueError("Chemin invalide.")
        # Retire les anciens assets du même kind (au cas où l'extension change).
        for old_ext in (".png", ".jpg", ".jpeg", ".webp"):
            old = entity.dossier / f"{kind}{old_ext}"
            if old.exists() and old != target:
                old.unlink()
        import shutil
        shutil.copy2(source_path, target)

        # Met à jour config.json
        cfg_file = entity.dossier / "config.json"
        try:
            data = json.loads(cfg_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        key = "logo_fichier" if kind == "logo" else "signature_fichier"
        data[key] = target.name
        cfg_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        self._log.info(f"{kind} mis à jour pour entité {entity_id} : {target.name}")
        self.rescan()
        return self._entities[entity_id]

    def update(self, entity_id: str, data: dict[str, Any]) -> Entity:
        """Met à jour les champs éditables d'une entité existante.

        Champs acceptés : nom, forme_juridique, adresse, telephone, email,
        signataire_nom, signataire_fonction. L'id du dossier reste stable
        (renommer le dossier casserait les références dans les dossiers
        collaborateurs qui pointent dessus).
        """
        entity = self._entities.get(entity_id)
        if entity is None:
            raise ValueError(f"Entité inconnue : {entity_id!r}")
        cfg_file = entity.dossier / "config.json"
        try:
            current = json.loads(cfg_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            current = {}

        if "nom" in data:
            nom = (data.get("nom") or "").strip()
            if not nom:
                raise ValueError("Le nom de l'entité est obligatoire.")
            current["nom"] = nom
        for key in ("forme_juridique", "adresse", "telephone", "email", "cct_applicable"):
            if key in data:
                current[key] = (data.get(key) or "").strip()
        if "signataire_nom" in data or "signataire_fonction" in data:
            current.setdefault("signataire", {})
            if "signataire_nom" in data:
                current["signataire"]["nom"] = (data.get("signataire_nom") or "").strip()
            if "signataire_fonction" in data:
                current["signataire"]["fonction"] = (data.get("signataire_fonction") or "").strip()
        if "langue_principale" in data:
            langue = (data.get("langue_principale") or "fr").strip()
            if langue not in LANGUES_PRINCIPALES:
                raise ValueError(
                    f"Langue principale invalide : {langue!r}. "
                    f"Valeurs admises : {sorted(LANGUES_PRINCIPALES)}."
                )
            current["langue_principale"] = langue
        if "politique_inclusif" in data:
            politique = (data.get("politique_inclusif") or "neutre").strip()
            if politique not in POLITIQUES_INCLUSIF:
                raise ValueError(
                    f"Politique inclusif invalide : {politique!r}. "
                    f"Valeurs admises : {sorted(POLITIQUES_INCLUSIF)}."
                )
            current["politique_inclusif"] = politique
        if "competences_socles" in data:
            socles_in = data.get("competences_socles") or []
            if not isinstance(socles_in, list):
                raise ValueError("competences_socles doit être une liste de chaînes.")
            current["competences_socles"] = [
                str(s).strip() for s in socles_in if str(s).strip()
            ]

        # On préserve toujours id et fichiers d'assets.
        current["id"] = entity.id
        current.setdefault("logo_fichier", entity.logo_fichier)
        current.setdefault("signature_fichier", entity.signature_fichier)

        cfg_file.write_text(
            json.dumps(current, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        self._log.info(f"Entité mise à jour : {entity_id}")
        self.rescan()
        return self._entities[entity_id]

    def remove_asset(self, entity_id: str, kind: str) -> Entity:
        """Supprime le logo ou la signature (fichier physique).

        Garde-fou : la config.json reste pointée sur `logo.png` / `signature.png`
        par défaut, donc à la prochaine sauvegarde d'asset, le nom par défaut
        est restauré.
        """
        if kind not in {"logo", "signature"}:
            raise ValueError(f"Type d'asset inconnu : {kind!r}")
        entity = self._entities.get(entity_id)
        if entity is None:
            raise ValueError(f"Entité inconnue : {entity_id!r}")
        path = entity.logo_path if kind == "logo" else entity.signature_path
        if path.exists():
            path.unlink()
            self._log.info(f"{kind} supprimé pour entité {entity_id}")
        self.rescan()
        return self._entities[entity_id]
