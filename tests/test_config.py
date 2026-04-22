from __future__ import annotations

import json

from _app.core.config import (
    USER_PREF_FIELDS,
    get_config,
    save_user_preferences,
)


def test_loads_defaults_when_config_missing(sandbox):
    (sandbox / "config.json").unlink()
    cfg = get_config()
    assert cfg.lm_studio_url.startswith("http://localhost")
    assert cfg.lm_studio_model == ""
    assert cfg.chemin_entities == sandbox / "Entities"


def test_reads_user_fields_only(sandbox):
    (sandbox / "config.json").write_text(
        json.dumps({
            "theme": "dark",
            "audit_log_prompts": True,
            "chemin_outputs": "/etc",  # tentative d'override — doit être ignorée
        }),
        encoding="utf-8",
    )
    cfg = get_config()
    assert cfg.theme == "dark"
    assert cfg.audit_log_prompts is True
    assert cfg.chemin_outputs == sandbox / "Outputs"


def test_save_user_preferences_persists_only_whitelist(sandbox):
    save_user_preferences({
        "theme": "light",
        "lm_studio_url": "http://evil.example.com",  # doit être ignoré
    })
    data = json.loads((sandbox / "config.json").read_text(encoding="utf-8"))
    assert data["theme"] == "light"
    assert "lm_studio_url" not in data or data["lm_studio_url"].startswith("http://localhost")


def test_whitelist_contains_expected_fields():
    assert "theme" in USER_PREF_FIELDS
    assert "audit_log_prompts" in USER_PREF_FIELDS
    assert "entite_active" in USER_PREF_FIELDS
    assert "lm_studio_url" not in USER_PREF_FIELDS
    assert "chemin_entities" not in USER_PREF_FIELDS
