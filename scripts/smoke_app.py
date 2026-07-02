"""Smoke test the app-level analytics flow."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.business_qa import answer_from_workbook
from app.charts import calculate_core_kpis, filter_sales
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

    report = build_markdown_report_from_sheets(
        sheets,
        fato_override=filtered,
        filter_note="- Categories: eletronicos\n- States: SP",
    )
    if "Applied Filters" not in report or "eletronicos" not in report:
        raise SystemExit("Filtered report did not include filter disclosure")

    print("app smoke passed")


if __name__ == "__main__":
    main()
