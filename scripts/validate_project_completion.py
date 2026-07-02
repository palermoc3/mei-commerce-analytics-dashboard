"""Validate that the shipped project surfaces are complete and aligned."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.business_qa import answer_from_workbook
from app.charts import calculate_core_kpis
from app.data_loader import REQUIRED_SHEETS, load_workbook
from app.reporting import build_markdown_report_from_sheets


REQUIRED_FILES = (
    "README.md",
    "requirements.txt",
    ".env.example",
    ".github/workflows/ci.yml",
    "data/dataset_analitico_mei.xlsx",
    "docs/AI_BUSINESS_KNOWLEDGE_BASE.md",
    "app/__init__.py",
    "app/main.py",
    "app/data_loader.py",
    "app/charts.py",
    "app/business_qa.py",
    "app/gemini_client.py",
    "app/reporting.py",
    "scripts/run_checks.py",
    "scripts/smoke_app.py",
    "scripts/validate_workbook_contract.py",
    "scripts/validate_business_contracts.py",
    "scripts/validate_knowledge_base.py",
    "scripts/validate_kpis.py",
    "scripts/validate_project_completion.py",
    "scripts/export_report.py",
    "tests/test_analytics.py",
)

REQUIRED_DOC_SNIPPETS = {
    "README.md": (
        "## Por Que Este Projeto Mostra Prontidão Júnior",
        "## Como Usei IA Neste Projeto",
        "python scripts/validate_project_completion.py",
    ),
    "docs/AI_BUSINESS_KNOWLEDGE_BASE.md": (
        "## Project Completion Audit",
        "scripts/validate_project_completion.py",
    ),
}

EXPECTED_KPIS = {
    "completed_orders": 2127,
    "revenue": 160692.02,
    "item_revenue": 151081.10,
    "gross_profit": 73807.63,
    "gross_margin_percent": 48.85,
    "average_ticket": 75.55,
    "units_sold": 3279,
    "shipping_total": 12090.00,
    "discount_total": 2479.08,
}

REQUIRED_REPORT_SECTIONS = (
    "Executive Summary",
    "Category Performance",
    "Top Products By Units",
    "Raw Orders By Status",
    "Customer Retention",
    "Product Review Quality",
    "Known Limitations",
)

REQUIRED_QA_SNIPPETS = (
    ("Qual foi a receita total?", "Grão: pedido"),
    ("Como está a retenção de clientes?", "Clientes recorrentes"),
    ("Pedidos pending entram nas vendas?", "Fonte: `Purchases`"),
    ("Como estão os carrinhos abandonados?", "grão operacional de carrinho"),
    ("Quais cupons deram desconto?", "Limitação"),
)


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def validate_project_completion() -> list[str]:
    """Return completion-audit errors without exiting."""

    errors: list[str] = []

    for relative_path in REQUIRED_FILES:
        path = ROOT / relative_path
        if not path.exists():
            errors.append(f"missing required file: {relative_path}")
        elif path.is_file() and path.stat().st_size == 0 and relative_path != "app/__init__.py":
            errors.append(f"empty required file: {relative_path}")

    for relative_path, snippets in REQUIRED_DOC_SNIPPETS.items():
        path = ROOT / relative_path
        if not path.exists():
            continue
        content = _read(relative_path)
        for snippet in snippets:
            if snippet not in content:
                errors.append(f"{relative_path} missing snippet: {snippet}")

    run_checks = _read("scripts/run_checks.py")
    if "scripts/validate_project_completion.py" not in run_checks:
        errors.append("standard gate does not include project completion validation")

    try:
        sheets = load_workbook(ROOT / "data/dataset_analitico_mei.xlsx")
    except Exception as exc:  # pragma: no cover - reported as audit failure
        errors.append(f"workbook failed to load: {exc}")
        return errors

    if set(sheets) != set(REQUIRED_SHEETS):
        errors.append("loaded workbook sheets do not match REQUIRED_SHEETS")

    kpis = calculate_core_kpis(sheets["Fato Vendas"])
    if kpis != EXPECTED_KPIS:
        errors.append(f"KPI snapshot mismatch: {kpis}")

    report = build_markdown_report_from_sheets(sheets)
    for section in REQUIRED_REPORT_SECTIONS:
        if section not in report:
            errors.append(f"report missing section: {section}")

    for question, expected in REQUIRED_QA_SNIPPETS:
        answer = answer_from_workbook(question, sheets)
        if expected not in answer:
            errors.append(f"QA answer for {question!r} missing {expected!r}")

    return errors


def main() -> None:
    errors = validate_project_completion()
    if errors:
        raise SystemExit("project completion validation failed: " + "; ".join(errors))
    print("project completion validation passed")


if __name__ == "__main__":
    main()
