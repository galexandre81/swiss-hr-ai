"""Tests : préférence couleur principale + upload logo/signature entité."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# --- Couleur primaire --------------------------------------------------


@pytest.fixture
def api(sandbox, monkeypatch):
    import webview
    monkeypatch.setattr(webview, "windows", [])
    from _app.ui.api import Api
    return Api()


def test_settings_exposes_default_color(api):
    s = api.settings()
    assert s["couleur_primaire"] == "#6B4AAF"


def test_update_accepts_valid_hex(api, sandbox):
    res = api.update_settings({"couleur_primaire": "#336699"})
    assert res["couleur_primaire"] == "#336699"
    data = json.loads((sandbox / "config.json").read_text(encoding="utf-8"))
    assert data["couleur_primaire"] == "#336699"


def test_update_rejects_invalid_hex(api):
    current = api.settings()["couleur_primaire"]
    res = api.update_settings({"couleur_primaire": "red"})
    # Valeur invalide : ignorée silencieusement, la couleur précédente reste.
    assert res["couleur_primaire"] == current


def test_update_rejects_short_hex(api):
    current = api.settings()["couleur_primaire"]
    res = api.update_settings({"couleur_primaire": "#abc"})
    assert res["couleur_primaire"] == current


# --- Assets entité -----------------------------------------------------


def _png_bytes() -> bytes:
    """Renvoie un mini-PNG valide (1×1 transparent)."""
    # PNG 1×1 transparent, minimal.
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\x00\x01"
        b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def test_set_logo_copies_file_and_updates_config(api, sandbox, tmp_path):
    ent = api.create_entity({"nom": "Horlogerie du Léman SA"})["entite"]
    src = tmp_path / "logo_source.png"
    src.write_bytes(_png_bytes())

    ent_mgr = api._entities
    updated = ent_mgr.set_asset(ent["id"], "logo", src)
    assert updated.logo_path.exists()
    assert updated.logo_path.name == "logo.png"

    cfg = json.loads((updated.dossier / "config.json").read_text(encoding="utf-8"))
    assert cfg["logo_fichier"] == "logo.png"


def test_set_signature_with_jpg_extension(api, sandbox, tmp_path):
    ent = api.create_entity({"nom": "Entité JPG"})["entite"]
    src = tmp_path / "sig.jpg"
    # JPEG minimal : pas besoin de vraie image valide ici — on teste la copie.
    src.write_bytes(b"\xff\xd8\xff\xe0fake")

    updated = api._entities.set_asset(ent["id"], "signature", src)
    assert updated.signature_path.exists()
    assert updated.signature_path.suffix == ".jpg"
    cfg = json.loads((updated.dossier / "config.json").read_text(encoding="utf-8"))
    assert cfg["signature_fichier"] == "signature.jpg"


def test_set_asset_rejects_unknown_kind(api, sandbox, tmp_path):
    ent = api.create_entity({"nom": "X"})["entite"]
    src = tmp_path / "a.png"
    src.write_bytes(_png_bytes())
    with pytest.raises(ValueError):
        api._entities.set_asset(ent["id"], "pas_valide", src)


def test_set_asset_rejects_bad_format(api, sandbox, tmp_path):
    ent = api.create_entity({"nom": "X"})["entite"]
    bad = tmp_path / "notes.txt"
    bad.write_bytes(b"nope")
    with pytest.raises(ValueError):
        api._entities.set_asset(ent["id"], "logo", bad)


def test_remove_asset_deletes_file(api, sandbox, tmp_path):
    ent = api.create_entity({"nom": "Retrait"})["entite"]
    src = tmp_path / "logo.png"
    src.write_bytes(_png_bytes())
    api._entities.set_asset(ent["id"], "logo", src)
    assert api._entities.active.logo_path.exists() if api._entities.active else True

    api._entities.remove_asset(ent["id"], "logo")
    updated = api._entities.all()[0]
    assert not updated.logo_path.exists()


def test_api_remove_asset_endpoint(api, sandbox, tmp_path):
    ent = api.create_entity({"nom": "API Retrait"})["entite"]
    src = tmp_path / "logo.png"
    src.write_bytes(_png_bytes())
    api._entities.set_asset(ent["id"], "logo", src)

    res = api.entity_remove_asset(ent["id"], "logo")
    assert "entite" in res
    assert res["entite"]["logo_present"] is False


def test_api_remove_asset_rejects_invalid_kind(api, sandbox):
    ent = api.create_entity({"nom": "X"})["entite"]
    res = api.entity_remove_asset(ent["id"], "avatar")
    assert "erreur" in res


def test_update_entity_changes_name_and_persists(api, sandbox):
    ent = api.create_entity({"nom": "Ancien Nom SA"})["entite"]
    res = api.update_entity(ent["id"], {"nom": "Nouveau Nom Sàrl"})
    assert res["entite"]["nom"] == "Nouveau Nom Sàrl"
    # Persisté sur disque
    cfg = json.loads(
        (sandbox / "Entities" / ent["id"] / "config.json").read_text(encoding="utf-8")
    )
    assert cfg["nom"] == "Nouveau Nom Sàrl"


def test_update_entity_rejects_empty_name(api, sandbox):
    ent = api.create_entity({"nom": "Initial"})["entite"]
    res = api.update_entity(ent["id"], {"nom": "   "})
    assert "erreur" in res


def test_update_entity_ignores_forbidden_fields(api, sandbox):
    ent = api.create_entity({"nom": "Test"})["entite"]
    res = api.update_entity(ent["id"], {
        "nom": "Test",
        "id": "hackez-moi",              # doit être ignoré
        "logo_fichier": "../evil.png",    # doit être ignoré
    })
    # ID et logo_fichier préservés
    assert res["entite"]["id"] == ent["id"]
    cfg = json.loads(
        (sandbox / "Entities" / ent["id"] / "config.json").read_text(encoding="utf-8")
    )
    assert cfg["id"] == ent["id"]
    assert cfg["logo_fichier"] == "logo.png"


def test_update_entity_signataire_nested(api, sandbox):
    ent = api.create_entity({"nom": "T"})["entite"]
    res = api.update_entity(ent["id"], {
        "signataire_nom": "Alice Durand",
        "signataire_fonction": "DRH",
    })
    assert res["entite"]["signataire_nom"] == "Alice Durand"
    assert res["entite"]["signataire_fonction"] == "DRH"


def test_get_entity_returns_editable_fields(api, sandbox):
    ent = api.create_entity({
        "nom": "Société Démo SA",
        "adresse": "Rue Test 1, 1000 Lausanne",
        "signataire_nom": "Jean Test",
    })["entite"]
    data = api.get_entity(ent["id"])
    assert data["nom"] == "Société Démo SA"
    assert data["adresse"] == "Rue Test 1, 1000 Lausanne"
    assert data["signataire_nom"] == "Jean Test"


def test_set_asset_changes_extension(api, sandbox, tmp_path):
    """Si on uploade un PNG puis un JPG, l'ancien PNG est supprimé."""
    ent = api.create_entity({"nom": "Changement"})["entite"]
    png = tmp_path / "l.png"
    png.write_bytes(_png_bytes())
    api._entities.set_asset(ent["id"], "logo", png)
    png_target = (Path(ent["logo_present"]) if False else
                  api._entities.all()[0].dossier / "logo.png")
    assert png_target.exists()

    jpg = tmp_path / "l.jpg"
    jpg.write_bytes(b"\xff\xd8\xff")
    api._entities.set_asset(ent["id"], "logo", jpg)
    jpg_target = api._entities.all()[0].dossier / "logo.jpg"
    assert jpg_target.exists()
    assert not png_target.exists(), "L'ancien .png aurait dû être supprimé."
