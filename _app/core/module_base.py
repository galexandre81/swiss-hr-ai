"""Contrat de module : classe mère que tous les outils RH doivent hériter.

Un module = un dossier dans _app/modules/ contenant un fichier module.py
qui définit une sous-classe de ModuleBase nommée `Module`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ModuleContext:
    """Services mis à disposition d'un module lors de son exécution.

    On passe les services par un objet plutôt qu'en paramètres individuels
    pour pouvoir en ajouter plus tard (ex: rag_engine, doc_engine) sans
    casser la signature run() des modules existants.
    """

    llm: Any              # _app.core.LLMClient
    entity: Any | None    # _app.core.Entity (peut être None)
    logger: Any           # _app.core.Logger
    rag: Any | None = None       # RAG engine (sera branché plus tard)
    doc: Any | None = None       # doc engine (sera branché plus tard)
    extras: dict[str, Any] = field(default_factory=dict)


class ModuleBase:
    """Classe mère de tous les modules RH.

    Chaque module concret doit au minimum :
        - surcharger les attributs de classe id/nom/icone/description/temperature
        - implémenter inputs_schema() et run()
    """

    # --- Métadonnées (surcharger dans chaque module) ---------------------

    id: str = "base"
    nom: str = "Module"
    icone: str = "default"             # nom d'icône (ex: "certificat", "balance")
    description: str = ""
    categorie: str = "general"          # "juridique", "documents", "rh", ...
    temperature: float = 0.3
    statut: str = "disponible"          # "disponible" ou "a_venir"

    # --- Interface ---------------------------------------------------------

    def inputs_schema(self) -> list[dict[str, Any]]:
        """Décrit les champs du formulaire d'entrée.

        Chaque champ est un dict de la forme :
            {"id": "nom_employe", "label": "Nom de l'employé",
             "type": "text" | "textarea" | "number" | "select" | "rating5" | "file",
             "required": True, "aide": "..."}
        """
        return []

    def run(self, inputs: dict[str, Any], ctx: ModuleContext) -> dict[str, Any]:
        """Exécute le module.

        Retourne un dict avec au minimum :
            {"texte": "...",              # contenu généré (affichable)
             "fichier": "chemin/abs",     # optionnel — document produit
             "sources": [...]}            # optionnel — passages RAG cités
        """
        raise NotImplementedError

    # --- Métadonnées exposées au frontend --------------------------------

    def meta(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "nom": self.nom,
            "icone": self.icone,
            "description": self.description,
            "categorie": self.categorie,
            "statut": self.statut,
        }
