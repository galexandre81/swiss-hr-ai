"""Pont JavaScript <-> Python pour PyWebView.

Toutes les méthodes publiques de la classe Api sont exposées au JS sous
la forme `window.pywebview.api.<methode>(...)` et retournent des objets
JSON-sérialisables.

Règle : JAMAIS de Path ou d'objets Python non-sérialisables dans les
retours — on renvoie toujours des dicts/listes/strings.
"""

from __future__ import annotations

from typing import Any

from _app.core import (
    EntityManager,
    LLMClient,
    ModuleRegistry,
    get_config,
    get_logger,
)


class Api:
    """API exposée au frontend HTML."""

    def __init__(self):
        self._cfg = get_config()
        self._log = get_logger()
        self._llm = LLMClient()
        self._entities = EntityManager()
        self._registry = ModuleRegistry()

    # --- Statut général (pour la barre du bas) ---------------------------

    def status(self) -> dict[str, Any]:
        llm_info = self._llm.status()
        active = self._entities.active
        return {
            "llm": llm_info.as_dict(),
            "entite_active": active.as_dict() if active else None,
            "nb_entites": len(self._entities.all()),
            "version": "0.1.0",
            "hors_ligne": True,
        }

    # --- Entités ---------------------------------------------------------

    def list_entities(self) -> list[dict[str, Any]]:
        return [e.as_dict() for e in self._entities.all()]

    def set_active_entity(self, entity_id: str) -> dict[str, Any] | None:
        ent = self._entities.set_active(entity_id)
        return ent.as_dict() if ent else None

    def rescan_entities(self) -> list[dict[str, Any]]:
        self._entities.rescan()
        return self.list_entities()

    # --- Modules ---------------------------------------------------------

    def list_modules(self) -> list[dict[str, Any]]:
        return self._registry.list_modules()

    def run_module(self, module_id: str, inputs: dict[str, Any]) -> dict[str, Any]:
        """Exécute un module (futur — stub pour l'instant)."""
        mod = self._registry.get(module_id)
        if mod is None:
            return {"erreur": f"Module '{module_id}' non disponible (à venir)."}
        from _app.core.module_base import ModuleContext
        ctx = ModuleContext(
            llm=self._llm,
            entity=self._entities.active,
            logger=self._log,
        )
        try:
            result = mod.run(inputs, ctx)
        except Exception as exc:
            self._log.error(f"Module {module_id} a échoué : {exc!r}")
            return {"erreur": f"Erreur pendant l'exécution : {exc}"}
        self._log.audit(
            "module_run",
            module=module_id,
            entity=self._entities.active.id if self._entities.active else None,
            inputs_keys=list(inputs.keys()),
        )
        return result

    # --- Divers ----------------------------------------------------------

    def open_folder(self, dossier: str) -> bool:
        """Ouvre un dossier du projet dans l'Explorateur Windows."""
        import os
        import subprocess

        mapping = {
            "base_juridique": self._cfg.chemin_base_juridique,
            "templates": self._cfg.chemin_templates,
            "entities": self._cfg.chemin_entities,
            "outputs": self._cfg.chemin_outputs,
            "logs": self._cfg.chemin_logs,
        }
        target = mapping.get(dossier)
        if target is None or not target.exists():
            return False
        try:
            if os.name == "nt":
                os.startfile(str(target))  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", str(target)])
            return True
        except Exception as exc:
            self._log.error(f"Ouverture dossier {dossier} échouée : {exc}")
            return False
