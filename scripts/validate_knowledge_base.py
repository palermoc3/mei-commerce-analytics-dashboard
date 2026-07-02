"""Validate that the canonical business knowledge base is present."""

from __future__ import annotations

from pathlib import Path


KNOWLEDGE_BASE_PATH = Path("docs/AI_BUSINESS_KNOWLEDGE_BASE.md")

REQUIRED_SECTIONS = (
    "## Source Of Truth Priority",
    "## Business Glossary",
    "## Workbook Structure",
    "## Data Dictionary",
    "## Entity Relationships",
    "## Business Rules And Validations",
    "## Metrics And KPI Definitions",
    "## Current Analytical Highlights",
    "## Reporting Rules",
    "## Chart Specification",
    "## Common Business Questions And Expected AI Reasoning",
    "## Implemented Application Scope",
    "## Known Assumptions And Limitations",
    "## AI Handoff",
)

REQUIRED_SNIPPETS = (
    "Tests in `test/` or `tests/`",
    "`Fato Vendas` grain is one row per item",
    "deduplicating by `ID Venda`",
    "Coupon code attribution is unavailable",
    "Customer retention uses:",
    "python scripts/run_checks.py",
)


def main() -> None:
    if not KNOWLEDGE_BASE_PATH.exists():
        raise SystemExit(f"Missing knowledge base: {KNOWLEDGE_BASE_PATH}")

    content = KNOWLEDGE_BASE_PATH.read_text(encoding="utf-8")
    if not content.strip():
        raise SystemExit(f"Empty knowledge base: {KNOWLEDGE_BASE_PATH}")

    missing_sections = [
        section for section in REQUIRED_SECTIONS if section not in content
    ]
    missing_snippets = [
        snippet for snippet in REQUIRED_SNIPPETS if snippet not in content
    ]

    errors = []
    if missing_sections:
        errors.append("missing sections: " + ", ".join(missing_sections))
    if missing_snippets:
        errors.append("missing required snippets: " + ", ".join(missing_snippets))
    if errors:
        raise SystemExit("Knowledge base validation failed: " + "; ".join(errors))

    print(f"knowledge_base={KNOWLEDGE_BASE_PATH}")
    print("knowledge base validation passed")


if __name__ == "__main__":
    main()
