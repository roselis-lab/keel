from keel.schemas.threat import Threat
from keel.catalog import lint_threat


def _threat(**over):
    base = dict(
        id="T-X", title="Sensitive data disclosure", harm="data-exposed",
        weaknesses=[{"component": "tool", "text": "returns raw records with no scoping"}],
        reachability="NOT applicable if the model sees no secrets",
        mitigations=[{"id": "CTRL-DLP", "strength": "soft", "rationale": "lowers likelihood"}],
    )
    base.update(over)
    return Threat(**base)


def test_lint_flags_all_soft():
    msgs = lint_threat(_threat())
    assert any("no `gating` mitigation" in m for m in msgs)


def test_lint_flags_technique_title():
    msgs = lint_threat(_threat(title="Prompt injection"))
    assert any("technique" in m for m in msgs)


def test_lint_clean_threat_has_no_advice():
    t = _threat(mitigations=[{"id": "CTRL-DLP", "strength": "gating", "rationale": "blocks"}])
    assert lint_threat(t) == []
