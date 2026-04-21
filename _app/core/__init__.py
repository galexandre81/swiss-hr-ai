"""Socle partagé : services utilisés par tous les modules RH."""

from _app.core.config import Config, get_config
from _app.core.logger import Logger, get_logger
from _app.core.llm_client import LLMClient, LLMStatus
from _app.core.entity_manager import EntityManager, Entity
from _app.core.module_base import ModuleBase
from _app.core.module_registry import ModuleRegistry

__all__ = [
    "Config",
    "get_config",
    "Logger",
    "get_logger",
    "LLMClient",
    "LLMStatus",
    "EntityManager",
    "Entity",
    "ModuleBase",
    "ModuleRegistry",
]
