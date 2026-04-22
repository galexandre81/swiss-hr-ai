"""Registre des modules.

Deux sources sont combinées :
    1. Les modules effectivement implémentés dans _app/modules/<id>/module.py
       (découverte dynamique par introspection du package).
    2. Le catalogue prévu dans _app/modules/_catalogue.json, qui liste les
       10 modules du cahier des charges avec leurs métadonnées et un statut
       "à venir" tant qu'aucune implémentation n'existe encore.

Le frontend reçoit la liste fusionnée : les tuiles "à venir" restent
visibles pour que l'utilisateur voie la roadmap, mais elles sont
désactivées tant que le module n'est pas codé.
"""

from __future__ import annotations

import importlib
import json
import pkgutil
from pathlib import Path
from typing import Any

from _app.core.logger import get_logger
from _app.core.module_base import ModuleBase

MODULES_PACKAGE = "_app.modules"
CATALOG_FILENAME = "_catalogue.json"


class ModuleRegistry:
    def __init__(self):
        self._log = get_logger()
        self._implemented: dict[str, ModuleBase] = {}
        self._catalog: list[dict[str, Any]] = []
        self._load_catalog()
        self._discover()

    # --- Chargement ------------------------------------------------------

    def _load_catalog(self) -> None:
        pkg_path = Path(__file__).resolve().parent.parent / "modules"
        cat_file = pkg_path / CATALOG_FILENAME
        if not cat_file.exists():
            self._log.warning(f"Catalogue manquant : {cat_file}")
            return
        try:
            self._catalog = json.loads(cat_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            self._log.error(f"Catalogue mal formé : {exc}")
            self._catalog = []

    def _discover(self) -> None:
        """Parcourt _app/modules/ et instancie toute classe `Module` trouvée."""
        try:
            pkg = importlib.import_module(MODULES_PACKAGE)
        except ModuleNotFoundError:
            self._log.warning(f"Package {MODULES_PACKAGE} introuvable")
            return

        for info in pkgutil.iter_modules(pkg.__path__):
            if info.name.startswith("_"):
                continue  # on ignore _catalogue et fichiers "privés"
            fqname = f"{MODULES_PACKAGE}.{info.name}.module"
            try:
                mod = importlib.import_module(fqname)
            except Exception as exc:
                self._log.warning(f"Module {info.name} non chargé : {exc}")
                continue
            cls = getattr(mod, "Module", None)
            if cls is None or not issubclass(cls, ModuleBase):
                continue
            try:
                instance: ModuleBase = cls()
            except Exception as exc:
                self._log.error(f"Instanciation module {info.name} échouée : {exc}")
                continue
            self._implemented[instance.id] = instance
            self._log.info(f"Module chargé : {instance.id}")

    # --- API publique ----------------------------------------------------

    def list_modules(self) -> list[dict[str, Any]]:
        """Retourne la liste fusionnée, implémenté > catalogue."""
        out: list[dict[str, Any]] = []
        seen: set[str] = set()
        # 1. modules implémentés
        for impl in self._implemented.values():
            out.append({**impl.meta(), "statut": "disponible"})
            seen.add(impl.id)
        # 2. modules seulement prévus (statut "a_venir")
        for entry in self._catalog:
            if entry["id"] in seen:
                continue
            out.append({**entry, "statut": "a_venir"})
        # Tri par ordre catalogue pour que le dashboard soit stable
        order = {e["id"]: i for i, e in enumerate(self._catalog)}
        out.sort(key=lambda m: order.get(m["id"], 999))
        return out

    def get(self, module_id: str) -> ModuleBase | None:
        return self._implemented.get(module_id)
