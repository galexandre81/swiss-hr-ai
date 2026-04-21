"""Lecture du config.json global de l'application.

Un seul point d'entrée : get_config().
Les chemins retournés sont des Path absolus résolus depuis la racine projet.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# Racine = dossier qui contient _app/, Base_Juridique/, Templates/, etc.
# _app/core/config.py → remonte de 2 niveaux pour atteindre la racine.
ROOT_DIR: Path = Path(__file__).resolve().parent.parent.parent


@dataclass
class Config:
    """Configuration globale chargée depuis config.json."""

    # Endpoint LM Studio (API compatible OpenAI)
    lm_studio_url: str = "http://localhost:1234/v1"
    lm_studio_model: str = "qwen-3.5-9b"
    lm_studio_timeout: int = 120

    # Températures par défaut
    temperature_factuel: float = 0.1
    temperature_neutre: float = 0.3
    temperature_creatif: float = 0.7

    # Langue de l'interface
    langue: str = "fr"

    # Entité active au démarrage (id ; si vide : première détectée)
    entite_active: str = ""

    # Chemins (relatifs à ROOT_DIR) — on les stocke en Path résolu
    chemin_base_juridique: Path = field(default_factory=lambda: ROOT_DIR / "Base_Juridique")
    chemin_templates: Path = field(default_factory=lambda: ROOT_DIR / "Templates")
    chemin_entities: Path = field(default_factory=lambda: ROOT_DIR / "Entities")
    chemin_outputs: Path = field(default_factory=lambda: ROOT_DIR / "Outputs")
    chemin_logs: Path = field(default_factory=lambda: ROOT_DIR / "Logs")
    chemin_data: Path = field(default_factory=lambda: ROOT_DIR / "data")

    @property
    def root(self) -> Path:
        return ROOT_DIR

    @classmethod
    def load(cls, path: Path | None = None) -> "Config":
        """Charge config.json à la racine, ou valeurs par défaut si absent."""
        cfg_path = path or (ROOT_DIR / "config.json")
        cfg = cls()
        if cfg_path.exists():
            try:
                data: dict[str, Any] = json.loads(cfg_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"config.json mal formé : {exc}. Corrigez le fichier ou supprimez-le "
                    f"pour retrouver les valeurs par défaut."
                ) from exc
            for key, value in data.items():
                if hasattr(cfg, key) and not key.startswith("chemin_"):
                    setattr(cfg, key, value)
        # Création défensive des dossiers (utile au premier lancement)
        for attr in (
            "chemin_base_juridique",
            "chemin_templates",
            "chemin_entities",
            "chemin_outputs",
            "chemin_logs",
            "chemin_data",
        ):
            getattr(cfg, attr).mkdir(parents=True, exist_ok=True)
        return cfg


_cached_config: Config | None = None


def get_config() -> Config:
    """Singleton simple — la config est lue une seule fois par exécution."""
    global _cached_config
    if _cached_config is None:
        _cached_config = Config.load()
    return _cached_config
