"""Smoke test the app-level analytics flow."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.business_qa import answer_from_workbook
from datetime import date

from app.charts import calculate_core_kpis, compare_periods, filter_sales
from app.data_loader import load_workbook
from app.reporting import build_markdown_report_from_sheets


def main() -> None:
    sheets = load_workbook()
    fato = sheets["Fato Vendas"]
    kpis = calculate_core_kpis(fato)
    if kpis["completed_orders"] != 2127:
        raise SystemExit(f"Unexpected completed order count: {kpis['completed_orders']}")

    filtered = filter_sales(fato, categories=["eletronicos"], states=["SP"])
    if filtered.empty:
        raise SystemExit("Expected filtered sales rows for eletronicos/SP")

    answer = answer_from_workbook("Qual foi a receita total?", sheets)
    if "ID Venda" not in answer or "R$ 160.692,02" not in answer:
        raise SystemExit("Governed QA answer did not include expected formula/value")

    retention_answer = answer_from_workbook("Como está a retenção de clientes?", sheets)
    if "Clientes recorrentes" not in retention_answer or "ID Cliente" not in retention_answer:
        raise SystemExit("Retention QA answer did not include expected formula")

    report = build_markdown_report_from_sheets(
        sheets,
        fato_override=filtered,
        filter_note="- Categories: eletronicos\n- States: SP",
    )
    if "Applied Filters" not in report or "eletronicos" not in report:
        raise SystemExit("Filtered report did not include filter disclosure")
    if "Customer Retention" not in report or "Top Customers" not in report:
        raise SystemExit("Filtered report did not include customer retention sections")

    comparison = compare_periods(
        fato,
        current_start=date(2026, 1, 1),
        current_end=date(2026, 6, 30),
        previous_start=date(2025, 7, 1),
        previous_end=date(2025, 12, 31),
    )
    if comparison.empty or "growth_percent" not in comparison.columns:
        raise SystemExit("Period comparison smoke check failed")

    print("app smoke passed")


if __name__ == "__main__":
    main()
