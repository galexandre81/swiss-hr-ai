"""Détecteur déterministe de formulations codées / proscrites.

Garde-fou n°1 (cf. §8 et §19 de la spec certificats) : un LLM 9B
produit par défaut du langage codé RH suisse. On ne peut pas se reposer
uniquement sur le prompt pour l'éviter. On ajoute donc un **scanner
post-génération** qui signale ces tournures avec leur position et
sévérité.

Le scan est déterministe (regex ou match de sous-chaîne), sans LLM —
ainsi, un RH qui se demande pourquoi une alerte a sonné peut retrouver
la règle exacte dans `blacklist.json`.

Format fichier par langue :

    Bibliotheques/<langue>/blacklist.json
    {
      "version": "2026-04-22",
      "langue": "fr",
      "regles": [
        {
          "id": "code_fr_01",
          "severite": "bloquant" | "alerte",
          "pattern": "s'est efforcé(?:e)? de",
          "type": "regex",
          "raison": "Tournure d'effort sans résultat (niveau 2 codé).",
          "suggestion": "Préciser un résultat concret ou adopter une formulation factuelle."
        },
        ...
      ]
    }

Sévérités :
- `bloquant` → refus de finalisation tant que non résolu (ex: « s'est
  efforcé » seul).
- `alerte` → signalement au RH avec suggestion, non bloquant.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from _app.core.config import get_config
from _app.core.logger import get_logger
from _app.core.paths import safe_within

BLACKLIST_FILENAME = "blacklist.json"
SEVERITE_BLOQUANT = "bloquant"
SEVERITE_ALERTE = "alerte"
VALID_SEVERITES = frozenset({SEVERITE_BLOQUANT, SEVERITE_ALERTE})


@dataclass
class BlacklistHit:
    regle_id: str
    severite: str
    start: int
    end: int
    extrait: str
    raison: str
    suggestion: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "regle_id": self.regle_id,
            "severite": self.severite,
            "start": self.start,
            "end": self.end,
            "extrait": self.extrait,
            "raison": self.raison,
            "suggestion": self.suggestion,
        }


class BlacklistDetector:
    """Scanner déterministe par langue."""

    def __init__(self, racine: Path | None = None):
        cfg = get_config()
        self._log = get_logger()
        self._racine: Path = racine or cfg.chemin_bibliotheques
        self._racine.mkdir(parents=True, exist_ok=True)
        # Cache des règles compilées par langue
        self._compiled: dict[str, list[tuple[dict[str, Any], re.Pattern[str]]]] = {}

    # --- Chargement ------------------------------------------------------

    def _rules(self, langue: str) -> list[tuple[dict[str, Any], re.Pattern[str]]]:
        if langue in self._compiled:
            return self._compiled[langue]
        target = self._racine / langue / BLACKLIST_FILENAME
        if safe_within(target, self._racine) is None:
            raise ValueError(f"Langue invalide : {langue!r}")
        if not target.exists():
            self._log.warning(f"Blacklist absente pour {langue} — {target}")
            self._compiled[langue] = []
            return []
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Blacklist {target} mal formée : {exc}") from exc

        compiled: list[tuple[dict[str, Any], re.Pattern[str]]] = []
        for entry in data.get("regles", []):
            if not isinstance(entry, dict):
                continue
            raw = entry.get("pattern", "")
            kind = entry.get("type", "regex")
            severite = entry.get("severite", SEVERITE_ALERTE)
            if severite not in VALID_SEVERITES:
                self._log.warning(f"Sévérité inconnue ignorée : {severite!r}")
                continue
            if not raw:
                continue
            try:
                if kind == "regex":
                    pattern = re.compile(raw, re.IGNORECASE)
                else:
                    pattern = re.compile(re.escape(raw), re.IGNORECASE)
            except re.error as exc:
                self._log.warning(f"Pattern invalide ignoré : {raw!r} ({exc})")
                continue
            compiled.append((entry, pattern))
        self._compiled[langue] = compiled
        return compiled

    def reload(self) -> None:
        self._compiled.clear()

    # --- API -------------------------------------------------------------

    def scan(self, text: str, langue: str) -> list[BlacklistHit]:
        """Scanne `text` contre la blacklist de `langue`.

        Retourne la liste des matches dans l'ordre d'apparition.
        Dédoublonnage simple : pour une même règle, on ne garde que le
        premier match (évite de polluer le rapport RH avec 10 alertes
        identiques).
        """
        hits: list[BlacklistHit] = []
        seen: set[str] = set()
        for entry, pattern in self._rules(langue):
            rid = entry.get("id", "?")
            if rid in seen:
                continue
            m = pattern.search(text)
            if not m:
                continue
            seen.add(rid)
            extrait = text[max(0, m.start() - 20): m.end() + 20]
            hits.append(BlacklistHit(
                regle_id=rid,
                severite=entry.get("severite", SEVERITE_ALERTE),
                start=m.start(),
                end=m.end(),
                extrait=extrait,
                raison=entry.get("raison", ""),
                suggestion=entry.get("suggestion", ""),
            ))
        hits.sort(key=lambda h: h.start)
        return hits

    def has_bloquant(self, hits: list[BlacklistHit]) -> bool:
        return any(h.severite == SEVERITE_BLOQUANT for h in hits)
