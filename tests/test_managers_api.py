"""Tests de l'API managers_* (CRUD + génération questionnaire)."""

from __future__ import annotations

import pytest

from _app.core.questionnaire_engine import QuestionnaireEngine


@pytest.fixture
def api(sandbox, monkeypatch):
    import webview
    monkeypatch.setattr(webview, "windows", [])
    from _app.ui.api import Api
    return Api()


def _make_dossier(api, nom="Blanc", prenom="Sophie") -> str:
    r = api.wizard_create_dossier("certificats", {"nom": nom, "prenom": prenom})
    return r["dossier"]["id"]


def test_managers_empty_initially(api):
    did = _make_dossier(api)
    assert api.managers_list(did) == {"items": []}


def test_managers_add_and_persist(api):
    did = _make_dossier(api)
    res = api.managers_add(did, {
        "nom": "Jean Dupont",
        "fonction": "Directeur opérations",
        "periode_debut": "01.01.2020",
        "periode_fin": "31.12.2022",
    })
    assert "manager" in res
    mid = res["manager"]["id"]
    # Relecture depuis le disque
    api2_store = api._dossiers
    fresh = api2_store.get(did)
    managers = fresh.modules.get("certificats", {}).get("managers", [])
    assert len(managers) == 1
    assert managers[0]["id"] == mid


def test_managers_reject_empty_name(api):
    did = _make_dossier(api)
    res = api.managers_add(did, {"nom": "   "})
    assert "erreur" in res


def test_managers_generate_id_conflict(api):
    did = _make_dossier(api)
    api.managers_add(did, {"nom": "Jean Dupont"})
    res = api.managers_add(did, {"nom": "Jean Dupont"})
    assert res["manager"]["id"].endswith("_2")


def test_managers_remove(api):
    did = _make_dossier(api)
    m = api.managers_add(did, {"nom": "À retirer"})["manager"]
    assert api.managers_remove(did, m["id"]) == {"supprime": True}
    assert api.managers_list(did) == {"items": []}


def test_managers_remove_unknown(api):
    did = _make_dossier(api)
    res = api.managers_remove(did, "nope")
    assert "erreur" in res


@pytest.mark.skipif(
    not QuestionnaireEngine.is_available(),
    reason="reportlab non installé",
)
def test_generate_questionnaire_writes_pdf(api):
    did = _make_dossier(api)
    m = api.managers_add(did, {
        "nom": "Jean Dupont",
        "periode_debut": "01.01.2020",
        "periode_fin": "31.12.2022",
    })["manager"]

    res = api.managers_generate_questionnaire(did, m["id"])
    assert "fichier" in res
    # Fichier effectivement écrit dans vierges/
    dossier = api._dossiers.get(did)
    vierges = dossier.subfolder("03_questionnaires_managers/vierges")
    pdfs = list(vierges.glob("*.pdf"))
    assert pdfs, "Le PDF questionnaire n'a pas été créé."
    # Métadonnée questionnaire_vierge persistée
    managers = dossier.modules["certificats"]["managers"]
    target = next(x for x in managers if x["id"] == m["id"])
    assert target["questionnaire_vierge"] == res["fichier"]


@pytest.mark.skipif(
    not QuestionnaireEngine.is_available(),
    reason="reportlab non installé",
)
def test_list_detects_response_pdf(api):
    did = _make_dossier(api)
    m = api.managers_add(did, {"nom": "Alice Durand"})["manager"]
    api.managers_generate_questionnaire(did, m["id"])

    # Simule la réception : on copie un PDF dans remplis/ avec l'id du manager dans le nom.
    dossier = api._dossiers.get(did)
    remplis = dossier.subfolder("03_questionnaires_managers/remplis")
    (remplis / f"reponse_{m['id']}.pdf").write_bytes(b"%PDF-1.4\ntest\n%%EOF")

    listing = api.managers_list(did)["items"]
    target = next(x for x in listing if x["id"] == m["id"])
    assert target["reponses_detectees"] == [f"reponse_{m['id']}.pdf"]
