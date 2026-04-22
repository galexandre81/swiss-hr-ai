from __future__ import annotations

import json

import pytest

from _app.core.formulation_library import FormulationLibrary


def _seed_fr(sandbox):
    (sandbox / "Bibliotheques" / "fr" / "formulations_validees.json").write_text(
        json.dumps({
            "version": "test",
            "langue": "fr",
            "valide_par": "tests",
            "formulations": {
                "appreciation_globale": {
                    "5": ["a fourni des prestations excellentes"],
                    "3": ["a accompli ses tâches à notre satisfaction"],
                },
                "qualite_travail": {
                    "5": ["Qualité exceptionnelle.", "Très haute qualité."],
                },
            },
        }),
        encoding="utf-8",
    )


def test_phrases_returns_list_for_known_level(sandbox):
    _seed_fr(sandbox)
    lib = FormulationLibrary()
    out = lib.phrases("qualite_travail", 5, "fr")
    assert len(out) == 2
    assert "Qualité exceptionnelle." in out


def test_phrases_returns_empty_for_unknown_level(sandbox):
    _seed_fr(sandbox)
    lib = FormulationLibrary()
    assert lib.phrases("qualite_travail", 1, "fr") == []


def test_phrases_rejects_invalid_level(sandbox):
    _seed_fr(sandbox)
    lib = FormulationLibrary()
    with pytest.raises(ValueError):
        lib.phrases("x", 9, "fr")


def test_pick_is_deterministic(sandbox):
    _seed_fr(sandbox)
    lib = FormulationLibrary()
    a = lib.pick("qualite_travail", 5, "fr")
    b = lib.pick("qualite_travail", 5, "fr")
    assert a == b == "Qualité exceptionnelle."
    # Variant selection via prefer_index.
    c = lib.pick("qualite_travail", 5, "fr", prefer_index=1)
    assert c == "Très haute qualité."


def test_absent_library_does_not_crash(sandbox):
    # pas de seed → fichier absent
    lib = FormulationLibrary()
    assert lib.phrases("qualite_travail", 5, "fr") == []
    info = lib.info("fr")
    assert info.version == "absent"


def test_info_exposes_criteria(sandbox):
    _seed_fr(sandbox)
    lib = FormulationLibrary()
    info = lib.info("fr")
    assert "qualite_travail" in info.criteres
    assert "appreciation_globale" in info.criteres
