"""Tests pour l'archivage de documents sources (§15.1 de la spec).

On teste en direct les helpers de l'API (chemin programmatique via
`_documents_attach_raw`) pour éviter la dépendance à la file dialog
pywebview dans un environnement sans UI.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def _make_sample_pdf(tmp_path: Path, name: str = "contrat.pdf",
                    content: bytes = b"%PDF-1.4\ndummy\n%%EOF") -> Path:
    p = tmp_path / name
    p.write_bytes(content)
    return p


@pytest.fixture
def api(sandbox, monkeypatch):
    """Construit une Api sans lancer pywebview."""
    import webview

    # Pas de vraie fenêtre — `documents_pick_and_attach` n'est pas testé ici.
    monkeypatch.setattr(webview, "windows", [])

    from _app.ui.api import Api
    return Api()


def test_attach_pdf_and_list(api, sandbox, tmp_path):
    src = _make_sample_pdf(tmp_path)
    d = api.wizard_create_dossier("certificats", {"nom": "Martin", "prenom": "Pierre"})
    did = d["dossier"]["id"]

    result = api._documents_attach_raw(did, [str(src)])
    assert result["ajoutes"] == 1
    assert result["erreurs"] == []

    listing = api.documents_list(did)
    assert len(listing["items"]) == 1
    assert listing["items"][0]["nom"] == "contrat.pdf"


def test_refuses_unauthorized_extension(api, sandbox, tmp_path):
    exe = tmp_path / "virus.exe"
    exe.write_bytes(b"MZ\x90\x00")
    d = api.wizard_create_dossier("certificats", {"nom": "Dupont", "prenom": "Jean"})
    result = api._documents_attach_raw(d["dossier"]["id"], [str(exe)])
    assert result["ajoutes"] == 0
    assert any("non autorisée" in e for e in result["erreurs"])


def test_refuses_missing_file(api, sandbox, tmp_path):
    d = api.wizard_create_dossier("certificats", {"nom": "X", "prenom": "Y"})
    result = api._documents_attach_raw(d["dossier"]["id"], [str(tmp_path / "nope.pdf")])
    assert result["ajoutes"] == 0


def test_refuses_oversized_file(api, sandbox, tmp_path, monkeypatch):
    big = tmp_path / "gros.pdf"
    big.write_bytes(b"0" * 1024)
    monkeypatch.setattr("_app.ui.api._DOCUMENT_MAX_BYTES", 512)
    d = api.wizard_create_dossier("certificats", {"nom": "Big", "prenom": "File"})
    result = api._documents_attach_raw(d["dossier"]["id"], [str(big)])
    assert result["ajoutes"] == 0
    assert any("trop volumineux" in e for e in result["erreurs"])


def test_name_conflicts_are_renamed(api, sandbox, tmp_path):
    src = _make_sample_pdf(tmp_path)
    d = api.wizard_create_dossier("certificats", {"nom": "Conflict", "prenom": "Case"})
    did = d["dossier"]["id"]
    api._documents_attach_raw(did, [str(src)])
    api._documents_attach_raw(did, [str(src)])
    names = [it["nom"] for it in api.documents_list(did)["items"]]
    assert "contrat.pdf" in names
    assert any(n.startswith("contrat_2") for n in names)


def test_remove_moves_to_dossier_trash(api, sandbox, tmp_path):
    src = _make_sample_pdf(tmp_path)
    d = api.wizard_create_dossier("certificats", {"nom": "Trash", "prenom": "Test"})
    did = d["dossier"]["id"]
    api._documents_attach_raw(did, [str(src)])
    res = api.documents_remove(did, "contrat.pdf")
    assert res.get("supprime") is True
    # Fichier absent de la liste
    assert not api.documents_list(did)["items"]
    # Présent dans la corbeille locale du dossier
    dossier = api._dossiers.get(did)
    trash = dossier.subfolder("02_documents_sources") / "_supprimes"
    assert trash.exists()
    assert any(p.suffix == ".pdf" for p in trash.iterdir())


def test_remove_rejects_traversal(api, sandbox, tmp_path):
    src = _make_sample_pdf(tmp_path)
    d = api.wizard_create_dossier("certificats", {"nom": "Safe", "prenom": "Path"})
    did = d["dossier"]["id"]
    api._documents_attach_raw(did, [str(src)])
    res = api.documents_remove(did, "../../dossier.json")
    assert "erreur" in res


def test_attach_writes_audit_event(api, sandbox, tmp_path):
    src = _make_sample_pdf(tmp_path, name="eval_2023.pdf")
    d = api.wizard_create_dossier("certificats", {"nom": "Audit", "prenom": "Trace"})
    did = d["dossier"]["id"]
    api._documents_attach_raw(did, [str(src)])

    dossier = api._dossiers.get(did)
    audit_folder = dossier.subfolder("07_audit")
    traces = list(audit_folder.glob("trace_*.jsonl"))
    assert traces
    content = traces[0].read_text(encoding="utf-8")
    events = [json.loads(line) for line in content.splitlines() if line.strip()]
    kinds = [e["kind"] for e in events]
    assert "document_attached" in kinds
    attached = next(e for e in events if e["kind"] == "document_attached")
    assert attached["nom"] == "eval_2023.pdf"
    assert "sha256" in attached
