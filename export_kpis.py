"""Export core KPIs to a static JSON file for publication.

Usage:
  python export_kpis.py --output public/kpis.json
"""
from __future__ import annotations

import json
from pathlib import Path
import argparse

from app.data_loader import load_workbook
from app.charts import (
    active_product_count,
    calculate_core_kpis,
    cart_summary,
    review_summary,
)


def main(output: Path) -> None:
    sheets = load_workbook()
    kpis = calculate_core_kpis(sheets["Fato Vendas"])
    reviews = review_summary(sheets["Reviews"])
    carts = cart_summary(sheets["Carts"], sheets["Cart Items"])
    products_active = active_product_count(sheets["Products"])

    output_payload = {
        "receita": {
            "revenue": kpis["revenue"],
            "item_revenue": kpis["item_revenue"],
            "average_ticket": kpis["average_ticket"],
            "shipping_total": kpis["shipping_total"],
            "discount_total": kpis["discount_total"],
        },
        "rentabilidade": {
            "gross_profit": kpis["gross_profit"],
            "gross_margin_percent": kpis["gross_margin_percent"],
        },
        "operacao": {
            "completed_orders": kpis["completed_orders"],
            "units_sold": kpis["units_sold"],
            "products_active": products_active,
        },
        "clientes": {
            "average_rating": reviews["average_rating"],
            "open_carts": carts["open_carts"],
            "abandoned_carts": carts["abandoned_carts"],
            "cart_value": carts["cart_item_value"],
        },
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf8") as f:
        json.dump(output_payload, f, indent=2, ensure_ascii=False)
    print(f"Wrote KPIs to {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="public/kpis.json")
    args = parser.parse_args()
    main(Path(args.output))
