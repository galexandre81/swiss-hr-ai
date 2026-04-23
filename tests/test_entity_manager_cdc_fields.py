"""Tests des 4 champs étendus Entity pour le module Cahier des charges.

Rétrocompatibilité : une config.json existante, sans les 4 nouveaux
champs, doit continuer de fonctionner — les entités obtiennent des
valeurs par défaut sensées.
"""

from __future__ import annotations

import json

import pytest

from _app.core.entity_manager import EntityManager


def test_create_entity_with_defaults(sandbox):
    """Une entité créée sans préciser les nouveaux champs obtient
    les valeurs par défaut et les persiste dans config.json."""
    mgr = EntityManager()
    ent = mgr.create({"nom": "Acme SA"})

    assert ent.langue_principale == "fr"
    assert ent.politique_inclusif == "neutre"
    assert ent.cct_applicable == ""
    assert ent.competences_socles == []

    cfg = json.loads((ent.dossier / "config.json").read_text(encoding="utf-8"))
    assert cfg["langue_principale"] == "fr"
    assert cfg["politique_inclusif"] == "neutre"
    assert cfg["cct_applicable"] == ""
    assert cfg["competences_socles"] == []


def test_create_entity_with_all_cdc_fields(sandbox):
    mgr = EntityManager()
    ent = mgr.create({
        "nom": "Horlogerie du Léman SA",
        "langue_principale": "fr",
        "politique_inclusif": "doublets",
        "cct_applicable": "horlogerie",
        "competences_socles": [
            "Sens des responsabilités",
            "  Esprit d'équipe  ",  # trimé
            "",                      # filtré
        ],
    })
    assert ent.langue_principale == "fr"
    assert ent.politique_inclusif == "doublets"
    assert ent.cct_applicable == "horlogerie"
    assert ent.competences_socles == [
        "Sens des responsabilités",
        "Esprit d'équipe",
    ]


def test_legacy_config_rescan_fills_defaults(sandbox):
    """Un config.json antérieur (sans les nouveaux champs) doit être
    lu sans erreur, avec application des valeurs par défaut."""
    target = sandbox / "Entities" / "legacy_entity"
    target.mkdir()
    (target / "config.json").write_text(
        json.dumps({
            "id": "legacy_entity",
            "nom": "Cabinet Legacy",
            "forme_juridique": "SA",
        }),
        encoding="utf-8",
    )
    mgr = EntityManager()
    ent = mgr.all()[0]
    assert ent.id == "legacy_entity"
    assert ent.langue_principale == "fr"
    assert ent.politique_inclusif == "neutre"
    assert ent.cct_applicable == ""
    assert ent.competences_socles == []


def test_invalid_politique_falls_back_with_warning(sandbox):
    target = sandbox / "Entities" / "weird"
    target.mkdir()
    (target / "config.json").write_text(
        json.dumps({
            "id": "weird",
            "nom": "Weird",
            "politique_inclusif": "nimporte_quoi",
            "langue_principale": "klingon",
        }),
        encoding="utf-8",
    )
    mgr = EntityManager()
    ent = mgr.all()[0]
    assert ent.politique_inclusif == "neutre"
    assert ent.langue_principale == "fr"


def test_update_entity_new_fields(sandbox):
    mgr = EntityManager()
    ent = mgr.create({"nom": "Acme"})
    mgr.update(ent.id, {
        "politique_inclusif": "point_median",
        "cct_applicable": "commerce_detail",
        "competences_socles": ["Confidentialité", "Rigueur"],
    })
    ent2 = next(e for e in mgr.all() if e.id == ent.id)
    assert ent2.politique_inclusif == "point_median"
    assert ent2.cct_applicable == "commerce_detail"
    assert ent2.competences_socles == ["Confidentialité", "Rigueur"]


def test_update_rejects_invalid_politique(sandbox):
    mgr = EntityManager()
    ent = mgr.create({"nom": "Acme"})
    with pytest.raises(ValueError):
        mgr.update(ent.id, {"politique_inclusif": "n_importe"})


def test_as_dict_includes_new_fields(sandbox):
    mgr = EntityManager()
    ent = mgr.create({
        "nom": "Acme",
        "langue_principale": "de",
        "politique_inclusif": "doublets",
        "competences_socles": ["Éthique"],
    })
    d = ent.as_dict()
    assert d["langue_principale"] == "de"
    assert d["politique_inclusif"] == "doublets"
    assert d["competences_socles"] == ["Éthique"]
    assert "cct_applicable" in d
