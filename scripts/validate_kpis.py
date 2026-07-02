"""Validate core KPI formulas against the knowledge base snapshot."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.charts import calculate_core_kpis
from app.data_loader import load_workbook


EXPECTED = {
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


def main() -> None:
    sheets = load_workbook()
    actual = calculate_core_kpis(sheets["Fato Vendas"])
    mismatches = []
    for key, expected in EXPECTED.items():
        value = actual[key]
        if isinstance(expected, float):
            ok = round(float(value), 2) == round(expected, 2)
        else:
            ok = value == expected
        if not ok:
            mismatches.append(f"{key}: expected {expected}, got {value}")

    print(actual)
    if mismatches:
        raise SystemExit("KPI validation failed: " + "; ".join(mismatches))
    print("KPI validation passed")


if __name__ == "__main__":
    main()
