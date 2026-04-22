from __future__ import annotations

from _app.core.audit_trail import AuditTrail, sha256_of
from _app.core.dossier_store import DossierStore


def test_trail_appends_events_and_seals(sandbox):
    store = DossierStore()
    d = store.create(nom="Blanc", prenom="Sophie")

    trail = AuditTrail(d.racine, filename="trace_test.jsonl")
    trail.record_decision("absences_longues", "oui", justification="absence maternité 6 mois")
    trail.record_alert("code_01", "tournure codée détectée", resolution="remplacée par neutre")
    trail.record_draft(version=1, texte="Hello draft")
    seal = trail.seal("Final text.", outputs=["certificat.txt"])

    events = trail.events()
    kinds = [e["kind"] for e in events]
    assert "trail_opened" in kinds
    assert "zone_grise_decision" in kinds
    assert "alerte" in kinds
    assert "brouillon" in kinds
    assert "seal" in kinds
    assert seal["sha256"] == sha256_of("Final text.")


def test_trail_is_append_only(sandbox):
    store = DossierStore()
    d = store.create(nom="Noir", prenom="Jean")
    trail1 = AuditTrail(d.racine, filename="trace_append.jsonl")
    trail1.append("event_a", i=1)
    trail2 = AuditTrail(d.racine, filename="trace_append.jsonl")  # même fichier
    trail2.append("event_b", i=2)

    events = trail2.events()
    kinds = [e["kind"] for e in events]
    # L'ordre est préservé et rien n'a été écrasé.
    assert kinds.count("event_a") == 1
    assert kinds.count("event_b") == 1
    assert kinds.index("event_a") < kinds.index("event_b")


def test_export_consolidated(sandbox):
    store = DossierStore()
    d = store.create(nom="Roux", prenom="Aurélie")
    trail = AuditTrail(d.racine)
    trail.append("demo")
    export = trail.export_consolidated()
    assert "events" in export
    assert "exported_at" in export
    assert export["events"]
