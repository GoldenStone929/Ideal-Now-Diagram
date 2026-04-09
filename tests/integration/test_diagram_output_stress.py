"""Stress and mocked-provider tests for diagram output generation."""

from __future__ import annotations

import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from diagram_autogen import pipeline
from diagram_autogen.pipeline import ProviderResult, generate_diagram_payload


def _assert_payload_basic(payload: dict) -> None:
    assert isinstance(payload.get("nodes"), list) and payload["nodes"]
    assert isinstance(payload.get("edges"), list)
    assert "meta" in payload and isinstance(payload["meta"], dict)
    assert payload["meta"]["section_count"] >= 3
    assert payload["meta"]["quality_score"] > 0

    node_ids = {node["id"] for node in payload["nodes"]}
    assert node_ids
    for edge in payload["edges"]:
        assert edge["from"] in node_ids
        assert edge["to"] in node_ids


def _mock_outline(name_prefix: str, section_count: int = 5, *, short_labels: bool = False, low_quality: bool = False) -> dict:
    sections = []
    for i in range(section_count):
        label = f"{name_prefix}{i+1}" if short_labels else f"{name_prefix} Section {i+1}"
        summary = "x" if low_quality else f"{label} explains a major phase with concrete details."
        points = ["d"] if low_quality else [f"{label} detail {j}" for j in range(1, 5)]
        sections.append({"label": label, "summary": summary, "points": points})

    links = [] if low_quality else [{"from": i, "to": i + 1, "reason": "Sequential dependency."} for i in range(section_count - 1)]
    if not low_quality and section_count >= 5:
        links.append({"from": 0, "to": 3, "reason": "Cross dependency from planning to implementation."})
        links.append({"from": 1, "to": 4, "reason": "Design constraints influence release."})

    return {"title": f"{name_prefix} Outline", "sections": sections, "links": links}


def _build_stress_inputs(n: int = 36) -> list[str]:
    heads = [
        "clinical trial summary",
        "factory incident log",
        "children story about a map",
        "meeting minutes for platform migration",
        "bug triage record",
        "drug safety SOP notes",
    ]
    tails = [
        "identify risks and mitigation steps",
        "define owners and dependencies",
        "capture timeline and handoff checkpoints",
        "explain root causes and corrective actions",
        "group related tasks into sections",
        "highlight what depends on what",
    ]
    seeds = []
    for i in range(n):
        random.seed(i)
        h = random.choice(heads)
        t = random.choice(tails)
        seeds.append(
            (
                f"{h}. We need to break this down into workable chunks. "
                f"Please map key points, constraints, and transitions. "
                f"Then {t}. Finally summarize outputs for handoff."
            )
        )
    return seeds


@pytest.mark.parametrize("text", _build_stress_inputs(36))
def test_bulk_output_stability_without_provider(text: str):
    payload = generate_diagram_payload(text, mode="local", allow_llm=False, llm_attempts=0)
    _assert_payload_basic(payload)
    assert payload["meta"]["fallback_used"] is True
    assert payload["meta"]["strategy"] == "heuristic_fallback"


def test_mock_local_provider_consensus_pass(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DIAGRAM_CONSENSUS_SAMPLES", "3")
    monkeypatch.setenv("DIAGRAM_MIN_QUALITY", "2.35")

    outline_a = _mock_outline("Alpha", section_count=5)
    outline_b = _mock_outline("Beta", section_count=5)
    calls = {"n": 0}

    def fake_local(*args, **kwargs):
        idx = calls["n"]
        calls["n"] += 1
        if idx % 3 in (0, 1):
            return ProviderResult(ok=True, payload=outline_a, provider="local")
        return ProviderResult(ok=True, payload=outline_b, provider="local")

    monkeypatch.setattr(pipeline, "_call_local_provider", fake_local)

    payload = generate_diagram_payload(
        "A long context about architecture stages and dependencies.",
        mode="local",
        allow_llm=True,
        llm_attempts=1,
    )
    _assert_payload_basic(payload)
    assert payload["meta"]["fallback_used"] is False
    assert payload["meta"]["strategy"] == "local_provider_consensus"
    assert payload["meta"]["quality_gate_passed"] is True
    assert payload["meta"]["consensus_strength"] >= 0.66


def test_mock_external_provider_repair_then_pass(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DIAGRAM_CONSENSUS_SAMPLES", "2")
    monkeypatch.setenv("DIAGRAM_MIN_QUALITY", "2.8")

    low = _mock_outline("L", section_count=3, short_labels=True, low_quality=True)
    high = _mock_outline("High", section_count=6)

    def fake_external(*args, **kwargs):
        if kwargs.get("prompt_override"):
            return ProviderResult(ok=True, payload=high, provider="external")
        return ProviderResult(ok=True, payload=low, provider="external")

    monkeypatch.setattr(pipeline, "_call_external_provider", fake_external)

    payload = generate_diagram_payload(
        "External API mode test input for retry and repair gate.",
        mode="external",
        allow_llm=True,
        llm_attempts=1,
    )
    _assert_payload_basic(payload)
    assert payload["meta"]["fallback_used"] is False
    assert payload["meta"]["strategy"] == "external_provider_consensus"
    assert payload["meta"]["quality_gate_passed"] is True
    assert any(log["stage"] == "provider_repair" and log["ok"] for log in payload["meta"]["attempts"])


def test_mock_provider_total_failure_fallback(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DIAGRAM_CONSENSUS_SAMPLES", "3")
    monkeypatch.setenv("DIAGRAM_MIN_QUALITY", "2.35")

    def fake_local_fail(*args, **kwargs):
        return ProviderResult(ok=False, payload=None, provider="local", error="mock timeout")

    monkeypatch.setattr(pipeline, "_call_local_provider", fake_local_fail)

    payload = generate_diagram_payload(
        "Provider is down but output should still be generated.",
        mode="local",
        allow_llm=True,
        llm_attempts=2,
    )
    _assert_payload_basic(payload)
    assert payload["meta"]["fallback_used"] is True
    assert payload["meta"]["quality_gate_passed"] is False
    # 2 attempts * 3 samples each -> at least 6 failed sample logs
    failed_samples = [log for log in payload["meta"]["attempts"] if log["stage"] == "provider_sample" and not log["ok"]]
    assert len(failed_samples) >= 6
