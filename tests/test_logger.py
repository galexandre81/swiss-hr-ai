from __future__ import annotations

import json

from _app.core.logger import Logger


def _read_audit(sandbox):
    logs = sorted(sandbox.glob("Logs/audit_*.jsonl"))
    assert logs, "Aucun fichier d'audit produit"
    with logs[0].open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def test_audit_llm_call_fingerprint_only(sandbox):
    log = Logger()
    log.audit_llm_call(
        module="certificats",
        entity="entite_demo",
        temperature=0.3,
        duration_ms=1234,
        status="ok",
        prompt="Bonjour",
        response="Bien reçu",
    )
    [rec] = _read_audit(sandbox)
    assert rec["event"] == "llm_call"
    assert rec["module"] == "certificats"
    assert rec["duration_ms"] == 1234
    assert set(rec["prompt"]) == {"sha256_16", "length"}
    assert rec["prompt"]["length"] == len("Bonjour")
    assert "prompt_full" not in rec
    assert "response_full" not in rec


def test_audit_llm_call_full_content(sandbox):
    # Active le mode full-logging via config.json puis reset caches.
    cfg = sandbox / "config.json"
    data = json.loads(cfg.read_text(encoding="utf-8"))
    data["audit_log_prompts"] = True
    cfg.write_text(json.dumps(data), encoding="utf-8")

    from _app.core import config as cfg_mod
    from _app.core import logger as log_mod
    cfg_mod.reset_cache()
    log_mod.reset_cache()

    log = Logger()
    log.audit_llm_call(
        module="juridique",
        entity=None,
        temperature=0.1,
        duration_ms=50,
        status="ok",
        prompt="Question confidentielle",
        response="Réponse complète",
    )
    [rec] = _read_audit(sandbox)
    assert rec["prompt_full"] == "Question confidentielle"
    assert rec["response_full"] == "Réponse complète"
