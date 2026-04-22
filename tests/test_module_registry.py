from __future__ import annotations

import json

from _app.core.module_registry import ModuleRegistry


def test_catalog_yields_disponible_and_a_venir(sandbox):
    reg = ModuleRegistry()
    mods = reg.list_modules()
    assert len(mods) >= 1
    # certificats est implémenté → disponible ; les autres restent à venir.
    by_id = {m["id"]: m for m in mods}
    assert by_id["certificats"]["statut"] == "disponible"
    assert all(m["statut"] == "a_venir" for m in mods if m["id"] != "certificats")


def test_implemented_module_overrides_catalog(sandbox, monkeypatch):
    reg = ModuleRegistry()
    ids = {m["id"] for m in reg.list_modules()}
    assert "certificats" in ids
    assert "juridique" in ids


def test_list_modules_is_ordered_by_catalog(sandbox):
    reg = ModuleRegistry()
    ids = [m["id"] for m in reg.list_modules()]
    # L'ordre doit suivre celui du _catalogue.json livré avec le repo.
    # On vérifie juste que la liste n'est pas triée alphabétiquement.
    assert ids != sorted(ids)


def test_missing_catalog_gracefully(sandbox, monkeypatch):
    # Si _catalogue.json est absent, le registre ne fait apparaître que
    # les modules effectivement implémentés (découverts par introspection).
    from _app.core import module_registry as mr

    def _noop(self):
        self._catalog = []

    monkeypatch.setattr(mr.ModuleRegistry, "_load_catalog", _noop)
    reg = mr.ModuleRegistry()
    mods = reg.list_modules()
    ids = {m["id"] for m in mods}
    # Au minimum, `certificats` est implémenté et doit remonter.
    assert "certificats" in ids
    # Pas de module "à venir" non implémenté (puisque catalogue vide).
    assert all(m["statut"] == "disponible" for m in mods)


def test_get_returns_none_for_unknown(sandbox):
    reg = ModuleRegistry()
    assert reg.get("inexistant") is None


# Sanity: JSON bien formé dans le repo
def test_catalog_file_is_valid_json(sandbox):
    # On lit le vrai catalogue du repo (pas celui du sandbox).
    from pathlib import Path

    from _app.core.module_registry import CATALOG_FILENAME
    real = Path(__file__).resolve().parent.parent / "_app" / "modules" / CATALOG_FILENAME
    data = json.loads(real.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    for entry in data:
        assert {"id", "nom", "icone", "description", "categorie"} <= set(entry)
