from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from _app.core.blacklist_detector import BlacklistDetector
from _app.core.dossier_store import DossierStore
from _app.core.formulation_library import FormulationLibrary
from _app.core.module_base import ModuleContext


# --- Fixtures dédiées --------------------------------------------------

def _copy_real_library(sandbox):
    """Copie le seed livré dans le repo vers le sandbox.

    Le module certificats dépend de formulations validées — on reproduit
    la bibliothèque FR réelle pour exercer le flow de bout en bout.
    """
    real = Path(__file__).resolve().parent.parent / "Bibliotheques" / "fr"
    dst = sandbox / "Bibliotheques" / "fr"
    dst.mkdir(parents=True, exist_ok=True)
    for name in ("formulations_validees.json", "blacklist.json"):
        src = real / name
        if src.exists():
            shutil.copy(src, dst / name)


def _complete_answers() -> dict[str, dict]:
    return {
        "identite": {
            "type_document": "certificat_final",
            "langue": "fr",
            "civilite": "Madame",
            "genre": "f",
            "prenom": "Sophie",
            "nom": "Blanc",
            "date_naissance": "12.05.1990",
            "lieu_origine": "Genève GE",
        },
        "parcours": {
            "date_debut": "15.01.2020",
            "date_fin": "31.03.2024",
            "fonction": "Cheffe de projet IT",
            "taux_activite": "100%",
            "departement": "Organisation & Systèmes",
            "activites": "Pilotage du projet ERP\nGestion d'une équipe de 4 personnes",
            "realisations": "Migration ERP livrée sous budget\nAutomatisation du reporting mensuel",
        },
        "decisions": {
            "motif_fin": "demission",
            "afficher_motif": False,
        },
        "evaluation": {
            "subs_applicable": True,
            "clients_applicable": False,
            "crit_qualite_travail_niveau": "5",
            "crit_quantite_travail_niveau": "4",
            "crit_competences_techniques_niveau": "5",
            "crit_fiabilite_autonomie_niveau": "5",
            "crit_comportement_hierarchie_niveau": "5",
            "crit_comportement_collegues_niveau": "5",
            "crit_comportement_subordonnes_niveau": "5",
            "appreciation_globale_niveau": "5",
        },
        "conclusion": {
            "remerciements": True,
            "regrets": True,
            "voeux": True,
        },
    }


# --- Import du module ---------------------------------------------------

def _load_module():
    from _app.modules.certificats.module import Module
    return Module()


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------

def test_module_declares_steps(sandbox):
    mod = _load_module()
    steps = mod.steps()
    ids = [s.id for s in steps]
    assert ids == ["identite", "parcours", "decisions", "evaluation", "conclusion"]


def test_validate_identite_requires_langue_and_names(sandbox):
    mod = _load_module()
    errors = mod.validate_step("identite", {})
    assert any("Type" in e or "type_document" in e or "obligatoire" in e for e in errors)


def test_validate_parcours_rejects_bad_dates(sandbox):
    mod = _load_module()
    errors = mod.validate_step("parcours", {
        "date_debut": "pas une date", "fonction": "Dev",
    })
    assert any("JJ.MM.AAAA" in e for e in errors)


def test_validate_parcours_accepts_swiss_and_iso(sandbox):
    mod = _load_module()
    # Format suisse natif
    assert mod.validate_step("parcours", {
        "date_debut": "15.01.2020", "date_fin": "31.03.2024", "fonction": "Dev",
    }) == []
    # Tolérance ISO (données legacy)
    assert mod.validate_step("parcours", {
        "date_debut": "2020-01-15", "fonction": "Dev",
    }) == []


