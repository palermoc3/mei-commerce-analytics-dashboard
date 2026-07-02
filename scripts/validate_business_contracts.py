"""Validate business-rule contracts from the knowledge base against the workbook."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.charts import customer_retention_summary
from app.data_loader import load_workbook


TOLERANCE = 0.01
COMPLETED_STATUSES = {"paid", "shipped"}


def _close(actual: pd.Series, expected: pd.Series) -> pd.Series:
    return (actual.astype(float) - expected.astype(float)).abs() <= TOLERANCE


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate_business_contracts(sheets: dict[str, pd.DataFrame]) -> list[str]:
    """Return validation errors for workbook-level business contracts."""

    errors: list[str] = []

    fato = sheets["Fato Vendas"]
    purchases = sheets["Purchases"]
    item_purchases = sheets["Item Purchases"]
    products = sheets["Products"]
    users = sheets["Users"]
    customer_dimension = sheets["Dimensão Clientes"]
    reviews = sheets["Reviews"]
    coupons = sheets["Coupons"]
    carts = sheets["Carts"]
    cart_items = sheets["Cart Items"]

    purchase_expected_total = (
        purchases["Subtotal (R$)"] + purchases["Frete (R$)"] - purchases["Desconto (R$)"]
    )
    _require(
        bool(_close(purchases["Total (R$)"], purchase_expected_total).all()),
        "Purchases.Total must equal subtotal + shipping - discount within R$ 0.01",
        errors,
    )
    _require(
        set(purchases["Status"]).issubset({"pending", "paid", "shipped", "canceled"}),
        "Purchases.Status contains values outside the documented enum",
        errors,
    )
    _require(
        set(purchases["Metodo Pagamento"]).issubset({"pix", "credit_card", "debit_card"}),
        "Purchases.Metodo Pagamento contains values outside the documented enum",
        errors,
    )
    _require(
        set(fato["Status Venda"]).issubset(COMPLETED_STATUSES),
        "Fato Vendas must contain only paid or shipped purchases",
        errors,
    )
    completed_purchase_ids = set(
        purchases.loc[purchases["Status"].isin(COMPLETED_STATUSES), "ID"]
    )
    _require(
        set(fato["ID Venda"]) == completed_purchase_ids,
        "Fato Vendas IDs must match completed Purchases IDs exactly",
        errors,
    )

    item_expected_subtotal = (
        item_purchases["Quantidade"] * item_purchases["Preco Unitario (R$)"]
    )
    _require(
        bool((item_purchases["Quantidade"] > 0).all()),
        "Item Purchases.Quantidade must be positive",
        errors,
    )
    _require(
        bool(_close(item_purchases["Subtotal (R$)"], item_expected_subtotal).all()),
        "Item Purchases.Subtotal must equal quantity * unit price within R$ 0.01",
        errors,
    )

    cart_expected_subtotal = cart_items["Quantidade"] * cart_items["Preco Unitario (R$)"]
    _require(
        set(carts["Status"]).issubset({"open", "checked_out", "abandoned"}),
        "Carts.Status contains values outside the documented enum",
        errors,
    )
    _require(
        bool((cart_items["Quantidade"] > 0).all()),
        "Cart Items.Quantidade must be positive",
        errors,
    )
    _require(
        bool(_close(cart_items["Subtotal (R$)"], cart_expected_subtotal).all()),
        "Cart Items.Subtotal must equal quantity * unit price within R$ 0.01",
        errors,
    )

    _require(
        bool((products["Estoque"] >= 0).all()),
        "Products.Estoque must be non-negative",
        errors,
    )
    _require(
        bool((products["Preco Venda (R$)"] >= 0).all()),
        "Products.Preco Venda must be non-negative",
        errors,
    )
    _require(
        bool((products["Preco Custo (R$)"] >= 0).all()),
        "Products.Preco Custo must be non-negative",
        errors,
    )
    _require(
        bool((products["Preco Venda (R$)"] > products["Preco Custo (R$)"]).all()),
        "Products.Preco Venda must be greater than Preco Custo",
        errors,
    )

    normalized_emails = users["Email"].str.casefold()
    _require(
        bool(normalized_emails.is_unique),
        "Users.Email must be unique case-insensitively",
        errors,
    )
    _require(
        bool(users["Email"].str.contains(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", regex=True).all()),
        "Users.Email must match a basic email format",
        errors,
    )
    _require(
        bool((customer_dimension["Idade"] >= 18).all()),
        "Dimensão Clientes.Idade must be at least 18",
        errors,
    )

    _require(
        bool(reviews["Nota"].between(1, 5).all()),
        "Reviews.Nota must be an integer rating from 1 to 5",
        errors,
    )
    _require(
        not reviews.duplicated(["ID Cliente", "ID Produto"]).any(),
        "Reviews must be unique per customer-product pair",
        errors,
    )

    _require(
        bool(coupons["Codigo"].str.casefold().is_unique),
        "Coupons.Codigo must be unique case-insensitively",
        errors,
    )
    _require(
        set(coupons["Tipo Desconto"]).issubset({"percentage", "fixed_amount"}),
        "Coupons.Tipo Desconto contains values outside the documented enum",
        errors,
    )
    _require(
        bool((coupons["Valor Desconto"] > 0).all()),
        "Coupons.Valor Desconto must be greater than zero",
        errors,
    )

    _require(
        bool((fato["Departamento"] == fato["Categoria"]).all()),
        "Fato Vendas.Departamento must duplicate Categoria in this snapshot",
        errors,
    )
    retention = customer_retention_summary(fato)
    _require(
        retention["active_customers"] == sheets["Dimensão Clientes"]["ID Cliente"].nunique(),
        "Retention active customers must match Dimensão Clientes customer count",
        errors,
    )

    return errors


def main() -> None:
    sheets = load_workbook()
    errors = validate_business_contracts(sheets)
    if errors:
        raise SystemExit("Business contract validation failed: " + "; ".join(errors))
    print("business contract validation passed")


if __name__ == "__main__":
    main()
