"""Module Générateur de Certificats de travail (art. 330a CO).

Implémenté comme WizardModule : flow stateful persisté dans un dossier
collaborateur, garde-fous déterministes, formulations validées.

Voir `module.py` pour les étapes et `generator.py` pour l'assemblage.
"""

from _app.modules.certificats.module import Module

__all__ = ["Module"]
