"""Contrat pour les modules "wizard" — flows multi-étapes stateful.

Certains modules RH (certificats, lettres complexes, analyse CCT) ne
rentrent pas dans le pattern `inputs → run → output` mono-coup de
`ModuleBase` : ils nécessitent un flow stateful sur plusieurs jours,
avec reprise de session, décisions tracées, multi-managers, etc.

Un WizardModule :
    - définit une suite ordonnée de **Step** ;
    - chaque step a son propre schéma d'inputs ;
    - l'état est persisté dans le **dossier collaborateur** associé ;
    - la génération finale (`finalize`) utilise l'état consolidé.

Le dashboard détecte les WizardModule et ouvre une vue dédiée (liste
des dossiers + reprise + nouvelle entrée).

Ce contrat **étend** `ModuleBase` sans le casser : un WizardModule
reste introspectable par `ModuleRegistry` comme n'importe quel module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from _app.core.module_base import ModuleBase, ModuleContext


@dataclass
class WizardStep:
    """Définition d'une étape du wizard.

    - `id` : identifiant stable (utilisé comme clé dans wizard_state).
    - `label` : titre affiché.
    - `description` : aide contextuelle (court paragraphe).
    - `inputs` : liste de champs au même format que `ModuleBase.inputs_schema()`.
    - `required_fields` : ids des champs strictement obligatoires pour
      valider l'étape (sous-ensemble de `inputs`).
    """

    id: str
    label: str
    description: str = ""
    inputs: list[dict[str, Any]] = field(default_factory=list)
    required_fields: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "description": self.description,
            "inputs": self.inputs,
            "required_fields": self.required_fields,
        }


class WizardModuleBase(ModuleBase):
    """Classe mère pour modules multi-étapes stateful.

    Implémentation concrète :
        - surcharger `steps()` ;
        - surcharger `validate_step()` (optionnel — validations métier) ;
        - surcharger `finalize()` — génère le livrable final.

    Le state vit dans `Dossier.wizard_state`. Structure imposée :
        {
          "step": "<id_courant>",       # étape active
          "answers": {                   # réponses par step
            "<step_id>": { ...champs... }
          },
          "completed": ["<step_id>", ...],
          "finalized": false,
        }
    """

    # Attribut de classe : à True = le frontend doit ouvrir la vue wizard
    # au lieu du formulaire mono-écran.
    is_wizard: bool = True

    # --- Définition des étapes ------------------------------------------

    def steps(self) -> list[WizardStep]:
        raise NotImplementedError

    def step_index(self, step_id: str) -> int:
        for i, s in enumerate(self.steps()):
            if s.id == step_id:
                return i
        return -1

    def step_by_id(self, step_id: str) -> WizardStep | None:
        for s in self.steps():
            if s.id == step_id:
                return s
        return None

    def first_step_id(self) -> str:
        steps = self.steps()
        return steps[0].id if steps else ""

    # --- État persistant (dans Dossier.wizard_state) --------------------

    @staticmethod
    def empty_state() -> dict[str, Any]:
        return {
            "step": "",
            "answers": {},
            "completed": [],
            "finalized": False,
        }

    def ensure_state(self, state: dict[str, Any]) -> dict[str, Any]:
        """Normalise un état potentiellement vide/legacy."""
        if not isinstance(state, dict):
            state = {}
        merged = self.empty_state()
        merged.update({k: v for k, v in state.items() if k in merged})
        if not merged["step"]:
            merged["step"] = self.first_step_id()
        return merged

    # --- Validation d'étape ---------------------------------------------

    def validate_step(
        self,
        step_id: str,
        answers: dict[str, Any],
    ) -> list[str]:
        """Retourne la liste des messages d'erreur. Vide = valide.

        Impl par défaut : contrôle des `required_fields`. À surcharger
        dans le module concret pour ajouter des règles métier.
        """
        step = self.step_by_id(step_id)
        if step is None:
            return [f"Étape inconnue : {step_id!r}."]
        errors: list[str] = []
        for fid in step.required_fields:
            val = answers.get(fid)
            if val is None or (isinstance(val, str) and not val.strip()):
                label = next(
                    (f.get("label", fid) for f in step.inputs if f.get("id") == fid),
                    fid,
                )
                errors.append(f"Champ obligatoire : {label}")
        return errors

    # --- Transitions ----------------------------------------------------

    def record_answers(
        self,
        state: dict[str, Any],
        step_id: str,
        answers: dict[str, Any],
    ) -> dict[str, Any]:
        state = self.ensure_state(state)
        state["answers"][step_id] = answers
        if step_id not in state["completed"]:
            state["completed"].append(step_id)
        # Avance automatiquement à l'étape suivante si elle existe.
        idx = self.step_index(step_id)
        steps = self.steps()
        if idx >= 0 and idx + 1 < len(steps):
            state["step"] = steps[idx + 1].id
        return state

    def can_finalize(self, state: dict[str, Any]) -> tuple[bool, list[str]]:
        """True si toutes les étapes requises sont complétées."""
        state = self.ensure_state(state)
        missing: list[str] = []
        for step in self.steps():
            if step.id not in state["completed"]:
                missing.append(step.label)
        return (len(missing) == 0, missing)

    # --- Exécution ------------------------------------------------------

    def finalize(
        self,
        state: dict[str, Any],
        ctx: ModuleContext,
    ) -> dict[str, Any]:
        """Produit le livrable final à partir de l'état consolidé.

        Retourne un dict au moins : {"texte": "...", "alertes": [...]}.
        À surcharger.
        """
        raise NotImplementedError

    # --- Compatibilité ModuleBase ---------------------------------------

    def run(self, inputs: dict[str, Any], ctx: ModuleContext) -> dict[str, Any]:
        """Rappel : les wizards passent par `finalize`, pas `run`.

        On garde ce hook pour que ModuleRegistry continue de fonctionner
        sans distinction côté découverte. Un appel direct à run() n'est
        pas supporté — l'UI doit emprunter le chemin wizard.
        """
        raise RuntimeError(
            "Module wizard : utilisez l'API wizard_* plutôt que run(). "
            f"(module={self.id})"
        )

    def meta(self) -> dict[str, Any]:
        base = super().meta()
        base["is_wizard"] = True
        return base

    def inputs_schema(self) -> list[dict[str, Any]]:
        """Exposition plate des inputs, pour compat avec les vues legacy."""
        out: list[dict[str, Any]] = []
        for step in self.steps():
            for field_ in step.inputs:
                out.append({**field_, "_step": step.id})
        return out
