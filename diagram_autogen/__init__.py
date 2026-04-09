"""Auto diagram generation package."""

from .pipeline import chunk_text, generate_diagram_payload, get_generation_test_cases

__all__ = ["chunk_text", "generate_diagram_payload", "get_generation_test_cases"]
