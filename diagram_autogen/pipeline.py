"""Text-to-diagram generation pipeline with local/external LLM modes."""

from __future__ import annotations

import json
import os
import re
import textwrap
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Literal
from urllib import error, request


Mode = Literal["local", "external"]

_STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "have",
    "there",
    "were",
    "they",
    "them",
    "their",
    "about",
    "will",
    "what",
    "into",
    "been",
    "also",
    "than",
    "then",
    "your",
    "you",
    "our",
    "not",
    "are",
    "was",
    "can",
    "should",
    "would",
    "could",
    "when",
    "where",
    "how",
    "why",
    "all",
    "out",
    "use",
    "using",
    "local",
    "external",
    "api",
    "step",
    "steps",
    "handles",
    "handle",
    "previous",
    "outputs",
    "output",
    "follow",
    "followup",
    "context",
    "phase",
    "stages",
    "stage",
}

_STOPWORDS_ZH = {
    "我们",
    "你们",
    "他们",
    "这个",
    "那个",
    "这些",
    "那些",
    "以及",
    "然后",
    "因为",
    "所以",
    "需要",
    "进行",
    "已经",
    "如果",
    "可以",
    "一个",
    "一些",
    "还有",
    "并且",
    "对于",
    "通过",
    "为了",
    "但是",
    "不是",
    "没有",
    "并",
    "和",
    "或",
    "及",
    "在",
    "将",
    "把",
    "是",
    "了",
}

_TRANSITION_HINTS = {
    "because": "Dependency driven by rationale in context.",
    "therefore": "Downstream result inferred from upstream section.",
    "so that": "Goal-driven dependency in source context.",
    "then": "Sequential transition described in source context.",
    "after": "Temporal sequence from source context.",
    "before": "Temporal ordering from source context.",
    "finally": "Final stage relationship from source context.",
    "depends on": "Explicit dependency phrase found in source context.",
    "requires": "Prerequisite relationship identified in source context.",
}


OUTLINE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "summary": {"type": "string"},
                    "points": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["label", "summary", "points"],
                "additionalProperties": False,
            },
        },
        "links": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "from": {"type": "integer"},
                    "to": {"type": "integer"},
                    "reason": {"type": "string"},
                },
                "required": ["from", "to", "reason"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["title", "sections", "links"],
    "additionalProperties": False,
}


@dataclass
class ProviderResult:
    """Provider call result."""

    ok: bool
    payload: dict[str, Any] | None
    provider: str
    error: str = ""


