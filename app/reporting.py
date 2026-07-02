"""Markdown report generation for the analytics snapshot."""

from __future__ import annotations

from pathlib import Path

from app.business_qa import _format_brl
from app.charts import (
    calculate_core_kpis,
    cart_status_summary,
    category_performance,
    customer_retention_summary,
    monthly_customer_cohorts,
    payment_method_summary,
    product_ranking,
    rating_distribution,
    revenue_by_state,
    review_summary,
    top_customers,
)
from app.data_loader import DEFAULT_WORKBOOK_PATH, load_workbook


def _markdown_table(rows) -> str:
    if rows.empty:
        return "_No data._"

    columns = [str(column) for column in rows.columns]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for _, row in rows.iterrows():
        values = [str(row[column]) for column in rows.columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def build_markdown_report_from_sheets(
    sheets,
    fato_override=None,
    filter_note: str | None = None,
) -> str:
    fato = sheets["Fato Vendas"] if fato_override is None else fato_override
    kpis = calculate_core_kpis(fato)
    reviews = review_summary(sheets["Reviews"])
    retention = customer_retention_summary(fato)

    categories = category_performance(fato).head(6)
    products = product_ranking(fato, limit=5)
    states = revenue_by_state(fato).head(5)
    payments = payment_method_summary(fato)
    ratings = rating_distribution(sheets["Reviews"])
    carts = cart_status_summary(sheets["Carts"], sheets["Cart Items"])
    customers = top_customers(fato, sheets["Dimensão Clientes"], limit=5)
    cohorts = monthly_customer_cohorts(fato).head(12)

    lines = [
        "# MEI Commerce AI Analytics Report",
        "",
        "## Executive Summary",
        "",
        f"- Completed orders: {kpis['completed_orders']}",
        f"- Completed order revenue: {_format_brl(kpis['revenue'])}",
        f"- Item revenue: {_format_brl(kpis['item_revenue'])}",
        f"- Gross profit: {_format_brl(kpis['gross_profit'])}",
        f"- Gross margin: {kpis['gross_margin_percent']:.2f}%",
        f"- Average ticket: {_format_brl(kpis['average_ticket'])}",
        f"- Units sold: {kpis['units_sold']}",
        f"- Active customers: {retention['active_customers']}",
        f"- Repeat customers: {retention['repeat_customers']} ({retention['repeat_customer_rate_percent']:.2f}%)",
        f"- Average customer revenue: {_format_brl(retention['average_customer_revenue'])}",
        f"- Reviews: {reviews['review_count']} with average rating {reviews['average_rating']:.2f}",
        "",
        "Revenue is order-level: `Fato Vendas` is deduplicated by `ID Venda` before summing `Total do Pedido (R$)`. Product and category metrics use item-level fields.",
        "",
    ]
    if filter_note:
        lines.extend(["## Applied Filters", "", filter_note, ""])

    lines.extend(
        [
            "## Category Performance",
            "",
            _markdown_table(categories),
            "",
            "## Top Products",
            "",
            _markdown_table(products),
            "",
            "## State Revenue",
            "",
            _markdown_table(states),
            "",
            "## Payment Methods",
            "",
            _markdown_table(payments),
            "",
            "## Customer Retention",
            "",
            "Customer revenue is order-level: `Fato Vendas` is deduplicated by `ID Venda`, grouped by `ID Cliente`, and summed from `Total do Pedido (R$)`.",
            "",
            "### Top Customers",
            "",
            _markdown_table(customers),
            "",
            "### Monthly Customer Cohorts",
            "",
            _markdown_table(cohorts),
            "",
            "## Review Distribution",
            "",
            _markdown_table(ratings),
            "",
            "## Cart Status",
            "",
            _markdown_table(carts),
            "",
            "## Known Limitations",
            "",
            "- Data is synthetic and snapshot-based.",
            "- Coupon code attribution is unavailable; discount amount is reliable.",
            "- `Departamento` duplicates `Categoria`.",
            "- Shipping and discounts are order-level, not item-level.",
            "",
        ]
    )
    return "\n".join(lines)


def build_markdown_report(workbook_path: str | Path = DEFAULT_WORKBOOK_PATH) -> str:
    sheets = load_workbook(workbook_path)
    return build_markdown_report_from_sheets(sheets)


def write_markdown_report(
    output_path: str | Path = "reports/mei_commerce_report.md",
    workbook_path: str | Path = DEFAULT_WORKBOOK_PATH,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_markdown_report(workbook_path), encoding="utf-8")
    return path
