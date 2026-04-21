"""Point d'entrée de l'application.

Usage :
    python run.py              # lance l'interface graphique
    python run.py --check      # vérifie juste la connexion LM Studio

Ce fichier reste volontairement minimal : toute la logique est dans _app/.
"""

from __future__ import annotations

import sys


def check_lm_studio() -> int:
    from _app.core import LLMClient
    client = LLMClient()
    info = client.status()
    print(f"[LM Studio] statut : {info.status.value}")
    print(f"[LM Studio] message : {info.message}")
    if info.models:
        print(f"[LM Studio] modèles chargés : {', '.join(info.models)}")
    return 0 if info.status.value == "ready" else 1


def main(argv: list[str]) -> int:
    if "--check" in argv:
        return check_lm_studio()
    # Import tardif : évite d'importer PyWebView lors du --check en CI.
    from _app.ui.app import launch
    launch()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
