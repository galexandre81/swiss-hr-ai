from __future__ import annotations

import json

from _app.core.blacklist_detector import BlacklistDetector


def _seed(sandbox, regles):
    (sandbox / "Bibliotheques" / "fr" / "blacklist.json").write_text(
        json.dumps({"version": "t", "langue": "fr", "regles": regles}),
        encoding="utf-8",
    )


def test_detects_coded_effort_expression(sandbox):
    _seed(sandbox, [{
        "id": "fr_code_efforce",
        "severite": "bloquant",
        "type": "regex",
        "pattern": r"s['\u2019]est efforc[ée]e? de",
        "raison": "Effort sans résultat.",
        "suggestion": "Remplacer.",
    }])
    det = BlacklistDetector()
    text = "Il s'est efforcé de remplir ses tâches."
    hits = det.scan(text, "fr")
    assert len(hits) == 1
    assert hits[0].severite == "bloquant"
    assert det.has_bloquant(hits)


def test_no_false_positive(sandbox):
    _seed(sandbox, [{
        "id": "any", "severite": "alerte", "type": "regex",
        "pattern": r"codé", "raison": "x", "suggestion": "y",
    }])
    det = BlacklistDetector()
    assert det.scan("Texte parfaitement neutre.", "fr") == []


def test_substring_pattern(sandbox):
    _seed(sandbox, [{
        "id": "subst", "severite": "alerte", "type": "substring",
        "pattern": "bonne chance", "raison": "x", "suggestion": "y",
    }])
    det = BlacklistDetector()
    hits = det.scan("Nous lui souhaitons bonne chance.", "fr")
    assert len(hits) == 1


def test_absent_blacklist_returns_empty(sandbox):
    det = BlacklistDetector()
    assert det.scan("texte", "fr") == []


def test_invalid_regex_is_skipped(sandbox):
    _seed(sandbox, [
        {"id": "bad", "severite": "alerte", "type": "regex", "pattern": "(([", "raison": "x", "suggestion": "y"},
        {"id": "good", "severite": "alerte", "type": "regex", "pattern": "toto", "raison": "x", "suggestion": "y"},
    ])
    det = BlacklistDetector()
    hits = det.scan("toto toto", "fr")
    assert len(hits) == 1
    assert hits[0].regle_id == "good"


def test_dedupes_per_rule(sandbox):
    _seed(sandbox, [{
        "id": "one", "severite": "alerte", "type": "regex",
        "pattern": "abc", "raison": "x", "suggestion": "y",
    }])
    det = BlacklistDetector()
    hits = det.scan("abc and abc and abc", "fr")
    assert len(hits) == 1