def test_end_to_end_draft_is_coherent(sandbox):
    _copy_real_library(sandbox)
    mod = _load_module()
    store = DossierStore()
    dossier = store.create(nom="Blanc", prenom="Sophie", langue="fr",
                           type_document="certificat_final")

    state = mod.ensure_state({})
    for step_id, ans in _complete_answers().items():
        errs = mod.validate_step(step_id, ans)
        assert errs == [], f"Erreurs sur {step_id}: {errs}"
        state = mod.record_answers(state, step_id, ans)

    ok, missing = mod.can_finalize(state)
    assert ok, f"Manquants : {missing}"

    ctx = ModuleContext(
        llm=None,
        entity=None,
        logger=None,
        formulations=FormulationLibrary(),
        blacklist=BlacklistDetector(),
    )
    preview = mod.preview(state, ctx)
    assert "Sophie" in preview["texte"]
    assert "Blanc" in preview["texte"]
    assert "Cheffe de projet IT" in preview["texte"]
    # Niveau 5 partout → formule "excellent" de la bibliothèque
    assert "excellentes" in preview["texte"] or "pleine et entière satisfaction" in preview["texte"]
    # Accords féminins : « Elle » et non plus le marqueur « Elle/Il »
    assert "Elle/Il" not in preview["texte"]
    assert "·e" not in preview["texte"]
    assert "née le" in preview["texte"]


def test_finalize_seals_and_blocks_on_incomplete(sandbox):
    _copy_real_library(sandbox)
    mod = _load_module()
    store = DossierStore()
    dossier = store.create(nom="Testeur", prenom="Pierre", langue="fr",
                           type_document="certificat_final")

    # État incomplet volontairement
    state = mod.ensure_state({})
    state = mod.record_answers(state, "identite", _complete_answers()["identite"])
    ok, missing = mod.can_finalize(state)
    assert not ok
    assert missing  # au moins une étape manquante signalée


def test_gender_agreement_f_m_inclusif(sandbox):
    _copy_real_library(sandbox)
    from _app.modules.certificats.generator import apply_genre

    sample = "Elle/Il a pris en charge des dossiers ; elle/il est reconnu·e."
    assert apply_genre(sample, "f") == "Elle a pris en charge des dossiers ; elle est reconnue."
    assert apply_genre(sample, "m") == "Il a pris en charge des dossiers ; il est reconnu."
    out_inc = apply_genre(sample, "inclusif")
    assert "Elle·Il" in out_inc and "elle·il" in out_inc and "·e" in out_inc


def test_preview_uses_genre_masculin(sandbox):
    _copy_real_library(sandbox)
    mod = _load_module()
    from _app.core.blacklist_detector import BlacklistDetector
    from _app.core.formulation_library import FormulationLibrary

    state = mod.ensure_state({})
    answers = _complete_answers()
    answers["identite"]["civilite"] = "Monsieur"
    answers["identite"]["genre"] = "m"
    answers["identite"]["prenom"] = "Marc"
    for step_id, ans in answers.items():
        state = mod.record_answers(state, step_id, ans)

    ctx = ModuleContext(
        llm=None, entity=None, logger=None,
        formulations=FormulationLibrary(), blacklist=BlacklistDetector(),
    )
    preview = mod.preview(state, ctx)
    assert "Elle/Il" not in preview["texte"]
    assert "né le" in preview["texte"] and "née le" not in preview["texte"]
    # Attention à ne pas matcher « il » dans « fil », « til » etc.
    assert " Il " in preview["texte"] or preview["texte"].startswith("Il ") or "\nIl " in preview["texte"]


def test_finalize_complete_writes_draft_and_audit(sandbox):
    _copy_real_library(sandbox)
    mod = _load_module()
    store = DossierStore()
    dossier = store.create(nom="Testeur", prenom="Complet", langue="fr",
                           type_document="certificat_final")

    state = mod.ensure_state({})
    for step_id, ans in _complete_answers().items():
        state = mod.record_answers(state, step_id, ans)
    dossier.wizard_state = state
    dossier.save()

    # Récupère le Dossier tel que vu par les services (from_disk)
    dossier = store.get(dossier.id)

    # Re-hydrate un Logger factice
    from _app.core.logger import get_logger
    ctx = ModuleContext(
        llm=None,
        entity=None,
        logger=get_logger(),
        formulations=FormulationLibrary(),
        blacklist=BlacklistDetector(),
        extras={"dossier": dossier},
    )
    result = mod.finalize(dossier.wizard_state, ctx)
    assert result["scelle"] is True
    assert result["sha256"]
    # Fichier .txt créé
    brouillons = list((dossier.racine / "05_brouillons").glob("certificat_*.txt"))
    assert brouillons
    # Trace d'audit écrite
    traces = list((dossier.racine / "07_audit").glob("trace_*.jsonl"))
    assert traces
    content = traces[0].read_text(encoding="utf-8")
    assert "seal" in content
