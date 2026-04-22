from __future__ import annotations

import json

import pytest

from _app.core.entity_manager import EntityManager, slugify


def test_slugify_handles_accents_and_spaces():
    assert slugify("Horlogerie du Léman SA") == "horlogerie_du_leman_sa"
    assert slugify("  --- !!! ") == "entite"
    assert slugify("") == "entite"


def test_scan_empty(sandbox):
    mgr = EntityManager()
    assert mgr.all() == []
    assert mgr.active is None


def test_create_entity_writes_config(sandbox):
    mgr = EntityManager()
    ent = mgr.create({"nom": "Société Démo SA", "forme_juridique": "SA"})
    assert ent.nom == "Société Démo SA"
    cfg_path = sandbox / "Entities" / ent.id / "config.json"
    assert cfg_path.exists()
    data = json.loads(cfg_path.read_text(encoding="utf-8"))
    assert data["forme_juridique"] == "SA"
    assert data["id"] == ent.id


def test_create_entity_rejects_empty_name(sandbox):
    mgr = EntityManager()
    with pytest.raises(ValueError):
        mgr.create({"nom": "   "})


def test_create_entity_disambiguates_slug(sandbox):
    mgr = EntityManager()
    a = mgr.create({"nom": "Acme"})
    b = mgr.create({"nom": "Acme"})
    assert a.id != b.id
    assert b.id.startswith("acme")


def test_set_active_persists_choice(sandbox):
    mgr = EntityManager()
    mgr.create({"nom": "Alpha"})
    beta = mgr.create({"nom": "Beta"})
    mgr.set_active(beta.id)
    assert mgr.active.id == beta.id
