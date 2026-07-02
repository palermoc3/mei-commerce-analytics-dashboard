"""Regression tests for workbook analytics formulas."""

from __future__ import annotations

import unittest

from app.charts import (
    calculate_core_kpis,
    cart_recovery_table,
    cart_status_summary,
    category_performance,
    payment_method_summary,
    product_ranking,
    rating_distribution,
    revenue_by_state,
)
from app.business_qa import answer_from_workbook
from app.data_loader import REQUIRED_SHEETS, load_workbook
from app.reporting import build_markdown_report


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


if __name__ == "__main__":
    unittest.main()
