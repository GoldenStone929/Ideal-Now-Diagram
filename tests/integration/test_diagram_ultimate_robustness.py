"""Robustness suite for arbitrary-context logical division."""

from __future__ import annotations

import random
import string
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from diagram_autogen.pipeline import generate_diagram_payload


def _assert_logical_payload(payload: dict) -> None:
    assert payload["nodes"], "nodes should not be empty"
    assert payload["edges"], "edges should not be empty"
    assert payload["meta"]["section_count"] >= 3
    assert payload["meta"]["quality_score"] >= 1.8

    node_ids = {node["id"] for node in payload["nodes"]}
    for edge in payload["edges"]:
        assert edge["from"] in node_ids
        assert edge["to"] in node_ids

    labels = [node["label"] for node in payload["nodes"] if node["id"].startswith("S")]
    assert len(labels) == len(set(labels)), "section labels should be unique"


@pytest.mark.parametrize(
    "text",
    [
        # Chinese narrative
        "小明先收集需求，然后整理规则。因为上线时间紧，所以团队先做核心流程，再补充验证和文档，最后发布并复盘。",
        # Mixed zh/en operational note
        "先做 intake and clarification, then retrieval. 因为依赖规则库，所以 validation 在 generation 后进行，最后 human review.",
        # No punctuation long plain text
        " ".join([f"token{i}" for i in range(900)]),
        # Bullet-heavy context
        "- define scope\n- collect data\n- build model\n- validate outputs\n- ship release\n- capture lessons learned",
        # Code-like context
        "def ingest(): pass\n\ndef transform(): pass\n\ndef validate(): pass\n# pipeline: ingest -> transform -> validate -> export",
        # Log-like context
        "09:01 start job | 09:02 download data | 09:08 parse error | 09:10 retry success | 09:15 run checks | 09:20 publish",
        # Email-like context
        "Hi team, first we finalize assumptions, then draft outputs, compare against baseline, validate checks, and submit for review.",
        # Story-like context
        "Ana found clues in the archive, asked Ben to decode notes, then both mapped routes and restored the old station garden.",
    ],
)
def test_divides_diverse_contexts_logically(text: str):
    payload = generate_diagram_payload(text, mode="local", allow_llm=False, llm_attempts=0)
    _assert_logical_payload(payload)


def _fuzz_context(seed: int) -> str:
    random.seed(seed)
    themes = [
        "planning",
        "incident",
        "story",
        "clinical coding",
        "migration",
        "release",
        "analysis",
        "validation",
    ]
    connectors = ["because", "then", "after", "finally", "depends on", "requires", "therefore"]
    units = []
    for i in range(random.randint(4, 9)):
        theme = random.choice(themes)
        connector = random.choice(connectors)
        noise = "".join(random.choices(string.ascii_lowercase, k=random.randint(8, 18)))
        units.append(
            f"step {i+1} handles {theme} {connector} previous outputs and tracks {noise} for follow-up"
        )
    return ". ".join(units) + "."


def test_bulk_fuzz_contexts_non_empty_and_logical():
    total = 300
    success = 0
    cross_positive = 0

    for i in range(total):
        payload = generate_diagram_payload(_fuzz_context(i), mode="local", allow_llm=False, llm_attempts=0)
        try:
            _assert_logical_payload(payload)
        except AssertionError:
            continue
        success += 1
        cross_positive += int(payload["meta"]["cross_link_count"] > 0)

    # Ultimate robustness target for fallback-only path.
    assert success == total
    # Most fuzz contexts contain dependency cues; cross links should appear in majority.
    assert cross_positive >= int(total * 0.65)
