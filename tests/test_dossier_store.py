from __future__ import annotations

import json

import pytest

from _app.core.dossier_store import SUBFOLDERS, Dossier, DossierStore


def test_create_dossier_builds_subtree(sandbox):
    store = DossierStore()
    d = store.create(nom="Müller", prenom="Anne-Laure", langue="fr",
                     type_document="certificat_final")
    assert d.racine.is_dir()
    for sub in SUBFOLDERS:
        assert (d.racine / sub).is_dir()
    meta = json.loads((d.racine / "dossier.json").read_text(encoding="utf-8"))
    assert meta["collaborateur"]["nom"] == "Müller"
    assert meta["langue"] == "fr"


def test_create_rejects_empty_name(sandbox):
    store = DossierStore()
    with pytest.raises(ValueError):
        store.create(nom="", prenom="Jean")


def test_create_conflict_appends_suffix(sandbox):
    store = DossierStore()
    d1 = store.create(nom="Dupont", prenom="Paul")
    d2 = store.create(nom="Dupont", prenom="Paul")
    assert d1.id != d2.id


def test_get_and_list(sandbox):
    store = DossierStore()
    d = store.create(nom="Rossi", prenom="Luca")
    fetched = store.get(d.id)
    assert fetched is not None
    assert fetched.collaborateur.nom == "Rossi"
    listing = store.list()
    assert len(listing) == 1
    assert listing[0]["id"] == d.id


def test_subfolder_rejects_traversal(sandbox):
    store = DossierStore()
    d = store.create(nom="Test", prenom="Case")
    with pytest.raises(ValueError):
        d.subfolder("../../etc")


def test_delete_moves_to_trash(sandbox):
    store = DossierStore()
    d = store.create(nom="Tmp", prenom="Paul")
    assert store.delete(d.id) is True
    assert not (store.racine / d.id).exists()
    trash = store.racine / "_supprimes"
    assert trash.exists() and any(trash.iterdir())


def test_roundtrip_wizard_state(sandbox):
    store = DossierStore()
    d = store.create(nom="Keller", prenom="Max")
    d.wizard_state = {"step": "parcours", "answers": {"identite": {"prenom": "Max"}},
                      "completed": ["identite"], "finalized": False}
    d.save()
    fetched = Dossier.from_disk(d.racine)
    assert fetched.wizard_state["step"] == "parcours"
    assert fetched.wizard_state["completed"] == ["identite"]
