"""Socle partagé : services utilisés par tous les modules RH."""

from _app.core.audit_trail import AuditEvent, AuditTrail, sha256_of
from _app.core.blacklist_detector import (
    SEVERITE_ALERTE,
    SEVERITE_BLOQUANT,
    BlacklistDetector,
    BlacklistHit,
)
from _app.core.config import Config, get_config, save_user_preferences
from _app.core.dossier_store import Collaborateur, Dossier, DossierStore
from _app.core.editor_base import EditorAction, EditorModuleBase, EditorSection
from _app.core.entity_manager import Entity, EntityManager
from _app.core.formulation_library import FormulationLibrary, LibraryInfo
from _app.core.llm_client import GenerationCancelled, LLMClient, LLMStatus
from _app.core.logger import Logger, get_logger
from _app.core.module_base import ModuleBase, ModuleContext
from _app.core.module_registry import ModuleRegistry
from _app.core.paths import safe_within
from _app.core.questionnaire_engine import (
    STANDARD_CRITERES_FR,
    Critere,
    QuestionnaireContext,
    QuestionnaireEngine,
)
from _app.core.wizard_base import WizardModuleBase, WizardStep

__all__ = [
    "Config",
    "get_config",
    "save_user_preferences",
    "Logger",
    "get_logger",
    "LLMClient",
    "LLMStatus",
    "GenerationCancelled",
    "EntityManager",
    "Entity",
    "ModuleBase",
    "ModuleContext",
    "ModuleRegistry",
    "safe_within",
    # --- Certificats / wizards -----
    "WizardModuleBase",
    "WizardStep",
    # --- Cahier des charges / éditeur -----
    "EditorModuleBase",
    "EditorSection",
    "EditorAction",
    "DossierStore",
    "Dossier",
    "Collaborateur",
    "AuditTrail",
    "AuditEvent",
    "sha256_of",
    "FormulationLibrary",
    "LibraryInfo",
    "BlacklistDetector",
    "BlacklistHit",
    "SEVERITE_ALERTE",
    "SEVERITE_BLOQUANT",
    "QuestionnaireEngine",
    "QuestionnaireContext",
    "Critere",
    "STANDARD_CRITERES_FR",
]