def _normalize_text(text: str) -> str:
    lines = [ln.rstrip() for ln in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    cleaned = "\n".join(lines).strip()
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned


def _split_sentences(text: str) -> list[str]:
    sentence_like = re.split(r"(?<=[.!?。！？])\s+", text)
    sentence_like = [item.strip() for item in sentence_like if item.strip()]
    if sentence_like:
        return sentence_like
    return [text.strip()] if text.strip() else []


def chunk_text(text: str, max_words: int = 180, overlap_words: int = 28) -> list[str]:
    """Chunk long input while keeping local coherence."""
    normalized = _normalize_text(text)
    if not normalized:
        return []

    paragraphs = [p.strip() for p in normalized.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [normalized]

    chunks: list[list[str]] = []
    current_words: list[str] = []

    for paragraph in paragraphs:
        paragraph_words = paragraph.split()
        if len(paragraph_words) > max_words:
            # Extremely long plain text without clear sentence punctuation:
            # split directly by a sliding word window.
            if not re.search(r"[.!?。！？]", paragraph):
                if current_words:
                    chunks.append(current_words)
                    current_words = []
                stride = max(1, max_words - overlap_words)
                pos = 0
                while pos < len(paragraph_words):
                    window = paragraph_words[pos : pos + max_words]
                    if not window:
                        break
                    chunks.append(window)
                    if pos + max_words >= len(paragraph_words):
                        break
                    pos += stride
                continue

            for sent in _split_sentences(paragraph):
                sent_words = sent.split()
                if not sent_words:
                    continue
                if len(current_words) + len(sent_words) > max_words and current_words:
                    chunks.append(current_words)
                    overlap = current_words[-overlap_words:] if overlap_words > 0 else []
                    current_words = overlap.copy()
                current_words.extend(sent_words)
            continue

        if len(current_words) + len(paragraph_words) > max_words and current_words:
            chunks.append(current_words)
            overlap = current_words[-overlap_words:] if overlap_words > 0 else []
            current_words = overlap.copy()
        current_words.extend(paragraph_words)

    if current_words:
        chunks.append(current_words)

    out = [" ".join(words).strip() for words in chunks if words]
    return out


def _top_keywords(text: str, max_items: int = 6) -> list[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", text.lower())
    filtered = [t for t in tokens if t not in _STOPWORDS and not t.isdigit()]
    zh_tokens = re.findall(r"[\u4e00-\u9fff]{2,12}", text)
    filtered_zh = [t for t in zh_tokens if t not in _STOPWORDS_ZH and len(t.strip()) >= 2]
    filtered.extend(filtered_zh)
    if not filtered:
        return []
    common = Counter(filtered).most_common(max_items)
    return [k for k, _ in common]


def _clean_label(label: str, fallback: str) -> str:
    value = re.sub(r"[\[\]{}()*_`]", " ", label).strip(" -:;,.")
    value = re.sub(r"\s+", " ", value).strip()
    if not value:
        value = fallback
    if len(value) > 28:
        value = value[:28].rsplit(" ", 1)[0].strip() or value[:28]
    return value


def _extract_heading_sections(text: str) -> list[dict[str, Any]]:
    lines = text.split("\n")
    heading_indices: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        striped = line.strip()
        if not striped:
            continue
        if re.match(r"^(#+\s+|[0-9]+[.)]\s+|[A-Z][A-Z0-9 _-]{5,}$)", striped):
            heading_indices.append((i, striped.lstrip("#").strip()))

    if len(heading_indices) < 2:
        return []

    sections: list[dict[str, Any]] = []
    for idx, (start, heading) in enumerate(heading_indices):
        end = heading_indices[idx + 1][0] if idx + 1 < len(heading_indices) else len(lines)
        block = "\n".join(lines[start + 1 : end]).strip()
        if not block:
            continue
        sentences = _split_sentences(block)
        summary = sentences[0] if sentences else block
        points: list[str] = []
        for ln in block.split("\n"):
            s = ln.strip()
            if re.match(r"^[-*•]\s+", s):
                points.append(re.sub(r"^[-*•]\s+", "", s))
        if not points:
            points = _top_keywords(block, max_items=4)
        sections.append(
            {
                "label": _clean_label(heading, f"Section {len(sections) + 1}"),
                "summary": summary[:180],
                "points": points[:5],
            }
        )
    return sections


def _title_from_keywords(keywords: list[str], fallback: str) -> str:
    if not keywords:
        return fallback
    top = keywords[:2]
    label = " / ".join(top)
    label = label.title() if re.search(r"[A-Za-z]", label) else label
    return _clean_label(label, fallback)


def _extract_list_points(text: str, limit: int = 6) -> list[str]:
    points: list[str] = []
    for ln in text.split("\n"):
        s = ln.strip()
        if re.match(r"^[-*•]\s+", s):
            points.append(re.sub(r"^[-*•]\s+", "", s).strip())
        elif re.match(r"^[0-9]{1,2}[.)]\s+", s):
            points.append(re.sub(r"^[0-9]{1,2}[.)]\s+", "", s).strip())
        if len(points) >= limit:
            break
    return [p for p in points if p]


def _merge_adjacent_groups(groups: list[dict[str, Any]], target_count: int) -> list[dict[str, Any]]:
    merged = groups.copy()
    if target_count < 1:
        target_count = 1
    while len(merged) > target_count:
        merged[0]["chunks"].extend(merged[1]["chunks"])
        merged[0]["text"] += " " + merged[1]["text"]
        merged.pop(1)
    return merged


def _sentence_group_texts(text: str, max_groups: int = 8) -> list[str]:
    sentences = _split_sentences(text)
    if len(sentences) < 4:
        return [text]

    groups: list[list[str]] = []
    current: list[str] = []
    current_keywords: set[str] = set()

    for sentence in sentences:
        sent_keywords = set(_top_keywords(sentence, max_items=8))
        lowered = sentence.lower()
        transition_hit = any(hint in lowered for hint in _TRANSITION_HINTS)

        if current:
            overlap = len(current_keywords.intersection(sent_keywords))
            if (len(current) >= 2 and overlap == 0) or transition_hit:
                groups.append(current.copy())
                current = [sentence]
                current_keywords = set(sent_keywords)
                continue

        current.append(sentence)
        current_keywords = current_keywords.union(sent_keywords)

    if current:
        groups.append(current)

    if len(groups) == 1 and len(sentences) >= 6:
        window = max(2, min(3, len(sentences) // 3))
        groups = [sentences[i : i + window] for i in range(0, len(sentences), window)]

    text_groups = [" ".join(group).strip() for group in groups if group]
    if len(text_groups) > max_groups:
        text_groups = text_groups[:max_groups]
    return text_groups or [text]


def _semantic_groups_from_chunks(chunks: list[str], max_groups: int = 8) -> list[dict[str, Any]]:
    if len(chunks) == 1:
        chunks = _sentence_group_texts(chunks[0], max_groups=max_groups)

    groups: list[dict[str, Any]] = []
    for chunk in chunks:
        kws = set(_top_keywords(chunk, max_items=10))
        if not groups:
            groups.append({"text": chunk, "chunks": [chunk], "keywords": kws})
            continue
        prev = groups[-1]
        overlap = len(prev["keywords"].intersection(kws))
        denom = max(min(len(prev["keywords"]), len(kws)), 1)
        overlap_ratio = overlap / denom
        transition_hit = any(hint in chunk.lower() for hint in _TRANSITION_HINTS)
        if overlap >= 2 and overlap_ratio >= 0.4 and not transition_hit:
            prev["text"] += " " + chunk
            prev["chunks"].append(chunk)
            prev["keywords"] = set(_top_keywords(prev["text"], max_items=12))
        else:
            groups.append({"text": chunk, "chunks": [chunk], "keywords": kws})
    if len(groups) > max_groups:
        groups = _merge_adjacent_groups(groups, max_groups)
        for group in groups:
            group["keywords"] = set(_top_keywords(group["text"], max_items=12))
    return groups


def _ensure_unique_labels(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: Counter[str] = Counter()
    out: list[dict[str, Any]] = []
    for sec in sections:
        label = _clean_label(str(sec.get("label", "")), "Section")
        key = label.lower()
        seen[key] += 1
        if seen[key] > 1:
            label = f"{label} {seen[key]}"
        patched = dict(sec)
        patched["label"] = label
        out.append(patched)
    return out


def _heuristic_outline(text: str, chunks: list[str]) -> dict[str, Any]:
    sections = _extract_heading_sections(text)
    if not sections:
        sections = []
        groups = _semantic_groups_from_chunks(chunks[:12], max_groups=8)
        for idx, group in enumerate(groups, start=1):
            group_text = group["text"]
            sentences = _split_sentences(group_text)
            summary = (sentences[0] if sentences else group_text)[:180]
            keywords = _top_keywords(group_text, max_items=6)
            label = _title_from_keywords(keywords, fallback=f"Section {idx}")
            list_points = _extract_list_points(group_text, limit=4)
            points = list_points or keywords[:5] or [f"group_{idx}_detail"]
            sections.append({"label": label, "summary": summary, "points": points[:6]})

    if len(sections) < 3:
        while len(sections) < 3:
            n = len(sections) + 1
            sections.append(
                {
                    "label": f"Section {n}",
                    "summary": f"Auto-generated section {n} from context.",
                    "points": [f"context_{n}", "auto_outline"],
                }
            )

    sections = _ensure_unique_labels(sections[:10])
    links: list[dict[str, Any]] = []
    for i in range(len(sections) - 1):
        links.append({"from": i, "to": i + 1, "reason": "Sequential flow from previous section."})

    # Add lightweight cross-links via keyword overlap.
    section_keywords = [_top_keywords(f"{sec['label']} {sec['summary']} {' '.join(sec['points'])}") for sec in sections]
    for i in range(len(sections)):
        for j in range(i + 2, len(sections)):
            overlap = set(section_keywords[i]).intersection(section_keywords[j])
            if len(overlap) >= 2:
                links.append(
                    {
                        "from": i,
                        "to": j,
                        "reason": f"Shared concepts: {', '.join(sorted(overlap)[:3])}.",
                    }
                )
            if len(links) >= len(sections) + 4:
                break
        if len(links) >= len(sections) + 4:
            break

    return {"title": "Auto Diagram", "sections": sections[:10], "links": links}


def _outline_quality(outline: dict[str, Any]) -> float:
    sections = outline.get("sections") or []
    links = outline.get("links") or []
    if not isinstance(sections, list) or not sections:
        return 0.0
    score = 0.0
    score += min(len(sections), 8) / 8.0
    score += min(len(links), len(sections)) / max(len(sections), 1)
    long_labels = sum(1 for s in sections if isinstance(s.get("label"), str) and len(s["label"]) >= 4)
    score += long_labels / max(len(sections), 1)
    return score


def _normalize_outline(outline: dict[str, Any] | None) -> dict[str, Any]:
    base = {"title": "Auto Diagram", "sections": [], "links": []}
    if not isinstance(outline, dict):
        return base

    normalized = {"title": str(outline.get("title", "Auto Diagram")).strip() or "Auto Diagram", "sections": [], "links": []}

    sections = outline.get("sections")
    if isinstance(sections, list):
        for idx, section in enumerate(sections[:10], start=1):
            if not isinstance(section, dict):
                continue
            label = _clean_label(str(section.get("label", "")).strip(), f"Section {idx}")
            summary = str(section.get("summary", "")).strip()[:220]
            points_raw = section.get("points")
            points: list[str] = []
            if isinstance(points_raw, list):
                points = [str(item).strip() for item in points_raw if str(item).strip()]
            if not points:
                points = _top_keywords(f"{label} {summary}", max_items=4)
            normalized["sections"].append(
                {
                    "label": label,
                    "summary": summary or f"Generated summary for {label}.",
                    "points": points[:6] if points else [f"{label.lower().replace(' ', '_')}_detail"],
                }
            )

    if len(normalized["sections"]) < 3:
        while len(normalized["sections"]) < 3:
            n = len(normalized["sections"]) + 1
            normalized["sections"].append(
                {"label": f"Section {n}", "summary": f"Auto-generated section {n}.", "points": [f"context_{n}", "auto_outline"]}
            )
    normalized["sections"] = _ensure_unique_labels(normalized["sections"][:10])

    links = outline.get("links")
    if isinstance(links, list):
        for link in links:
            if not isinstance(link, dict):
                continue
            try:
                src = int(link.get("from", -1))
                dst = int(link.get("to", -1))
            except (TypeError, ValueError):
                continue
            reason = str(link.get("reason", "")).strip()[:240]
            normalized["links"].append({"from": src, "to": dst, "reason": reason or "Dependency inferred from context."})

    return normalized


def _outline_signature(outline: dict[str, Any]) -> tuple[str, ...]:
    labels: list[str] = []
    for section in outline.get("sections", []):
        if not isinstance(section, dict):
            continue
        label = _clean_label(str(section.get("label", "")), "section").lower()
        labels.append(re.sub(r"[^a-z0-9]+", "", label)[:18] or "section")
    if not labels:
        return ("empty",)
    return tuple(labels[:10])


def _ensure_sequential_links(links: list[dict[str, Any]], section_count: int) -> list[dict[str, Any]]:
    existing = {(int(link["from"]), int(link["to"])) for link in links if "from" in link and "to" in link}
    out = links.copy()
    for idx in range(max(section_count - 1, 0)):
        key = (idx, idx + 1)
        if key in existing:
            continue
        out.append({"from": idx, "to": idx + 1, "reason": "Sequential storyline inferred from section ordering."})
    return out


def _dedupe_links(links: list[dict[str, Any]], section_count: int, max_links: int) -> list[dict[str, Any]]:
    bucket: dict[tuple[int, int], dict[str, Any]] = {}
    for link in links:
        try:
            src = int(link.get("from", -1))
            dst = int(link.get("to", -1))
        except (TypeError, ValueError):
            continue
        if src == dst:
            continue
        if src < 0 or dst < 0 or src >= section_count or dst >= section_count:
            continue
        reason = str(link.get("reason", "")).strip()[:240] or "Dependency inferred from context."
        key = (src, dst)
        if key not in bucket or len(reason) > len(bucket[key]["reason"]):
            bucket[key] = {"from": src, "to": dst, "reason": reason}

    items = sorted(bucket.values(), key=lambda item: (item["from"], item["to"]))
    seq = [item for item in items if item["to"] == item["from"] + 1]
    cross = [item for item in items if item["to"] != item["from"] + 1]
    merged = seq + cross
    return merged[:max_links]


def _enrich_outline_dependencies(outline: dict[str, Any], chunks: list[str]) -> dict[str, Any]:
    enriched = _normalize_outline(outline)
    section_count = len(enriched["sections"])
    if section_count <= 1:
        return enriched

    section_keywords: list[set[str]] = []
    for section in enriched["sections"]:
        text = f"{section['label']} {section['summary']} {' '.join(section['points'])}"
        section_keywords.append(set(_top_keywords(text, max_items=10)))

    pair_votes: Counter[tuple[int, int]] = Counter()
    pair_reasons: dict[tuple[int, int], str] = {}

    for chunk in chunks:
        kws = set(_top_keywords(chunk, max_items=14))
        if not kws:
            continue
        scores: list[tuple[int, int]] = []
        for idx, sec_kws in enumerate(section_keywords):
            overlap = len(kws.intersection(sec_kws))
            if overlap > 0:
                scores.append((overlap, idx))
        scores.sort(key=lambda item: item[0], reverse=True)
        top_sections = [idx for overlap, idx in scores[:3] if overlap > 0]

        for left in range(len(top_sections)):
            for right in range(left + 1, len(top_sections)):
                src = min(top_sections[left], top_sections[right])
                dst = max(top_sections[left], top_sections[right])
                if src == dst:
                    continue
                pair_votes[(src, dst)] += 1

        lowered = chunk.lower()
        for hint, reason in _TRANSITION_HINTS.items():
            if hint in lowered and len(top_sections) >= 2:
                src = min(top_sections[0], top_sections[1])
                dst = max(top_sections[0], top_sections[1])
                if src == dst:
                    continue
                pair_votes[(src, dst)] += 2
                pair_reasons[(src, dst)] = reason

    links = list(enriched.get("links", []))
    links = _ensure_sequential_links(links, section_count)
    for (src, dst), votes in pair_votes.most_common():
        if votes < 2:
            continue
        if dst == src + 1:
            continue
        reason = pair_reasons.get((src, dst), f"Sections co-mentioned across chunks ({votes} evidence hits).")
        links.append({"from": src, "to": dst, "reason": reason})
        if len(links) >= section_count + 8:
            break

    # Global cue-based cross links (helps short contexts with explicit dependency words).
    joined = " ".join(chunks).lower()
    cue_hits = [cue for cue in _TRANSITION_HINTS if cue in joined]
    if section_count >= 3 and cue_hits:
        primary_cue = cue_hits[0]
        links.append(
            {
                "from": 0,
                "to": min(2, section_count - 1),
                "reason": f"Global dependency cue detected: '{primary_cue}'.",
            }
        )
    if section_count >= 4 and ("therefore" in joined or "so that" in joined):
        links.append(
            {
                "from": 1,
                "to": section_count - 1,
                "reason": "Global causality cue suggests non-linear dependency to final section.",
            }
        )

    enriched["links"] = _dedupe_links(links, section_count=section_count, max_links=section_count + 8)
    return enriched


def _quality_report(outline: dict[str, Any]) -> dict[str, float | int]:
    normalized = _normalize_outline(outline)
    sections = normalized.get("sections", [])
    links = normalized.get("links", [])
    sec_count = len(sections)
    if sec_count == 0:
        return {"score": 0.0, "section_count": 0, "edge_count": 0, "cross_link_count": 0, "avg_points": 0.0}

    base = _outline_quality(normalized)
    avg_points = sum(min(len(section.get("points", [])), 4) / 4.0 for section in sections) / sec_count
    cross_links = sum(1 for link in links if abs(int(link.get("to", -1)) - int(link.get("from", -1))) > 1)
    cross_score = min(cross_links, max(1, sec_count // 2)) / max(1, sec_count // 2)
    link_density = min(len(links), sec_count + 2) / max(1, sec_count + 2)
    score = round(base + avg_points + cross_score + link_density, 4)
    return {
        "score": score,
        "section_count": sec_count,
        "edge_count": len(links),
        "cross_link_count": cross_links,
        "avg_points": round(avg_points, 4),
    }


def _choose_consensus_candidate(candidates: list[dict[str, Any]]) -> tuple[dict[str, Any], float]:
    if len(candidates) == 1:
        return candidates[0], 1.0
    sig_counts = Counter(item["signature"] for item in candidates)
    winner_sig, count = sig_counts.most_common(1)[0]
    pool = [item for item in candidates if item["signature"] == winner_sig]
    pool.sort(key=lambda item: item["quality"]["score"], reverse=True)
    return pool[0], count / max(len(candidates), 1)


def _layout_section_positions(section_count: int, cross_link_count: int) -> tuple[dict[int, tuple[int, int]], bool, int, int]:
    """Create graph coordinates for sections.

    - Simple contexts keep a single spine.
    - Complex contexts (many sections or non-linear links) use multi-spine lanes.
    """
    if section_count <= 0:
        return {}, False, 1, 0

    use_multi_spine = section_count >= 6 or cross_link_count >= 2
    if not use_multi_spine:
        top_y = 80
        step = 86 if section_count <= 8 else 72
        positions = {idx: (560, top_y + (idx + 1) * step) for idx in range(section_count)}
        return positions, False, 1, section_count

    cols = 3 if section_count >= 9 or cross_link_count >= 4 else 2
    rows = (section_count + cols - 1) // cols
    x_positions = [420, 700] if cols == 2 else [300, 560, 820]
    y_start = 190
    row_step = 0 if rows <= 1 else max(90, min(130, int((690 - y_start) / (rows - 1))))

    positions: dict[int, tuple[int, int]] = {}
    for idx in range(section_count):
        row = idx // cols
        col = idx % cols
        positions[idx] = (x_positions[col], y_start + row * row_step)
    return positions, True, cols, rows


def _outline_to_logic_steps_text(outline: dict[str, Any]) -> str:
    """Build a readable step-by-step explanation for the generated outline."""
    normalized = _normalize_outline(outline)
    sections = normalized.get("sections", [])
    links = normalized.get("links", [])
    title = str(normalized.get("title", "Auto Diagram")).strip() or "Auto Diagram"

    if not sections:
        return "No structured steps were generated yet."

    lines: list[str] = [f"Structured Logic: {title}", "", "Step-by-step breakdown:"]
    for idx, section in enumerate(sections, start=1):
        label = _clean_label(str(section.get("label", "")), f"Section {idx}")
        summary = str(section.get("summary", "")).strip() or f"Generated section {idx}."
        points = section.get("points") if isinstance(section.get("points"), list) else []
        clean_points = [str(item).strip() for item in points if str(item).strip()][:4]

        lines.append(f"{idx}. {label}")
        lines.append(f"   Purpose: {summary}")
        if clean_points:
            lines.append("   Key points:")
            for point in clean_points:
                lines.append(f"   - {point}")
        lines.append("")

    dependency_lines: list[str] = []
    for link in links:
        try:
            src = int(link.get("from", -1))
            dst = int(link.get("to", -1))
        except (TypeError, ValueError):
            continue
        if src < 0 or dst < 0 or src >= len(sections) or dst >= len(sections) or src == dst:
            continue
        src_label = _clean_label(str(sections[src].get("label", "")), f"Section {src + 1}")
        dst_label = _clean_label(str(sections[dst].get("label", "")), f"Section {dst + 1}")
        reason = str(link.get("reason", "Dependency in context."))[:220]
        relation = "Sequential" if dst == src + 1 else "Cross-link"
        dependency_lines.append(
            f"- {relation}: [{src + 1}] {src_label} -> [{dst + 1}] {dst_label}. Reason: {reason}"
        )

    if dependency_lines:
        lines.extend(["Dependencies:", *dependency_lines, ""])

    chain = " -> ".join([f"[{idx + 1}] { _clean_label(str(sec.get('label', '')), f'Section {idx + 1}') }" for idx, sec in enumerate(sections)])
    lines.extend(["Suggested reading order:", chain])
    return "\n".join(lines).strip()


def _to_graph(outline: dict[str, Any], context_preview: str) -> dict[str, Any]:
    sections = outline.get("sections") or []
    links = outline.get("links") or []
    sections = sections[:10]

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    normalized_links: list[tuple[int, int, str]] = []
    for link in links:
        try:
            src_i = int(link.get("from", -1))
            dst_i = int(link.get("to", -1))
        except (TypeError, ValueError):
            continue
        if src_i == dst_i:
            continue
        if src_i < 0 or dst_i < 0 or src_i >= len(sections) or dst_i >= len(sections):
            continue
        reason = str(link.get("reason", "Cross-section dependency."))[:240]
        normalized_links.append((src_i, dst_i, reason))

    cross_link_count = sum(1 for src_i, dst_i, _ in normalized_links if abs(dst_i - src_i) > 1)
    positions, use_multi_spine, cols, rows = _layout_section_positions(len(sections), cross_link_count)
    x_main = 560
    input_y = 88 if use_multi_spine else 80

    input_node = {
        "id": "InputContext",
        "label": "InputContext",
        "x": x_main,
        "y": input_y,
        "kind": "input",
        "role": "Raw context",
        "detail": "Pasted long context as source material for auto structuring.",
        "inside": [context_preview[:120] or "No preview available."],
    }
    nodes.append(input_node)

    section_id_map: dict[int, str] = {}
    for idx, section in enumerate(sections):
        node_id = f"S{idx + 1}"
        section_id_map[idx] = node_id
        label = _clean_label(str(section.get("label", "")), f"Section {idx + 1}")
        summary = str(section.get("summary", ""))
        points = section.get("points") if isinstance(section.get("points"), list) else []
        clean_points = [str(item).strip() for item in points if str(item).strip()]
        if not clean_points:
            clean_points = _top_keywords(summary, max_items=4) or [f"detail_{idx + 1}"]
        node_x, node_y = positions.get(idx, (x_main, 220 + idx * 76))
        nodes.append(
            {
                "id": node_id,
                "label": label,
                "x": node_x,
                "y": node_y,
                "kind": "main",
                "role": "Structured section",
                "detail": summary[:220] or f"Generated section {idx + 1}.",
                "inside": clean_points[:6],
            }
        )

    if sections:
        max_section_y = max(y for _, y in positions.values())
        output_y = min(840, max_section_y + (150 if use_multi_spine else 86))
    else:
        output_y = 220
    output_node = {
        "id": "StructuredMap",
        "label": "StructuredMap",
        "x": x_main,
        "y": output_y,
        "kind": "output",
        "role": "Diagram output",
        "detail": "Final high-level section map with dependencies.",
        "inside": ["section graph", "dependency links", "click-to-inspect details"],
    }
    nodes.append(output_node)

    edge_counter = 1
    if sections:
        entry_count = min(cols if use_multi_spine else 1, len(sections))
        for idx in range(entry_count):
            edges.append(
                {
                    "id": f"e{edge_counter}",
                    "from": "InputContext",
                    "to": section_id_map[idx],
                    "kind": "input",
                    "why": (
                        "Input context is decomposed into multiple primary sections."
                        if use_multi_spine
                        else "Input context is the source for first section."
                    ),
                    "does": (
                        "Starts one of the major section spines for complex context."
                        if use_multi_spine
                        else "Initial decomposition starts from raw context."
                    ),
                    "executor": "Selected model + fallback parser.",
                    "source": "Textarea input context.",
                }
            )
            edge_counter += 1

    for idx in range(len(sections) - 1):
        edges.append(
            {
                "id": f"e{edge_counter}",
                "from": f"S{idx + 1}",
                "to": f"S{idx + 2}",
                "kind": "sequential",
                "why": "Maintains major storyline / logic sequence.",
                "does": "Connects adjacent high-level sections.",
            }
        )
        edge_counter += 1

    for src_i, dst_i, reason in normalized_links:
        if dst_i == src_i + 1:
            continue
        edges.append(
            {
                "id": f"e{edge_counter}",
                "from": section_id_map[src_i],
                "to": section_id_map[dst_i],
                "kind": "cross",
                "why": reason,
                "does": "Adds non-linear dependency between sections.",
                "executor": "Dependency inference stage.",
                "source": "Chunk-level concept overlap / model extraction.",
            }
        )
        edge_counter += 1
        if edge_counter > 24:
            break

    if sections:
        if use_multi_spine:
            last_row_start = max((rows - 1) * cols, 0)
            exit_indices = list(range(last_row_start, len(sections)))
        else:
            exit_indices = [len(sections) - 1]
        for idx in exit_indices:
            edges.append(
                {
                    "id": f"e{edge_counter}",
                    "from": section_id_map[idx],
                    "to": "StructuredMap",
                    "kind": "output",
                    "why": (
                        "Each major section spine contributes to the final structured map."
                        if use_multi_spine
                        else "Final section leads to overall diagram output."
                    ),
                    "does": "Completes end-to-end structure generation.",
                }
            )
            edge_counter += 1
            if edge_counter > 36:
                break

    return {
        "nodes": nodes,
        "edges": edges,
        "layout_mode": "multi_spine" if use_multi_spine else "single_spine",
        "main_branch_count": int(cols if use_multi_spine else 1),
    }


def _safe_json_loads(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    if not stripped:
        return None
    try:
        loaded = json.loads(stripped)
        if isinstance(loaded, dict):
            return loaded
    except json.JSONDecodeError:
        pass

    # Weak recovery for wrapped markdown JSON blocks.
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, re.DOTALL)
    if match:
        try:
            loaded = json.loads(match.group(1))
            if isinstance(loaded, dict):
                return loaded
        except json.JSONDecodeError:
            return None
    return None


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str], timeout: int) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url=url, data=data, headers=headers, method="POST")
    with request.urlopen(req, timeout=timeout) as response:  # noqa: S310 - user supplied endpoint by env
        body = response.read().decode("utf-8")
    parsed = json.loads(body)
    if not isinstance(parsed, dict):
        raise ValueError("Provider did not return a JSON object.")
    return parsed


def _build_provider_prompt(text: str, chunks: list[str], *, sampling_hint: str = "") -> str:
    chunk_preview = "\n".join([f"[chunk {idx+1}] {chunk[:320]}" for idx, chunk in enumerate(chunks[:10])])
    return textwrap.dedent(
        f"""
        Task:
        You are converting long free-form context into a high-level structured diagram.
        Return JSON only.

        Requirements:
        - Create 3 to 10 major sections.
        - Each section must have: label, summary, points.
        - points should be short bullet-like details.
        - Add dependency links between sections using zero-based indexes.
        - links: [{{"from": section_index, "to": section_index, "reason": "..."}}]
        - Keep labels concise and non-duplicated.
        - Capture both sequential flow and non-linear dependencies.
        - If content is narrative, preserve chronology and causal links.

        Sampling Hint:
        {sampling_hint or "stable_structure"}

        Input Context:
        {text[:8000]}

        Chunk Previews:
        {chunk_preview}
        """
    ).strip()


def _build_repair_prompt(
    text: str,
    chunks: list[str],
    failed_outline: dict[str, Any],
    issues: list[str],
) -> str:
    issue_text = "\n".join([f"- {issue}" for issue in issues]) or "- improve structural quality"
    chunk_preview = "\n".join([f"[chunk {idx+1}] {chunk[:220]}" for idx, chunk in enumerate(chunks[:8])])
    return textwrap.dedent(
        f"""
        Repair Task:
        Improve the JSON outline so it is better for a section dependency diagram.
        Return JSON only.

        Quality Issues:
        {issue_text}

        Existing Outline JSON:
        {json.dumps(failed_outline, ensure_ascii=False)[:5000]}

        Input Context:
        {text[:6000]}

        Chunk Previews:
        {chunk_preview}
        """
    ).strip()


def _call_local_provider(
    text: str,
    chunks: list[str],
    timeout: int = 30,
    *,
    temperature: float = 0.0,
    prompt_override: str | None = None,
    sampling_hint: str = "",
) -> ProviderResult:
    model = os.getenv("LOCAL_LLM_MODEL", "gpt-oss")
    endpoint = os.getenv("LOCAL_LLM_API_URL", "http://127.0.0.1:11434/api/chat")
    prompt = prompt_override or _build_provider_prompt(text, chunks, sampling_hint=sampling_hint)

    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": "Return ONLY JSON that follows the schema."},
            {"role": "user", "content": prompt},
        ],
        "format": OUTLINE_SCHEMA,
        "options": {"temperature": max(0.0, min(float(temperature), 0.7))},
    }

    try:
        raw = _post_json(endpoint, payload, {"Content-Type": "application/json"}, timeout)
    except (error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
        return ProviderResult(ok=False, payload=None, provider="local", error=str(exc))

    message = raw.get("message", {})
    content = message.get("content", "") if isinstance(message, dict) else ""
    parsed = _safe_json_loads(content) if isinstance(content, str) else None
    if not parsed:
        return ProviderResult(ok=False, payload=None, provider="local", error="No valid JSON in model output.")
    return ProviderResult(ok=True, payload=parsed, provider="local")


def _call_external_provider(
    text: str,
    chunks: list[str],
    timeout: int = 45,
    *,
    temperature: float = 0.0,
    prompt_override: str | None = None,
    sampling_hint: str = "",
) -> ProviderResult:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return ProviderResult(ok=False, payload=None, provider="external", error="OPENAI_API_KEY is missing.")

    endpoint = os.getenv("EXTERNAL_LLM_API_URL", "https://api.openai.com/v1/chat/completions")
    model = os.getenv("EXTERNAL_LLM_MODEL", "gpt-4o-mini")
    prompt = prompt_override or _build_provider_prompt(text, chunks, sampling_hint=sampling_hint)

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Return ONLY JSON that matches the schema exactly."},
            {"role": "user", "content": prompt},
        ],
        "temperature": max(0.0, min(float(temperature), 0.6)),
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "diagram_outline", "strict": True, "schema": OUTLINE_SCHEMA},
        },
    }

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    try:
        raw = _post_json(endpoint, payload, headers, timeout)
    except (error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
        return ProviderResult(ok=False, payload=None, provider="external", error=str(exc))

    choices = raw.get("choices")
    if not isinstance(choices, list) or not choices:
        return ProviderResult(ok=False, payload=None, provider="external", error="No choices returned.")
    message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
    content = message.get("content", "") if isinstance(message, dict) else ""
    parsed = _safe_json_loads(content) if isinstance(content, str) else None
    if not parsed:
        return ProviderResult(ok=False, payload=None, provider="external", error="No valid JSON in output.")
    return ProviderResult(ok=True, payload=parsed, provider="external")


def _validate_outline(outline: dict[str, Any]) -> bool:
    sections = outline.get("sections")
    links = outline.get("links")
    if not isinstance(sections, list) or not sections:
        return False
    if not isinstance(links, list):
        return False
    for section in sections:
        if not isinstance(section, dict):
            return False
        if not isinstance(section.get("label"), str):
            return False
        if not isinstance(section.get("summary"), str):
            return False
        if not isinstance(section.get("points"), list):
            return False
    for link in links:
        if not isinstance(link, dict):
            return False
        if not isinstance(link.get("from"), int):
            return False
        if not isinstance(link.get("to"), int):
            return False
        if not isinstance(link.get("reason"), str):
            return False
    return True


def _quality_issues(report: dict[str, float | int]) -> list[str]:
    issues: list[str] = []
    if int(report.get("section_count", 0)) < 4:
        issues.append("Need at least 4 meaningful sections where possible.")
    if int(report.get("cross_link_count", 0)) < 1:
        issues.append("Need at least one non-linear cross-section dependency.")
    if float(report.get("avg_points", 0.0)) < 0.45:
        issues.append("Each section should include richer key points.")
    if float(report.get("score", 0.0)) < 2.2:
        issues.append("Overall structural quality score is low; improve hierarchy and links.")
    return issues


def _try_provider(
    mode: Mode,
    text: str,
    chunks: list[str],
    llm_attempts: int,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]], dict[str, float | int], bool, float]:
    logs: list[dict[str, Any]] = []
    caller = _call_local_provider if mode == "local" else _call_external_provider
    try:
        sample_count = int(os.getenv("DIAGRAM_CONSENSUS_SAMPLES", "3"))
    except ValueError:
        sample_count = 3
    sample_count = max(1, min(sample_count, 5))
    try:
        min_quality = float(os.getenv("DIAGRAM_MIN_QUALITY", "2.35"))
    except ValueError:
        min_quality = 2.35
    temp_schedule = [0.0, 0.2, 0.35, 0.45, 0.55]

    best_outline: dict[str, Any] | None = None
    best_quality: dict[str, float | int] = {"score": 0.0, "section_count": 0, "edge_count": 0, "cross_link_count": 0, "avg_points": 0.0}
    best_consensus = 0.0

    for attempt in range(1, max(llm_attempts, 0) + 1):
        candidates: list[dict[str, Any]] = []
        for sample_idx in range(sample_count):
            temperature = temp_schedule[min(sample_idx, len(temp_schedule) - 1)]
            result = caller(
                text,
                chunks,
                temperature=temperature,
                sampling_hint=f"attempt_{attempt}_sample_{sample_idx + 1}",
            )
            if not result.ok or not isinstance(result.payload, dict) or not _validate_outline(result.payload):
                logs.append(
                    {
                        "stage": "provider_sample",
                        "attempt": attempt,
                        "sample": sample_idx + 1,
                        "ok": False,
                        "provider": result.provider,
                        "temperature": temperature,
                        "error": result.error[:220],
                    }
                )
                continue

            outline = _enrich_outline_dependencies(_normalize_outline(result.payload), chunks)
            quality = _quality_report(outline)
            candidates.append(
                {
                    "outline": outline,
                    "quality": quality,
                    "signature": _outline_signature(outline),
                    "temperature": temperature,
                }
            )
            logs.append(
                {
                    "stage": "provider_sample",
                    "attempt": attempt,
                    "sample": sample_idx + 1,
                    "ok": True,
                    "provider": result.provider,
                    "temperature": temperature,
                    "score": quality["score"],
                }
            )

        if not candidates:
            continue

        picked, consensus_strength = _choose_consensus_candidate(candidates)
        picked_quality = picked["quality"]
        picked_score = float(picked_quality["score"])
        logs.append(
            {
                "stage": "provider_consensus",
                "attempt": attempt,
                "ok": True,
                "candidate_count": len(candidates),
                "consensus_strength": round(consensus_strength, 4),
                "score": picked_score,
            }
        )

        if picked_score > float(best_quality["score"]):
            best_outline = deepcopy(picked["outline"])
            best_quality = dict(picked_quality)
            best_consensus = consensus_strength

        if picked_score >= min_quality:
            return best_outline, logs, best_quality, True, best_consensus

        repair_prompt = _build_repair_prompt(
            text=text,
            chunks=chunks,
            failed_outline=picked["outline"],
            issues=_quality_issues(picked_quality),
        )
        repair_result = caller(
            text,
            chunks,
            temperature=0.0,
            prompt_override=repair_prompt,
            sampling_hint=f"attempt_{attempt}_repair",
        )
        if not repair_result.ok or not isinstance(repair_result.payload, dict) or not _validate_outline(repair_result.payload):
            logs.append(
                {
                    "stage": "provider_repair",
                    "attempt": attempt,
                    "ok": False,
                    "error": repair_result.error[:220],
                }
            )
            continue

        repaired_outline = _enrich_outline_dependencies(_normalize_outline(repair_result.payload), chunks)
        repaired_quality = _quality_report(repaired_outline)
        repaired_score = float(repaired_quality["score"])
        logs.append(
            {
                "stage": "provider_repair",
                "attempt": attempt,
                "ok": True,
                "score": repaired_score,
            }
        )
        if repaired_score > float(best_quality["score"]):
            best_outline = deepcopy(repaired_outline)
            best_quality = dict(repaired_quality)
            best_consensus = max(best_consensus, consensus_strength)
        if repaired_score >= min_quality:
            return best_outline, logs, best_quality, True, best_consensus

    return best_outline, logs, best_quality, False, best_consensus


