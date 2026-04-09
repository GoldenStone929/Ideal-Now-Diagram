"""Unit tests for auto diagram generation pipeline."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from diagram_autogen import chunk_text, generate_diagram_payload, get_generation_test_cases


def test_chunk_text_splits_long_context():
    text = " ".join([f"token{i}" for i in range(1200)])
    chunks = chunk_text(text, max_words=120, overlap_words=20)
    assert len(chunks) >= 8
    assert all(chunk.strip() for chunk in chunks)


def test_generate_diagram_for_random_text_fallback():
    text = (
        "Buy milk before 8pm. ETL pipeline broke because schema version changed. "
        "Need to align dashboard labels and call vendor support. "
        "Also remember to update the SOP and QA checklist this week."
    )
    payload = generate_diagram_payload(text, mode="local", allow_llm=False, llm_attempts=0)

    assert "nodes" in payload and payload["nodes"]
    assert "edges" in payload and payload["edges"]
    assert payload["meta"]["fallback_used"] is True
    assert payload["meta"]["quality_gate_passed"] is False
    assert payload["meta"]["quality_score"] > 0
    assert isinstance(payload.get("logic_steps_text"), str) and payload["logic_steps_text"].strip()
    node_ids = {node["id"] for node in payload["nodes"]}
    assert all(edge["from"] in node_ids and edge["to"] in node_ids for edge in payload["edges"])


def test_generate_diagram_for_story_context():
    text = (
        "Lina found a map in the attic. She asked Jay to decode the symbols. "
        "They visited the old station, solved a clue in the archive room, "
        "and organized volunteers to restore the hidden garden."
    )
    payload = generate_diagram_payload(text, mode="local", allow_llm=False, llm_attempts=0)

    assert len(payload["nodes"]) >= 5
    assert any(node["kind"] == "output" for node in payload["nodes"])
    assert payload["meta"]["section_count"] >= 3
    assert "cross_link_count" in payload["meta"]
    assert "consensus_strength" in payload["meta"]
    assert isinstance(payload.get("logic_steps_text"), str) and payload["logic_steps_text"].strip()


def test_generation_test_cases_include_story_and_random():
    cases = get_generation_test_cases()
    ids = {case["id"] for case in cases}
    assert "short_story" in ids
    assert "random_mix" in ids
