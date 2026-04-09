"""Diff Report

Generates human-readable diff reports from comparison results.
"""

from __future__ import annotations

from typing import Any


def generate_diff_report(compare_result: dict[str, Any]) -> str:
    """Generate a markdown-formatted diff report from a compare_result.

    Args:
        compare_result: Dict conforming to schemas/compare_result.schema.json.

    Returns:
        Markdown string.
    """
    lines: list[str] = []
    lines.append(f"# Comparison Report")
    lines.append(f"")
    lines.append(f"- **Compare ID**: {compare_result.get('compare_id', 'N/A')}")
    lines.append(f"- **Task ID**: {compare_result.get('task_id', 'N/A')}")
    lines.append(f"- **Generated Asset**: {compare_result.get('generated_asset_id', 'N/A')}")
    lines.append(f"- **Reference Asset**: {compare_result.get('reference_asset_id', 'N/A')}")
    lines.append(f"- **Logic Match**: {compare_result.get('logic_match', 'N/A')}")
    lines.append(f"- **Output Match**: {compare_result.get('output_match', 'N/A')}")
    lines.append(f"- **Similarity Score**: {compare_result.get('similarity_score', 'N/A')}")
    lines.append(f"")

    differences = compare_result.get("differences", [])
    if differences:
        lines.append(f"## Differences ({len(differences)} found)")
        lines.append("")
        lines.append("| Location | Severity | Expected | Actual |")
        lines.append("|----------|----------|----------|--------|")
        for d in differences:
            lines.append(
                f"| {d.get('location', '')} "
                f"| {d.get('severity', '')} "
                f"| {d.get('expected', '')[:50]} "
                f"| {d.get('actual', '')[:50]} |"
            )
    else:
        lines.append("## No differences found")

    lines.append("")
    lines.append(f"*Generated at {compare_result.get('timestamp', 'N/A')}*")

    return "\n".join(lines)
