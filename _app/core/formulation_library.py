"""Bibliothèque de formulations validées par langue et par niveau.

Enjeu critique (§8.3 spec cert.) : le LLM ne doit PAS choisir librement
la formule d'appréciation synthèse. Il sélectionne parmi des tournures
pré-validées qui correspondent à un niveau explicite sur l'échelle de
1 (mauvais) à 5 (excellent).

Structure de fichier attendue :

    Bibliotheques/<langue>/formulations_validees.json
    {
      "version": "2026-04-22",
      "langue": "fr",
      "valide_par": "Gates Solutions Sàrl — à faire relire par un juriste",
      "formulations": {
        "appreciation_globale": {
          "5": ["...", "..."],
          "4": ["..."],
          "3": ["..."],
          "2": ["..."],
          "1": ["..."]
        },
        "qualite_travail": { ... },
        "comportement_hierarchie": { ... },
        ...
      }
    }

Les clés de critère sont libres — chaque module utilise celles qu'il
connaît. Les niveaux sont des chaînes "1".."5" pour rester compatibles
JSON. Chaque entrée = liste de variantes (permet d'éviter la répétition
quand on génère plusieurs certificats).

FR et DE partagent la même structure ; EN a les mêmes clés mais des
formulations plus directes, moins codées (cf. §20.3).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from _app.core.config import get_config
from _app.core.logger import get_logger
from _app.core.paths import safe_within

LIBRARY_FILENAME = "formulations_validees.json"
VALID_LEVELS: tuple[str, ...] = ("1", "2", "3", "4", "5")


@dataclass
class LibraryInfo:
    langue: str
    version: str
    valide_par: str
    criteres: list[str]


class FormulationLibrary:
    """Accès lecture-seule aux formulations par langue."""

    def __init__(self, racine: Path | None = None):
        cfg = get_config()
        self._log = get_logger()
        self._racine: Path = racine or cfg.chemin_bibliotheques
        self._racine.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, dict[str, Any]] = {}

    # --- Chargement ------------------------------------------------------

    def _load(self, langue: str) -> dict[str, Any]:
        if langue in self._cache:
            return self._cache[langue]
        lang_dir = self._racine / langue
        target = lang_dir / LIBRARY_FILENAME
        if safe_within(target, self._racine) is None:
            raise ValueError(f"Langue invalide : {langue!r}")
        if not target.exists():
            self._log.warning(
                f"Bibliothèque absente pour {langue} — {target}. "
                f"Utilisez les formulations par défaut ou seedez le fichier."
            )
            self._cache[langue] = {"langue": langue, "version": "absent",
                                   "valide_par": "", "formulations": {}}
            return self._cache[langue]
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Bibliothèque {target} mal formée : {exc}") from exc
        self._cache[langue] = data
        return data

    def reload(self) -> None:
        self._cache.clear()

    # --- API -------------------------------------------------------------

    def info(self, langue: str) -> LibraryInfo:
        data = self._load(langue)
        return LibraryInfo(
            langue=data.get("langue", langue),
            version=data.get("version", ""),
            valide_par=data.get("valide_par", ""),
            criteres=sorted(data.get("formulations", {}).keys()),
        )

    def phrases(self, critere: str, niveau: int | str, langue: str) -> list[str]:
        """Retourne les variantes pour (critère, niveau). Vide si inconnu.

        Accepte `niveau` int (1-5) ou str ("1".."5"). Pas de fallback
        silencieux sur un niveau voisin : si la lib ne contient pas le
        niveau demandé, on renvoie [] et c'est à l'appelant de gérer.
        """
        lv = str(int(niveau)) if isinstance(niveau, int) else str(niveau)
        if lv not in VALID_LEVELS:
            raise ValueError(f"Niveau attendu 1-5, reçu {niveau!r}")
        data = self._load(langue)
        block = data.get("formulations", {}).get(critere, {})
        variants = block.get(lv, [])
        if not isinstance(variants, list):
            return []
        return [str(v) for v in variants if isinstance(v, str) and v.strip()]

    def pick(
        self,
        critere: str,
        niveau: int | str,
        langue: str,
        *,
        prefer_index: int = 0,
    ) -> str:
        """Renvoie une variante stable (par défaut la première).

        Déterministe par défaut pour garantir la reproductibilité d'un
        certificat à input identique. L'appelant peut varier l'index
        pour éviter les répétitions dans un même document.
        """
        variants = self.phrases(critere, niveau, langue)
        if not variants:
            return ""
        return variants[prefer_index % len(variants)]

    def critere_known(self, critere: str, langue: str) -> bool:
        data = self._load(langue)
        return critere in data.get("formulations", {})
