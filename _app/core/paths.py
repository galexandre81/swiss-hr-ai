"""Helpers de sécurité sur les chemins.

Tout chemin qui vient du frontend ou d'un fichier utilisateur passe par
safe_within(): on garantit qu'il reste confiné à la racine projet.
Cela empêche un "../.." malicieux dans un config.json d'entité de lire
des fichiers arbitraires sur le poste.
"""

from __future__ import annotations

from pathlib import Path


def safe_within(candidate: Path, root: Path) -> Path | None:
    """Retourne le chemin résolu si `candidate` est strictement sous `root`, sinon None.

    - Résout les liens symboliques (via .resolve()).
    - Accepte les chemins qui n'existent pas encore (ex : fichier qu'on va créer),
      mais refuse ceux qui échappent du root une fois résolus.
    """
    try:
        resolved = candidate.resolve()
        root_resolved = root.resolve()
    except (OSError, RuntimeError):
        return None
    try:
        resolved.relative_to(root_resolved)
    except ValueError:
        return None
    return resolved
