"""Code Validation Flow

Runs automated validation checks on a draft asset.
Delegates to tools/validators/ for actual check logic.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def run_code_validation(
    asset_card: dict[str, Any],
    code_content: str,
    metadata_validate_fn: Any = None,
    dependency_check_fn: Any = None,
    syntax_check_fn: Any = None,
    run_check_fn: Any = None,
) -> dict[str, Any]:
    """Run all validation checks on a code asset.

    Returns a validation_result dict.
    """
    checks: list[dict[str, Any]] = []

    if metadata_validate_fn:
        result = metadata_validate_fn(asset_card)
        checks.append({"check_name": "metadata_valid", **result})
    else:
        checks.append({
            "check_name": "metadata_valid",
            "passed": True,
            "details": "Validator not connected",
        })

    if dependency_check_fn:
        result = dependency_check_fn(asset_card)
        checks.append({"check_name": "dependency_valid", **result})
    else:
        checks.append({
            "check_name": "dependency_valid",
            "passed": True,
            "details": "Checker not connected",
        })

    if syntax_check_fn:
        result = syntax_check_fn(code_content, asset_card.get("language", "sas"))
        checks.append({"check_name": "syntax_valid", **result})
    else:
        checks.append({
            "check_name": "syntax_valid",
            "passed": True,
            "details": "Checker not connected",
        })

    if run_check_fn:
        result = run_check_fn(code_content, asset_card.get("language", "sas"))
        checks.append({"check_name": "run_valid", **result})

    overall = all(c["passed"] for c in checks)

    return {
        "asset_id": asset_card["asset_id"],
        "checks": checks,
        "overall_passed": overall,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
