"""Persistance des cahiers des charges — fichier JSON par entité.

Arborescence (cf. 12_DIVERGENCES_CAHIER_DES_CHARGES.md §3) :

    Entities/
      [ENTITE]/
        Catalogue_CdC/
          _index.json                 ← métadonnées agrégées, reconstructible
          _corbeille/                 ← soft-delete, TTL 30j via suppression_le
            [poste_id]_YYYYMMDDTHHMMSS/
              ...                     ← copie complète du dossier de poste
          [poste_id]/
            v1.0.json                 ← contenu du cahier des charges
            v1.1.json
            v2.0.json
            exports/
              v1.1_cahier_des_charges.docx
              v1.1_annonce_orp.docx

Principe clé (cf. divergence 3) : pas de base de données. Tout est
fichier JSON lisible. L'index est **reconstructible à tout moment**
depuis les fichiers de poste — il n'est qu'un cache pour la
performance de listage.

Isolation multi-entité : chaque instance de `CatalogueStore` est
construite pour **une seule entité**. Impossible de croiser deux
entités par accident — pas de filtrage à faire dans les requêtes,
l'isolation est physique (par dossier).
"""

from __future__ import annotations

import json
import re
import shutil
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from _app.core.logger import get_logger
from _app.core.paths import safe_within

# Nom du sous-dossier catalogue dans chaque entité.
CATALOGUE_SUBDIR = "Catalogue_CdC"
INDEX_FILENAME = "_index.json"
TRASH_SUBDIR = "_corbeille"
EXPORTS_SUBDIR = "exports"

# Durée de rétention dans la corbeille avant purge définitive.
TRASH_RETENTION_DAYS = 30

# Version du schéma de l'index (incrémenter si breaking change).
INDEX_SCHEMA_VERSION = "1.0"

# Regex pour parser les noms de version v1.0, v2.3, etc.
_VERSION_RE = re.compile(r"^v(\d+)\.(\d+)$")


# --- Données utilitaires ----------------------------------------------


@dataclass
class VersionInfo:
    """Parsing de 'v1.2' → VersionInfo(majeure=1, mineure=2)."""

    majeure: int
    mineure: int

    def __str__(self) -> str:
        return f"v{self.majeure}.{self.mineure}"

    @classmethod
    def parse(cls, s: str) -> VersionInfo:
        m = _VERSION_RE.match(s.strip())
        if not m:
            raise ValueError(
                f"Format de version invalide : {s!r}. Attendu : 'v<n>.<m>'."
            )
        return cls(int(m.group(1)), int(m.group(2)))

    def bump_minor(self) -> VersionInfo:
        return VersionInfo(self.majeure, self.mineure + 1)

    def bump_major(self) -> VersionInfo:
        return VersionInfo(self.majeure + 1, 0)

    def as_tuple(self) -> tuple[int, int]:
        return (self.majeure, self.mineure)


@dataclass
class PosteEntry:
    """Une entrée dans `_index.json` — métadonnées agrégées d'un poste.

    Toutes les infos ici sont dérivables des fichiers du dossier poste ;
    l'entrée n'est qu'un cache pour listage rapide.
    """

    poste_id: str
    intitule_poste: str = ""
    famille_metier: str = ""
    statut: str = "brouillon"              # "brouillon" | "valide" | "archive"
    version_active: str = "v1.0"
    versions: list[str] = field(default_factory=list)
    cree_le: str = ""
    cree_par: str = ""
    modifie_le: str = ""
    modifie_par: str = ""


# --- Erreurs métier ----------------------------------------------------


class CatalogueError(Exception):
    """Erreur générique du store de catalogue."""


class PosteIntrouvable(CatalogueError):
    """Poste inexistant dans le catalogue (ni actif, ni en corbeille)."""


class VersionIntrouvable(CatalogueError):
    """Version demandée absente pour ce poste."""


# --- Store principal ---------------------------------------------------


