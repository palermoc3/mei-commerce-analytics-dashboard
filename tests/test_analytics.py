"""Regression tests for workbook analytics formulas."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.charts import (
    calculate_core_kpis,
    cart_recovery_table,
    cart_status_summary,
    category_performance,
    filter_sales,
    payment_method_summary,
    product_ranking,
    rating_distribution,
    revenue_by_state,
)
from app.business_qa import answer_from_workbook
from app.data_loader import REQUIRED_SHEETS, load_workbook
from app.gemini_client import load_env_file
from app.reporting import build_markdown_report, build_markdown_report_from_sheets


class AnalyticsFormulaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sheets = load_workbook()
        cls.fato = cls.sheets["Fato Vendas"]

    def test_required_sheets_load(self) -> None:
        self.assertEqual(set(REQUIRED_SHEETS), set(self.sheets))

    def test_core_kpis_match_knowledge_base(self) -> None:
        self.assertEqual(
            calculate_core_kpis(self.fato),
            {
                "completed_orders": 2127,
                "revenue": 160692.02,
                "item_revenue": 151081.10,
                "gross_profit": 73807.63,
                "gross_margin_percent": 48.85,
                "average_ticket": 75.55,
                "units_sold": 3279,
                "shipping_total": 12090.00,
                "discount_total": 2479.08,
            },
        )

    def test_revenue_is_not_item_row_order_total_sum(self) -> None:
        repeated_total_sum = round(float(self.fato["Total do Pedido (R$)"].sum()), 2)
        governed_revenue = calculate_core_kpis(self.fato)["revenue"]

        self.assertNotEqual(repeated_total_sum, governed_revenue)
        self.assertEqual(governed_revenue, 160692.02)

    def test_category_and_product_rankings_use_item_fields(self) -> None:
        categories = category_performance(self.fato)
        products = product_ranking(self.fato, limit=3)

        self.assertEqual(categories.iloc[0]["Categoria"], "eletronicos")
        self.assertEqual(categories.iloc[0]["item_revenue"], 37409.10)
        self.assertEqual(products.iloc[0]["Produto"], "Fone Bluetooth")
        self.assertEqual(products.iloc[0]["item_revenue"], 9790.20)

    def test_state_and_payment_use_order_level_revenue(self) -> None:
        states = revenue_by_state(self.fato)
        payments = payment_method_summary(self.fato)

        self.assertEqual(states.iloc[0]["Estado Cliente"], "SP")
        self.assertEqual(states.iloc[0]["revenue"], 15234.73)
        self.assertEqual(payments.iloc[0]["Metodo Pagamento"], "credit_card")
        self.assertEqual(payments.iloc[0]["completed_orders"], 903)

    def test_business_qa_mentions_grain_and_formula(self) -> None:
        answer = answer_from_workbook("Qual foi a receita total?", self.sheets)

        self.assertIn("Grão: pedido", answer)
        self.assertIn("ID Venda", answer)
        self.assertIn("R$ 160.692,02", answer)

    def test_business_qa_coupon_limitation(self) -> None:
        answer = answer_from_workbook("Quais cupons deram desconto?", self.sheets)

        self.assertIn("Limitação", answer)
        self.assertIn("Cupom Utilizado", answer)

    def test_cart_and_review_insights(self) -> None:
        cart_status = cart_status_summary(self.sheets["Carts"], self.sheets["Cart Items"])
        recovery = cart_recovery_table(
            self.sheets["Carts"], self.sheets["Cart Items"], self.sheets["Users"], limit=5
        )
        ratings = rating_distribution(self.sheets["Reviews"])

        self.assertEqual(int(cart_status["carts"].sum()), 55)
        self.assertEqual(round(float(cart_status["cart_value"].sum()), 2), 8015.80)
        self.assertEqual(len(recovery), 5)
        self.assertEqual(int(ratings["review_count"].sum()), 259)

    def test_markdown_report_contains_metric_contract(self) -> None:
        report = build_markdown_report()

        self.assertIn("MEI Commerce AI Analytics Report", report)
        self.assertIn("deduplicated by `ID Venda`", report)
        self.assertIn("Coupon code attribution is unavailable", report)

    def test_filtered_markdown_report_discloses_filters(self) -> None:
        filtered = filter_sales(self.fato, categories=["eletronicos"])
        report = build_markdown_report_from_sheets(
            self.sheets,
            fato_override=filtered,
            filter_note="- Categories: eletronicos",
        )

        self.assertIn("Applied Filters", report)
        self.assertIn("eletronicos", report)

    def test_filter_sales_limits_fact_rows_by_business_dimensions(self) -> None:
        filtered = filter_sales(
            self.fato,
            start_date=__import__("datetime").date(2026, 1, 1),
            end_date=__import__("datetime").date(2026, 6, 30),
            categories=["eletronicos"],
            states=["SP"],
            payment_methods=["pix"],
        )

        self.assertFalse(filtered.empty)
        self.assertEqual(set(filtered["Categoria"]), {"eletronicos"})
        self.assertEqual(set(filtered["Estado Cliente"]), {"SP"})
        self.assertEqual(set(filtered["Metodo Pagamento"]), {"pix"})

    def test_load_env_file_does_not_override_existing_values(self) -> None:
        with TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("GEMINI_API_KEY=from_file\nNEW_KEY=value\n", encoding="utf-8")

            import os

            old_gemini = os.environ.get("GEMINI_API_KEY")
            old_new = os.environ.get("NEW_KEY")
            os.environ["GEMINI_API_KEY"] = "existing"
            os.environ.pop("NEW_KEY", None)
            try:
                loaded = load_env_file(env_path)
                self.assertEqual(os.environ["GEMINI_API_KEY"], "existing")
                self.assertEqual(os.environ["NEW_KEY"], "value")
                self.assertEqual(loaded, {"NEW_KEY": "value"})
            finally:
                if old_gemini is None:
                    os.environ.pop("GEMINI_API_KEY", None)
                else:
                    os.environ["GEMINI_API_KEY"] = old_gemini
                if old_new is None:
                    os.environ.pop("NEW_KEY", None)
                else:
                    os.environ["NEW_KEY"] = old_new


if __name__ == "__main__":
    unittest.main()
