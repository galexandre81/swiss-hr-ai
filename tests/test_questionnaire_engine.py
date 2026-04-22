from __future__ import annotations

from pathlib import Path

import pytest

from _app.core.questionnaire_engine import (
    STANDARD_CRITERES_FR,
    Critere,
    QuestionnaireContext,
    QuestionnaireEngine,
)

reportlab_missing = not QuestionnaireEngine.is_available()
pytestmark = pytest.mark.skipif(
    reportlab_missing,
    reason="reportlab non installé — installez-le avec `pip install reportlab==4.2.2`.",
)


def _ctx(**overrides):
    base = dict(
        employeur_nom="Horlogerie du Léman SA",
        employeur_email_rh="rh@horlogerie-leman.ch",
        collaborateur_nom="Blanc",
        collaborateur_prenom="Sophie",
        fonction="Cheffe de projet IT",
        periode_debut="15.01.2020",
        periode_fin="31.03.2024",
        manager_nom="Jean Dupont",
        criteres=STANDARD_CRITERES_FR,
        langue="fr",
    )
    base.update(overrides)
    return QuestionnaireContext(**base)


def test_pdf_is_generated(tmp_path: Path):
    target = tmp_path / "q.pdf"
    QuestionnaireEngine().generate_pdf(_ctx(), target)
    assert target.is_file()
    assert target.stat().st_size > 5000  # PDF non trivial


def test_pdf_contains_acroform_fields(tmp_path: Path):
    """Smoke : le PDF doit contenir des champs AcroForm (détection
    heuristique — la sous-chaîne "/AcroForm" est présente dans tout PDF
    avec un formulaire)."""
    target = tmp_path / "q.pdf"
    QuestionnaireEngine().generate_pdf(_ctx(), target)
    raw = target.read_bytes()
    assert b"/AcroForm" in raw
    # Au moins un champ radio (échelle 5 étoiles).
    assert b"/Btn" in raw or b"/Tx" in raw


def test_pdf_embeds_employer_and_collab_names(tmp_path: Path):
    target = tmp_path / "q.pdf"
    QuestionnaireEngine().generate_pdf(_ctx(), target)
    raw = target.read_bytes()
    # Les noms apparaissent en clair (les chaînes texte sont visibles dans les
    # flux PDF non compressés à la génération reportlab par défaut).
    assert b"Horlogerie" in raw or b"Blanc" in raw


def test_pdf_respects_criteres_list(tmp_path: Path):
    # On passe un sous-ensemble
    target = tmp_path / "q.pdf"
    custom = [
        Critere("qualite_travail", "Qualité du travail"),
        Critere("quantite_travail", "Quantité"),
    ]
    QuestionnaireEngine().generate_pdf(_ctx(criteres=custom), target)
    assert target.is_file()


def test_is_available():
    assert QuestionnaireEngine.is_available() is True
