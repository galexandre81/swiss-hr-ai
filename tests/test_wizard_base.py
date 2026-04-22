from __future__ import annotations

from typing import Any

from _app.core.module_base import ModuleContext
from _app.core.wizard_base import WizardModuleBase, WizardStep


class _DemoWizard(WizardModuleBase):
    id = "demo"
    nom = "Demo wizard"
    categorie = "test"

    def steps(self) -> list[WizardStep]:
        return [
            WizardStep(
                id="s1", label="Étape 1",
                inputs=[{"id": "name", "label": "Nom", "type": "text", "required": True}],
                required_fields=["name"],
            ),
            WizardStep(
                id="s2", label="Étape 2",
                inputs=[{"id": "color", "label": "Couleur", "type": "text"}],
                required_fields=[],
            ),
        ]

    def finalize(self, state, ctx):
        return {"texte": f"Bonjour {state['answers']['s1']['name']} !", "alertes": []}


def test_empty_state_and_first_step():
    w = _DemoWizard()
    s = w.ensure_state({})
    assert s["step"] == "s1"
    assert s["completed"] == []


def test_record_answers_advances_step():
    w = _DemoWizard()
    s = w.record_answers({}, "s1", {"name": "Alice"})
    assert s["answers"]["s1"]["name"] == "Alice"
    assert "s1" in s["completed"]
    assert s["step"] == "s2"


def test_validate_required_fields_missing():
    w = _DemoWizard()
    errors = w.validate_step("s1", {})
    assert errors
    assert "Nom" in errors[0]


def test_validate_required_fields_present():
    w = _DemoWizard()
    assert w.validate_step("s1", {"name": "Bob"}) == []


def test_unknown_step():
    w = _DemoWizard()
    assert w.validate_step("nope", {}) == ["Étape inconnue : 'nope'."]


def test_can_finalize_tracks_completion():
    w = _DemoWizard()
    ok, missing = w.can_finalize({})
    assert not ok and len(missing) == 2
    state = w.record_answers({}, "s1", {"name": "A"})
    state = w.record_answers(state, "s2", {"color": "red"})
    ok, missing = w.can_finalize(state)
    assert ok
    assert missing == []


def test_run_is_blocked_on_wizard():
    w = _DemoWizard()
    ctx = ModuleContext(llm=None, entity=None, logger=None)
    import pytest
    with pytest.raises(RuntimeError):
        w.run({}, ctx)


def test_inputs_schema_is_flat():
    w = _DemoWizard()
    flat = w.inputs_schema()
    assert {f["id"] for f in flat} == {"name", "color"}
    assert all("_step" in f for f in flat)