class CatalogueStore:
    """CRUD + versioning + corbeille 30 jours pour une entité donnée.

    Le store est **scopé à une entité** : toutes les opérations
    touchent `<entity_dossier>/Catalogue_CdC/`. Impossible d'accéder
    aux postes d'une autre entité depuis cette instance.

    Les appels sont synchrones et thread-unsafe — le module est
    mono-utilisateur (RH sur son poste), on ne multi-threade pas.
    """

    def __init__(self, entity_dossier: Path):
        if not entity_dossier.exists() or not entity_dossier.is_dir():
            raise CatalogueError(
                f"Dossier d'entité introuvable : {entity_dossier}"
            )
        self._entity_dossier = entity_dossier
        self._catalogue_dir = entity_dossier / CATALOGUE_SUBDIR
        self._trash_dir = self._catalogue_dir / TRASH_SUBDIR
        self._index_file = self._catalogue_dir / INDEX_FILENAME
        self._log = get_logger()
        # Création paresseuse à la première opération d'écriture.
        self._catalogue_dir.mkdir(parents=True, exist_ok=True)
        self._trash_dir.mkdir(parents=True, exist_ok=True)
        if safe_within(self._catalogue_dir, entity_dossier) is None:
            raise CatalogueError("Chemin de catalogue invalide.")

    # ==================================================================
    # Index : lecture, écriture, reconstruction
    # ==================================================================

    def _read_index(self) -> dict[str, Any]:
        """Lit `_index.json`. Si absent ou corrompu, reconstruit depuis
        les fichiers de poste.
        """
        if not self._index_file.exists():
            return self._rebuild_index()
        try:
            data = json.loads(self._index_file.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or "postes" not in data:
                raise ValueError("Structure d'index inattendue.")
            return data
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            self._log.warning(
                f"Index catalogue illisible ({exc}) — reconstruction."
            )
            return self._rebuild_index()

    def _write_index(self, data: dict[str, Any]) -> None:
        data["version_schema"] = INDEX_SCHEMA_VERSION
        data["last_written_at"] = _now_iso()
        tmp = self._index_file.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        # Écriture atomique : rename remplace l'ancien en une opération.
        tmp.replace(self._index_file)

    def _rebuild_index(self) -> dict[str, Any]:
        """Reconstruction depuis les fichiers de poste.

        Garantie : si l'index est supprimé ou corrompu, on ne perd rien.
        Le catalogue reste entièrement fonctionnel tant que les
        fichiers v*.json sont là.
        """
        postes: dict[str, dict[str, Any]] = {}
        for sub in sorted(self._catalogue_dir.iterdir()):
            if not sub.is_dir():
                continue
            # Les dossiers techniques (corbeille, etc.) commencent par "_".
            if sub.name.startswith("_"):
                continue
            entry = self._derive_entry(sub)
            if entry is not None:
                postes[entry.poste_id] = asdict(entry)

        data = {
            "version_schema": INDEX_SCHEMA_VERSION,
            "last_rebuilt_at": _now_iso(),
            "postes": postes,
        }
        self._write_index(data)
        self._log.info(
            f"Index catalogue reconstruit ({len(postes)} postes) "
            f"pour {self._entity_dossier.name}"
        )
        return data

    def _derive_entry(self, poste_dir: Path) -> PosteEntry | None:
        """Construit une PosteEntry en lisant les métadonnées du
        dernier fichier de version trouvé dans le dossier.
        """
        versions = self._list_version_files(poste_dir)
        if not versions:
            return None
        # Dernière version = par défaut, active.
        latest_v, latest_file = versions[-1]
        try:
            doc = json.loads(latest_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            self._log.warning(f"Version illisible : {latest_file} ({exc})")
            return None
        ident = doc.get("identification") or {}
        meta = doc.get("_meta") or {}
        return PosteEntry(
            poste_id=poste_dir.name,
            intitule_poste=ident.get("intitule_poste") or "",
            famille_metier=ident.get("departement") or "",  # heuristique V1
            statut=meta.get("statut") or "brouillon",
            version_active=str(latest_v),
            versions=[str(v) for v, _ in versions],
            cree_le=meta.get("cree_le") or "",
            cree_par=meta.get("cree_par") or "",
            modifie_le=meta.get("modifie_le") or meta.get("cree_le") or "",
            modifie_par=meta.get("modifie_par") or meta.get("cree_par") or "",
        )

    def _update_index_entry(self, entry: PosteEntry) -> None:
        data = self._read_index()
        data["postes"][entry.poste_id] = asdict(entry)
        self._write_index(data)

    def _remove_index_entry(self, poste_id: str) -> None:
        data = self._read_index()
        data["postes"].pop(poste_id, None)
        self._write_index(data)

    # ==================================================================
    # API publique — lecture
    # ==================================================================

    def list(
        self,
        *,
        statut: str | None = None,
        famille_metier: str | None = None,
        texte: str | None = None,
    ) -> list[PosteEntry]:
        """Liste les postes de l'entité, filtrés.

        Performance : O(n) sur l'index en mémoire, pas de fichier à
        ouvrir. Pour 200 postes, reste sous 5 ms.
        """
        data = self._read_index()
        entries = [
            PosteEntry(**_ignore_unknown(PosteEntry, raw))
            for raw in data["postes"].values()
        ]
        if statut is not None:
            entries = [e for e in entries if e.statut == statut]
        if famille_metier is not None:
            entries = [e for e in entries if e.famille_metier == famille_metier]
        if texte:
            needle = texte.lower().strip()
            entries = [
                e for e in entries
                if needle in e.intitule_poste.lower()
                or needle in e.famille_metier.lower()
                or needle in e.poste_id.lower()
            ]
        entries.sort(key=lambda e: (e.intitule_poste.lower(), e.poste_id))
        return entries

    def get(self, poste_id: str, version: str | None = None) -> dict[str, Any]:
        """Lit le document d'un poste, à une version donnée ou active.

        Lève `PosteIntrouvable` si le poste n'existe pas, `VersionIntrouvable`
        si la version demandée n'existe pas.
        """
        poste_dir = self._poste_dir(poste_id, must_exist=True)
        if version is None:
            data = self._read_index()
            raw = data["postes"].get(poste_id)
            if raw is None:
                # Fallback : version la plus récente sur disque
                versions = self._list_version_files(poste_dir)
                if not versions:
                    raise PosteIntrouvable(f"Poste vide : {poste_id}")
                version = str(versions[-1][0])
            else:
                version = raw.get("version_active") or "v1.0"
        version_file = poste_dir / f"{version}.json"
        if not version_file.exists():
            raise VersionIntrouvable(
                f"Version {version!r} absente pour poste {poste_id!r}."
            )
        return json.loads(version_file.read_text(encoding="utf-8"))

    def list_versions(self, poste_id: str) -> list[str]:
        poste_dir = self._poste_dir(poste_id, must_exist=True)
        return [str(v) for v, _ in self._list_version_files(poste_dir)]

    # ==================================================================
    # API publique — écriture
    # ==================================================================

    def create(
        self,
        document: dict[str, Any],
        *,
        cree_par: str,
        poste_id: str | None = None,
    ) -> tuple[str, str]:
        """Crée un nouveau poste en v1.0. Retourne `(poste_id, version)`.

        Le `poste_id` est généré (UUID court) sauf si fourni
        explicitement (utile pour les tests ou l'import).
        """
        poste_id = poste_id or _gen_poste_id()
        poste_dir = self._catalogue_dir / poste_id
        if poste_dir.exists():
            raise CatalogueError(f"poste_id déjà utilisé : {poste_id}")
        if safe_within(poste_dir, self._catalogue_dir) is None:
            raise CatalogueError("Chemin de poste invalide.")
        poste_dir.mkdir(parents=True)

        version = "v1.0"
        now = _now_iso()

        # Injection des métadonnées avant écriture.
        doc = dict(document)
        meta = dict(doc.get("_meta") or {})
        meta.setdefault("version_schema", "1.0")
        meta["cree_le"] = now
        meta["cree_par"] = cree_par
        meta["modifie_le"] = now
        meta["modifie_par"] = cree_par
        meta["entite_id"] = self._entity_dossier.name
        meta.setdefault("statut", "brouillon")
        doc["_meta"] = meta

        self._write_version_file(poste_dir, version, doc)

        # Mise à jour de l'index.
        ident = doc.get("identification") or {}
        entry = PosteEntry(
            poste_id=poste_id,
            intitule_poste=ident.get("intitule_poste") or "",
            famille_metier=ident.get("departement") or "",
            statut=meta["statut"],
            version_active=version,
            versions=[version],
            cree_le=now,
            cree_par=cree_par,
            modifie_le=now,
            modifie_par=cree_par,
        )
        self._update_index_entry(entry)
        self._log.info(f"CdC créé : {poste_id} ({version})")
        return poste_id, version

    def save(
        self,
        poste_id: str,
        document: dict[str, Any],
        *,
        modifie_par: str,
        new_version: str | None = None,
        commentaire_version: str = "",
    ) -> str:
        """Sauvegarde le document.

        - `new_version=None` (défaut) : écrase la version active (auto-save).
        - `new_version="minor"` : incrémente la mineure (v1.0 → v1.1).
        - `new_version="major"` : incrémente la majeure (v1.2 → v2.0).

        Retourne la version effectivement sauvegardée.
        """
        poste_dir = self._poste_dir(poste_id, must_exist=True)
        data = self._read_index()
        raw = data["postes"].get(poste_id)
        if raw is None:
            raise PosteIntrouvable(f"Poste absent de l'index : {poste_id}")

        version_active = raw.get("version_active") or "v1.0"
        versions: list[str] = raw.get("versions") or [version_active]

        if new_version is None:
            target_version = version_active
        elif new_version == "minor":
            target_version = str(VersionInfo.parse(version_active).bump_minor())
        elif new_version == "major":
            target_version = str(VersionInfo.parse(version_active).bump_major())
        else:
            raise ValueError(
                f"new_version invalide : {new_version!r}. "
                f"Attendu : None, 'minor' ou 'major'."
            )

        now = _now_iso()
        doc = dict(document)
        meta = dict(doc.get("_meta") or {})
        meta.setdefault("version_schema", "1.0")
        meta["modifie_le"] = now
        meta["modifie_par"] = modifie_par
        if commentaire_version:
            meta["commentaire_version"] = commentaire_version
        doc["_meta"] = meta

        self._write_version_file(poste_dir, target_version, doc)

        if target_version not in versions:
            versions.append(target_version)
            versions.sort(key=lambda v: VersionInfo.parse(v).as_tuple())

        ident = doc.get("identification") or {}
        entry = PosteEntry(
            poste_id=poste_id,
            intitule_poste=ident.get("intitule_poste") or raw.get("intitule_poste") or "",
            famille_metier=ident.get("departement") or raw.get("famille_metier") or "",
            statut=meta.get("statut") or raw.get("statut") or "brouillon",
            version_active=target_version,
            versions=versions,
            cree_le=raw.get("cree_le") or now,
            cree_par=raw.get("cree_par") or modifie_par,
            modifie_le=now,
            modifie_par=modifie_par,
        )
        self._update_index_entry(entry)
        self._log.info(
            f"CdC sauvegardé : {poste_id} → {target_version} "
            f"({'new version' if new_version else 'auto-save'})"
        )
        return target_version

    def set_active_version(self, poste_id: str, version: str) -> None:
        """Bascule la version active (usage : revenir à une version
        antérieure)."""
        poste_dir = self._poste_dir(poste_id, must_exist=True)
        if not (poste_dir / f"{version}.json").exists():
            raise VersionIntrouvable(
                f"Version {version!r} absente pour {poste_id!r}."
            )
        data = self._read_index()
        raw = data["postes"].get(poste_id)
        if raw is None:
            raise PosteIntrouvable(f"Poste absent de l'index : {poste_id}")
        raw["version_active"] = version
        data["postes"][poste_id] = raw
        self._write_index(data)
        self._log.info(f"Version active de {poste_id} basculée sur {version}")

    def duplicate(
        self,
        source_poste_id: str,
        *,
        cree_par: str,
        nouveau_intitule: str | None = None,
    ) -> str:
        """Copie un poste en nouveau poste. Reset à v1.0.

        Utile pour créer une variante ("Commercial régional Vaud" →
        "Commercial régional Genève").
        """
        doc = self.get(source_poste_id)  # version active
        # Reset des métadonnées
        doc["_meta"] = {}
        if nouveau_intitule:
            ident = dict(doc.get("identification") or {})
            ident["intitule_poste"] = nouveau_intitule
            doc["identification"] = ident
        new_id, _ = self.create(doc, cree_par=cree_par)
        self._log.info(f"CdC dupliqué : {source_poste_id} → {new_id}")
        return new_id

    def set_statut(self, poste_id: str, statut: str) -> None:
        """Change le statut (brouillon/valide/archive) de la version active."""
        if statut not in {"brouillon", "valide", "archive"}:
            raise ValueError(f"Statut invalide : {statut!r}")
        data = self._read_index()
        raw = data["postes"].get(poste_id)
        if raw is None:
            raise PosteIntrouvable(f"Poste absent de l'index : {poste_id}")
        version_active = raw.get("version_active") or "v1.0"
        poste_dir = self._poste_dir(poste_id, must_exist=True)
        doc = self.get(poste_id, version=version_active)
        meta = dict(doc.get("_meta") or {})
        meta["statut"] = statut
        doc["_meta"] = meta
        self._write_version_file(poste_dir, version_active, doc)
        raw["statut"] = statut
        data["postes"][poste_id] = raw
        self._write_index(data)
        self._log.info(f"Statut de {poste_id} → {statut}")

    # ==================================================================
    # Corbeille (soft-delete avec TTL 30 jours)
    # ==================================================================

    def delete_soft(self, poste_id: str, *, supprime_par: str) -> str:
        """Déplace le poste vers la corbeille. Retourne l'id en corbeille."""
        poste_dir = self._poste_dir(poste_id, must_exist=True)
        stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        trash_id = f"{poste_id}_{stamp}"
        trash_dest = self._trash_dir / trash_id
        if safe_within(trash_dest, self._trash_dir) is None:
            raise CatalogueError("Chemin corbeille invalide.")
        shutil.move(str(poste_dir), str(trash_dest))
        # Marqueur suppression + auteur
        (trash_dest / "_trash_meta.json").write_text(
            json.dumps(
                {
                    "original_poste_id": poste_id,
                    "supprime_le": _now_iso(),
                    "supprime_par": supprime_par,
                    "restaurable_jusquau": _now_plus_days_iso(TRASH_RETENTION_DAYS),
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        self._remove_index_entry(poste_id)
        self._log.info(f"CdC envoyé à la corbeille : {poste_id} → {trash_id}")
        return trash_id

    def list_trash(self) -> list[dict[str, Any]]:
        """Liste les postes en corbeille avec leur date limite de restauration."""
        out: list[dict[str, Any]] = []
        for sub in sorted(self._trash_dir.iterdir()):
            if not sub.is_dir():
                continue
            meta_file = sub / "_trash_meta.json"
            if not meta_file.exists():
                continue
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            out.append({"trash_id": sub.name, **meta})
        return out

    def restore_trash(self, trash_id: str) -> str:
        """Restaure un poste depuis la corbeille. Retourne le poste_id final.

        Si le poste_id original est déjà repris par un autre poste,
        un suffixe est ajouté.
        """
        trash_dir = self._trash_dir / trash_id
        if not trash_dir.exists() or not trash_dir.is_dir():
            raise PosteIntrouvable(f"Entrée corbeille inexistante : {trash_id}")
        meta_file = trash_dir / "_trash_meta.json"
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                original = meta.get("original_poste_id") or trash_id
            except json.JSONDecodeError:
                original = trash_id
        else:
            original = trash_id
        target = self._catalogue_dir / original
        suffix = 2
        while target.exists():
            target = self._catalogue_dir / f"{original}_restauré{suffix}"
            suffix += 1
        if safe_within(target, self._catalogue_dir) is None:
            raise CatalogueError("Chemin de restauration invalide.")
        shutil.move(str(trash_dir), str(target))
        # Nettoyage du marqueur trash
        (target / "_trash_meta.json").unlink(missing_ok=True)
        # Reconstruction de l'entrée d'index
        entry = self._derive_entry(target)
        if entry is not None:
            self._update_index_entry(entry)
        self._log.info(f"CdC restauré depuis corbeille : {trash_id} → {target.name}")
        return target.name

    def delete_hard(self, trash_id: str) -> None:
        """Suppression définitive depuis la corbeille."""
        trash_dir = self._trash_dir / trash_id
        if not trash_dir.exists():
            raise PosteIntrouvable(f"Entrée corbeille inexistante : {trash_id}")
        if safe_within(trash_dir, self._trash_dir) is None:
            raise CatalogueError("Chemin corbeille invalide.")
        shutil.rmtree(trash_dir)
        self._log.info(f"CdC supprimé définitivement : {trash_id}")

    def purge_expired(self) -> int:
        """Purge les entrées de corbeille dont la date de rétention est
        dépassée. Retourne le nombre purgé.
        """
        now = datetime.now()
        purged = 0
        for entry in self.list_trash():
            try:
                limite = datetime.fromisoformat(entry.get("restaurable_jusquau", ""))
            except ValueError:
                continue
            if now > limite:
                try:
                    self.delete_hard(entry["trash_id"])
                    purged += 1
                except CatalogueError as exc:
                    self._log.warning(
                        f"Purge échouée pour {entry['trash_id']} : {exc}"
                    )
        if purged:
            self._log.info(f"Corbeille purgée : {purged} entrée(s) supprimée(s).")
        return purged

    # ==================================================================
    # Helpers internes
    # ==================================================================

    def _poste_dir(self, poste_id: str, *, must_exist: bool) -> Path:
        target = self._catalogue_dir / poste_id
        if safe_within(target, self._catalogue_dir) is None:
            raise CatalogueError(f"Chemin de poste invalide : {poste_id!r}")
        if must_exist and not target.exists():
            raise PosteIntrouvable(f"Poste inconnu : {poste_id!r}")
        return target

    def _list_version_files(
        self, poste_dir: Path
    ) -> list[tuple[VersionInfo, Path]]:
        """Retourne [(VersionInfo, Path)] trié par version croissante."""
        out: list[tuple[VersionInfo, Path]] = []
        for p in poste_dir.glob("v*.json"):
            try:
                v = VersionInfo.parse(p.stem)
            except ValueError:
                continue
            out.append((v, p))
        out.sort(key=lambda t: t[0].as_tuple())
        return out

    def _write_version_file(
        self, poste_dir: Path, version: str, document: dict[str, Any]
    ) -> None:
        version_file = poste_dir / f"{version}.json"
        if safe_within(version_file, poste_dir) is None:
            raise CatalogueError("Chemin de fichier version invalide.")
        tmp = version_file.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(document, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        tmp.replace(version_file)


# --- Helpers module-level ----------------------------------------------


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _now_plus_days_iso(days: int) -> str:
    return (datetime.now() + timedelta(days=days)).isoformat(timespec="seconds")


def _gen_poste_id() -> str:
    """ID court lisible-ish : 8 premiers caractères d'un UUID4 hex."""
    return uuid.uuid4().hex[:8]


def _ignore_unknown(cls: type, raw: dict[str, Any]) -> dict[str, Any]:
    """Filtre un dict pour ne garder que les clés qui correspondent
    à des champs du dataclass `cls`. Tolère les évolutions de schéma.
    """
    if not isinstance(raw, dict):
        return {}
    fields_ = getattr(cls, "__dataclass_fields__", {})
    return {k: v for k, v in raw.items() if k in fields_}
