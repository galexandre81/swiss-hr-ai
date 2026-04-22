"""Lecture et écriture du config.json global de l'application.

Un seul point d'entrée : get_config().
Les chemins retournés sont des Path absolus résolus depuis la racine projet.

Les préférences utilisateur (theme, audit_log_prompts, entité active, ...)
sont persistées via save_user_preferences() et relues au prochain démarrage.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Racine = dossier qui contient _app/, Base_Juridique/, Templates/, etc.
# _app/core/config.py → remonte de 2 niveaux pour atteindre la racine.
ROOT_DIR: Path = Path(__file__).resolve().parent.parent.parent


# Champs considérés comme des préférences utilisateur modifiables depuis l'UI.
# Seuls ceux-ci peuvent être réécrits dans config.json par save_user_preferences().
USER_PREF_FIELDS = frozenset(
    {"entite_active", "theme", "audit_log_prompts", "lm_studio_model", "couleur_primaire"}
)

# Violet ARHIANE par défaut. Peut être modifié par l'utilisateur dans Paramètres.
DEFAULT_COULEUR_PRIMAIRE = "#6B4AAF"


@dataclass
class Config:
    """Configuration globale chargée depuis config.json."""

    # Endpoint LM Studio (API compatible OpenAI).
    lm_studio_url: str = "http://localhost:1234/v1"
    # Vide = auto-détection (on prend le premier modèle chargé dans LM Studio).
    lm_studio_model: str = ""
    lm_studio_timeout: int = 120
    lm_studio_connect_timeout: int = 3

    # Températures par défaut.
    temperature_factuel: float = 0.1
    temperature_neutre: float = 0.3
    temperature_creatif: float = 0.7

    # Langue de l'interface.
    langue: str = "fr"

    # Entité active au démarrage (id ; si vide : première détectée).
    entite_active: str = ""

    # Préférences UI / conformité.
    theme: str = "auto"              # "auto" | "light" | "dark"
    couleur_primaire: str = DEFAULT_COULEUR_PRIMAIRE  # hex #RRGGBB — accent UI + PDFs
    audit_log_prompts: bool = False  # False = on log un hash + longueur, pas le contenu

    # Chemins (relatifs à ROOT_DIR).
    chemin_base_juridique: Path = field(default_factory=lambda: ROOT_DIR / "Base_Juridique")
    chemin_templates: Path = field(default_factory=lambda: ROOT_DIR / "Templates")
    chemin_entities: Path = field(default_factory=lambda: ROOT_DIR / "Entities")
    chemin_outputs: Path = field(default_factory=lambda: ROOT_DIR / "Outputs")
    chemin_logs: Path = field(default_factory=lambda: ROOT_DIR / "Logs")
    chemin_data: Path = field(default_factory=lambda: ROOT_DIR / "data")
    # Dossiers collaborateurs (un sous-dossier par collaborateur — §17 spec cert.).
    chemin_dossiers: Path = field(default_factory=lambda: ROOT_DIR / "Dossiers")
    # Bibliothèques de formulations validées par langue (§20 spec cert.).
    chemin_bibliotheques: Path = field(default_factory=lambda: ROOT_DIR / "Bibliotheques")

    @property
    def root(self) -> Path:
        return ROOT_DIR

    @classmethod
    def load(cls, path: Path | None = None) -> Config:
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
        # Création défensive des dossiers (utile au premier lancement).
        for attr in (
            "chemin_base_juridique",
            "chemin_templates",
            "chemin_entities",
            "chemin_outputs",
            "chemin_logs",
            "chemin_data",
            "chemin_dossiers",
            "chemin_bibliotheques",
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


def save_user_preferences(updates: dict[str, Any]) -> None:
    """Réécrit config.json en ne modifiant que les champs USER_PREF_FIELDS.

    On ne persiste jamais les chemins ni les URLs — ces réglages sont du
    ressort de l'administrateur qui édite config.json manuellement.
    """
    cfg_path = ROOT_DIR / "config.json"
    try:
        data = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}
    except json.JSONDecodeError:
        data = {}

    cfg = get_config()
    for key, value in updates.items():
        if key not in USER_PREF_FIELDS:
            continue
        data[key] = value
        if hasattr(cfg, key):
            setattr(cfg, key, value)

    cfg_path.write_text(
        json.dumps(data, indent=4, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def reset_cache() -> None:
    """Utile pour les tests : force un rechargement propre."""
    global _cached_config
    _cached_config = None
