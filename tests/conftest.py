"""Fixtures partagées.

Chaque test s'exécute dans un dossier temporaire qui ressemble à la
racine projet (avec un `config.json` + les dossiers attendus), puis on
patche ROOT_DIR pour que tout le socle pointe vers ce bac à sable.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Import anticipé des modules à patcher.
from _app.core import config as config_mod
from _app.core import logger as logger_mod


@pytest.fixture
def sandbox(tmp_path, monkeypatch) -> Path:
    """Crée une racine projet isolée et redirige le socle dessus."""
    (tmp_path / "Base_Juridique").mkdir()
    (tmp_path / "Templates").mkdir()
    (tmp_path / "Entities").mkdir()
    (tmp_path / "Outputs").mkdir()
    (tmp_path / "Logs").mkdir()
    (tmp_path / "data").mkdir()
    (tmp_path / "Dossiers").mkdir()
    (tmp_path / "Bibliotheques").mkdir()
    (tmp_path / "Bibliotheques" / "fr").mkdir()

    (tmp_path / "config.json").write_text(
        json.dumps({
            "lm_studio_url": "http://localhost:1234/v1",
            "lm_studio_model": "",
            "theme": "auto",
            "audit_log_prompts": False,
        }),
        encoding="utf-8",
    )

    monkeypatch.setattr(config_mod, "ROOT_DIR", tmp_path)
    config_mod.reset_cache()
    logger_mod.reset_cache()
    yield tmp_path
    config_mod.reset_cache()
    logger_mod.reset_cache()
    # Purge les modules importés dynamiquement pendant les tests de registry.
    for name in list(sys.modules):
        if name.startswith("_app.modules."):
            sys.modules.pop(name, None)