def _build_folder_view(outline: dict[str, Any]) -> list[dict[str, Any]]:
    children = []
    for idx, section in enumerate(outline.get("sections", []), start=1):
        points = section.get("points") if isinstance(section.get("points"), list) else []
        children.append(
            {
                "name": f"{idx:02d}_{_clean_label(str(section.get('label', 'section')), f'section_{idx}')}",
                "type": "dir",
                "children": [{"name": str(pt), "type": "file"} for pt in points[:8]],
            }
        )
    return [{"name": "auto_structure", "type": "dir", "children": children}]


def generate_diagram_payload(
    text: str,
    mode: Mode = "local",
    *,
    allow_llm: bool = True,
    llm_attempts: int = 2,
) -> dict[str, Any]:
    """Generate diagram payload from free-form input text.

    This function always returns a usable graph if text is non-empty.
    """
    normalized = _normalize_text(text)
    if not normalized:
        raise ValueError("Input is empty. Please paste text before generating.")

    mode = "external" if mode == "external" else "local"
    chunks = chunk_text(normalized)
    if not chunks:
        chunks = [normalized]

    attempts: list[dict[str, Any]] = []
    provider_outline: dict[str, Any] | None = None
    provider_quality: dict[str, float | int] = {"score": 0.0, "section_count": 0, "edge_count": 0, "cross_link_count": 0, "avg_points": 0.0}
    provider_gate_passed = False
    consensus_strength = 0.0
    if allow_llm:
        provider_outline, attempt_logs, provider_quality, provider_gate_passed, consensus_strength = _try_provider(
            mode,
            normalized,
            chunks,
            llm_attempts,
        )
        attempts.extend(attempt_logs)

    heuristic_outline = _enrich_outline_dependencies(_heuristic_outline(normalized, chunks), chunks)
    heuristic_quality = _quality_report(heuristic_outline)
    heuristic_score = float(heuristic_quality["score"])
    provider_score = float(provider_quality["score"]) if provider_outline else 0.0

    if provider_outline and provider_score >= heuristic_score:
        final_outline = _enrich_outline_dependencies(provider_outline, chunks)
        strategy = f"{mode}_provider_consensus"
        fallback_used = False
    else:
        final_outline = heuristic_outline
        strategy = "heuristic_fallback"
        fallback_used = True

    final_outline = _normalize_outline(final_outline)
    final_quality = _quality_report(final_outline)
    graph = _to_graph(final_outline, context_preview=chunks[0])
    logic_steps_text = _outline_to_logic_steps_text(final_outline)
    payload = {
        "title": final_outline.get("title", "Auto Diagram"),
        "nodes": graph["nodes"],
        "edges": graph["edges"],
        "logic_steps_text": logic_steps_text,
        "folder_view": _build_folder_view(final_outline),
        "meta": {
            "mode_requested": mode,
            "strategy": strategy,
            "fallback_used": fallback_used,
            "quality_gate_passed": bool(provider_gate_passed and not fallback_used),
            "quality_score": round(float(final_quality["score"]), 4),
            "consensus_strength": round(consensus_strength, 4),
            "chunk_count": len(chunks),
            "section_count": len(final_outline.get("sections", [])),
            "edge_count": int(final_quality["edge_count"]),
            "cross_link_count": int(final_quality["cross_link_count"]),
            "layout_mode": str(graph.get("layout_mode", "single_spine")),
            "main_branch_count": int(graph.get("main_branch_count", 1)),
            "attempts": attempts,
            "provider_score": round(provider_score, 4),
            "heuristic_score": round(heuristic_score, 4),
        },
    }
    return payload


def get_generation_test_cases() -> list[dict[str, str]]:
    """Sample test cases for UI quick checks and regression seeds."""
    return [
        {
            "id": "email_context",
            "title": "Workload email",
            "text": (
                "Hi Team, we are balancing ASCO, S1 analyses, DB cut, and amendments. "
                "I will start QC next week and captured pending items for month-end discussion. "
                "I also explored an LLM diagram tool to decompose ideas and show dependencies. "
                "I think a local coding knowledge base with an open-source coding agent is foundational."
            ),
        },
        {
            "id": "random_mix",
            "title": "Random mixed context",
            "text": (
                "Buy milk before 8pm. The ETL failed yesterday due to schema mismatch. "
                "Need to call vendor and update API key rotation SOP. "
                "By Friday we should freeze metrics definitions and review dashboard labels."
            ),
        },
        {
            "id": "short_story",
            "title": "Short narrative story",
            "text": (
                "Mina found an old map in her grandmother's desk. "
                "She asked Leo to help decode the symbols. "
                "They followed clues across town, solved a puzzle at the library, "
                "and discovered a hidden garden that the neighborhood restored together."
            ),
        },
    ]
