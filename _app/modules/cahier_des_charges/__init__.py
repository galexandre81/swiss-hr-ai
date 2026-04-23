"""Module Cahier des charges.

Produit (a) un cahier des charges .docx structuré en 11 sections
inspirées des modèles officiels romands (Vaud, Genève, Fribourg),
et (b) jusqu'à 4 variantes d'annonce d'emploi à partir de ce document.

Implémenté comme EditorModule : le livrable est un document vivant,
édité par sections, avec copilote LLM contextuel et sauvegarde auto.

Voir `module.py` pour la définition du module, `models.py` pour les
structures de données, et `catalogue_store.py` pour la persistance.

Références :
    - specs/cahier_des_charges/01_SPEC_FONCTIONNEL.md
    - specs/cahier_des_charges/02_STRUCTURE_DOCX.md
    - 12_DIVERGENCES_CAHIER_DES_CHARGES.md
"""

from _app.modules.cahier_des_charges.module import Module

__all__ = ["Module"]
