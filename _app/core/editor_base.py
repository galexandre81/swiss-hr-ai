"""Contrat pour les modules "éditeur" — flows centrés sur un document vivant.

Les modules existants d'Arhiane se répartissent en deux familles :

- `ModuleBase` : formulaire → run → document final (mono-coup).
- `WizardModuleBase` : suite d'étapes ordonnées, chaque étape valide ses
  inputs et avance à la suivante. Le document final est produit par
  `finalize()` à la fin.

Le module "Cahier des charges" introduit une troisième famille :
l'**éditeur**. Le livrable est un document vivant, édité par sections,
sauvegardé automatiquement, enrichi progressivement par le RH en
dialogue avec un copilote LLM contextuel. Pas d'ordre imposé entre
sections, pas de passage obligé, plusieurs allers-retours entre
génération automatique et édition manuelle.

Un EditorModule :
    - définit une suite de **sections** (au moins titre + id ; la
      structure interne d'une section est propre au module concret) ;
    - persiste le document sous forme de fichier JSON unique par
      document (le catalogue du module gère le versioning, cf.
      `catalogue_store.py` côté modules/cahier_des_charges/) ;
    - expose `generate_section()` pour la génération LLM ciblée
      d'une section ;
    - expose `run_action()` pour les actions contextuelles (reformuler,
      traduire, raccourcir, etc.).

Ce contrat **étend** `ModuleBase` sans le casser : un EditorModule reste
introspectable par `ModuleRegistry` comme n'importe quel module. Le
dashboard lit `is_editor` dans les meta et route vers une vue dédiée.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from _app.core.module_base import ModuleBase, ModuleContext


@dataclass
class EditorSection:
    """Définition d'une section de document éditable.

    - `id` : identifiant stable (clé utilisée dans le JSON du document).
    - `titre` : titre affiché dans la navigation gauche de l'éditeur.
    - `description` : aide contextuelle (courte, 1-2 phrases).
    - `obligatoire` : True si la section doit être remplie avant
      validation finale (une section incomplète affichera une alerte
      informative, jamais bloquante — conforme doctrine Arhiane).
    - `verrouillee_apres_validation` : si True, la section n'est plus
      éditable une fois le document validé (usage rare).
    """

    id: str
    titre: str
    description: str = ""
    obligatoire: bool = True
    verrouillee_apres_validation: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "titre": self.titre,
            "description": self.description,
            "obligatoire": self.obligatoire,
            "verrouillee_apres_validation": self.verrouillee_apres_validation,
        }


@dataclass
class EditorAction:
    """Action contextuelle disponible sur une section du document.

    Exemples : "reformuler en plus court", "traduire en allemand",
    "proposer une variante plus technique". Ces actions appellent le
    LLM avec un prompt ciblé et remplacent ou complètent le texte de
    la section.

    - `id` : identifiant stable (ex: "reformuler", "raccourcir").
    - `label` : libellé affiché dans l'UI.
    - `sections` : liste des sections où l'action est disponible. Vide
      = disponible partout.
    """

    id: str
    label: str
    description: str = ""
    sections: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "description": self.description,
            "sections": list(self.sections),
        }


class EditorModuleBase(ModuleBase):
    """Classe mère pour modules éditeur.

    Implémentation concrète :
        - surcharger `sections()` — liste ordonnée des sections ;
        - surcharger `actions()` — actions contextuelles disponibles ;
        - surcharger `empty_document()` — gabarit vide d'un nouveau
          document (structure JSON avec toutes les sections à null) ;
        - surcharger `generate_initial()` — génération LLM initiale à
          partir des inputs de cadrage ;
        - surcharger `generate_section()` — génération ou régénération
          d'une section spécifique ;
        - surcharger `run_action()` — exécute une action contextuelle.

    L'état d'un document est un dict arbitraire, propre au module. Seule
    la clé `_meta` est réservée (versioning, dates, auteur). Le
    catalogue gère la persistance (pas cette classe).
    """

    # Attribut de classe : True = le frontend doit ouvrir la vue éditeur
    # au lieu du formulaire mono-écran ou du wizard.
    is_editor: bool = True

    # Clé réservée dans les documents pour les métadonnées techniques
    # (versioning, dates, auteur). Les modules concrets ne doivent pas
    # l'utiliser pour du contenu métier.
    META_KEY = "_meta"

    # --- Définition de la structure -------------------------------------

    def sections(self) -> list[EditorSection]:
        raise NotImplementedError

    def actions(self) -> list[EditorAction]:
        """Liste des actions contextuelles. Vide par défaut."""
        return []

    def section_by_id(self, section_id: str) -> EditorSection | None:
        for s in self.sections():
            if s.id == section_id:
                return s
        return None

    # --- Gabarit vide ----------------------------------------------------

    def empty_document(self) -> dict[str, Any]:
        """Gabarit vide d'un nouveau document.

        Par défaut : une clé par section, valeur = None. Les modules
        concrets surchargent pour injecter des structures plus riches
        (ex: liste de missions avec objets imbriqués).
        """
        doc: dict[str, Any] = {s.id: None for s in self.sections()}
        return doc

    # --- Statut de complétude ------------------------------------------

    def section_is_filled(self, document: dict[str, Any], section_id: str) -> bool:
        """Une section est "remplie" si sa valeur n'est ni None ni vide.

        À surcharger dans les modules concrets pour gérer des types
        plus complexes (liste de missions avec au moins une entrée, etc.).
        """
        value = document.get(section_id)
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, (list, dict)):
            return len(value) > 0
        return True

    def completion_status(self, document: dict[str, Any]) -> dict[str, Any]:
        """Statistiques de complétude pour l'affichage UI.

        Retourne :
            {
              "total": 11,
              "remplies": 7,
              "obligatoires_manquantes": ["raison_detre", ...],
              "pourcentage": 64,
            }
        """
        sections = self.sections()
        remplies: list[str] = []
        manquantes_oblig: list[str] = []
        for s in sections:
            if self.section_is_filled(document, s.id):
                remplies.append(s.id)
            elif s.obligatoire:
                manquantes_oblig.append(s.id)
        total = len(sections)
        pct = int(round(100 * len(remplies) / total)) if total else 0
        return {
            "total": total,
            "remplies": len(remplies),
            "obligatoires_manquantes": manquantes_oblig,
            "pourcentage": pct,
        }

    # --- Génération LLM (à surcharger par les modules concrets) ---------

    def generate_initial(
        self,
        inputs: dict[str, Any],
        ctx: ModuleContext,
    ) -> dict[str, Any]:
        """Génération initiale du document à partir des inputs de cadrage.

        Retour : un document partiel avec les sections pré-remplies par
        le LLM. Les sections non générées sont laissées à None.
        """
        raise NotImplementedError

    def generate_section(
        self,
        section_id: str,
        document: dict[str, Any],
        ctx: ModuleContext,
    ) -> Any:
        """(Re)génère une section spécifique à partir du document courant.

        Retourne la nouvelle valeur de la section (pas le document entier).
        """
        raise NotImplementedError

    def run_action(
        self,
        action_id: str,
        section_id: str,
        document: dict[str, Any],
        ctx: ModuleContext,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Exécute une action contextuelle sur une section.

        Retourne la nouvelle valeur de la section.
        """
        raise NotImplementedError

    # --- Compatibilité ModuleBase ---------------------------------------

    def run(self, inputs: dict[str, Any], ctx: ModuleContext) -> dict[str, Any]:
        """Rappel : les modules éditeur passent par les appels ciblés,
        pas un `run()` monolithique. Ce hook est conservé pour compat
        avec ModuleRegistry mais un appel direct lève une erreur claire.
        """
        raise RuntimeError(
            "Module éditeur : utilisez l'API editor_* plutôt que run(). "
            f"(module={self.id})"
        )

    def meta(self) -> dict[str, Any]:
        base = super().meta()
        base["is_editor"] = True
        base["sections"] = [s.as_dict() for s in self.sections()]
        base["actions"] = [a.as_dict() for a in self.actions()]
        return base

    def inputs_schema(self) -> list[dict[str, Any]]:
        """Exposition plate des inputs de cadrage initial.

        Par défaut, pas d'inputs : le document démarre vide et se
        construit via les appels à `generate_initial` / `generate_section`
        / édition manuelle. Les modules concrets surchargent pour demander
        les quelques questions de cadrage au démarrage.
        """
        return []
