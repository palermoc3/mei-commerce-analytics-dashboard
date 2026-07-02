"""Analytics calculations and chart-ready tables for MEI commerce data."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date

import pandas as pd


ORDER_ID = "ID Venda"
ORDER_TOTAL = "Total do Pedido (R$)"
ITEM_REVENUE = "Subtotal Item (R$)"
GROSS_PROFIT = "Lucro Bruto Item (R$)"
QUANTITY = "Quantidade Item"
DATE = "Data Compra"


@dataclass(frozen=True)
class CoreKpis:
    completed_orders: int
    revenue: float
    item_revenue: float
    gross_profit: float
    gross_margin_percent: float
    average_ticket: float
    units_sold: int
    shipping_total: float
    discount_total: float

    def as_dict(self) -> dict[str, float | int]:
        return asdict(self)


def _round_money(value: float) -> float:
    return round(float(value), 2)


def _round_percent(value: float) -> float:
    return round(float(value), 2)


def _purchase_datetime(series: pd.Series) -> pd.Series:
    """Normalize purchase timestamps before monthly grouping."""

    return pd.to_datetime(series, utc=True).dt.tz_convert(None)


def order_level_sales(fato_vendas: pd.DataFrame) -> pd.DataFrame:
    """Return one row per completed order from item-grain `Fato Vendas`."""

    required = [
        ORDER_ID,
        DATE,
        "ID Cliente",
        "Estado Cliente",
        "Metodo Pagamento",
        "Status Venda",
        "Desconto Cupom (R$)",
        "Frete (R$)",
        ORDER_TOTAL,
    ]
    missing = [column for column in required if column not in fato_vendas.columns]
    if missing:
        raise KeyError("Fato Vendas missing columns: " + ", ".join(missing))

    orders = (
        fato_vendas[required]
        .sort_values([ORDER_ID, DATE])
        .drop_duplicates(subset=ORDER_ID, keep="first")
        .copy()
    )
    orders[DATE] = _purchase_datetime(orders[DATE])
    orders["Mes"] = orders[DATE].dt.to_period("M").astype(str)
    return orders


def filter_sales(
    fato_vendas: pd.DataFrame,
    start_date: date | None = None,
    end_date: date | None = None,
    categories: list[str] | None = None,
    states: list[str] | None = None,
    payment_methods: list[str] | None = None,
) -> pd.DataFrame:
    """Filter item-grain fact rows while preserving the original columns."""

    filtered = fato_vendas.copy()
    purchase_dates = _purchase_datetime(filtered[DATE]).dt.date

    if start_date is not None:
        filtered = filtered.loc[purchase_dates >= start_date]
        purchase_dates = purchase_dates.loc[filtered.index]
    if end_date is not None:
        filtered = filtered.loc[purchase_dates <= end_date]
        purchase_dates = purchase_dates.loc[filtered.index]
    if categories:
        filtered = filtered.loc[filtered["Categoria"].isin(categories)]
    if states:
        filtered = filtered.loc[filtered["Estado Cliente"].isin(states)]
    if payment_methods:
        filtered = filtered.loc[filtered["Metodo Pagamento"].isin(payment_methods)]

    return filtered.copy()


def calculate_core_kpis(fato_vendas: pd.DataFrame) -> dict[str, float | int]:
    """Calculate governed core KPIs from the item-grain fact table."""

    orders = order_level_sales(fato_vendas)
    completed_orders = int(orders[ORDER_ID].nunique())
    revenue = float(orders[ORDER_TOTAL].sum())
    item_revenue = float(fato_vendas[ITEM_REVENUE].sum())
    gross_profit = float(fato_vendas[GROSS_PROFIT].sum())
    units_sold = int(fato_vendas[QUANTITY].sum())
    gross_margin = gross_profit / item_revenue * 100 if item_revenue else 0.0
    average_ticket = revenue / completed_orders if completed_orders else 0.0

    return CoreKpis(
        completed_orders=completed_orders,
        revenue=_round_money(revenue),
        item_revenue=_round_money(item_revenue),
        gross_profit=_round_money(gross_profit),
        gross_margin_percent=_round_percent(gross_margin),
        average_ticket=_round_money(average_ticket),
        units_sold=units_sold,
        shipping_total=_round_money(orders["Frete (R$)"].sum()),
        discount_total=_round_money(orders["Desconto Cupom (R$)"].sum()),
    ).as_dict()


def _growth_percent(current: float, previous: float) -> float | None:
    if previous == 0:
        return None
    return _round_percent((current - previous) / previous * 100)


def compare_periods(
    fato_vendas: pd.DataFrame,
    current_start: date,
    current_end: date,
    previous_start: date,
    previous_end: date,
) -> pd.DataFrame:
    """Compare governed KPIs between two date ranges."""

    current = calculate_core_kpis(
        filter_sales(fato_vendas, start_date=current_start, end_date=current_end)
    )
    previous = calculate_core_kpis(
        filter_sales(fato_vendas, start_date=previous_start, end_date=previous_end)
    )
    metric_labels = {
        "completed_orders": "Completed Orders",
        "revenue": "Order Revenue",
        "item_revenue": "Item Revenue",
        "gross_profit": "Gross Profit",
        "gross_margin_percent": "Gross Margin %",
        "average_ticket": "Average Ticket",
        "units_sold": "Units Sold",
        "shipping_total": "Shipping Total",
        "discount_total": "Discount Total",
    }
    rows = []
    for key, label in metric_labels.items():
        current_value = current[key]
        previous_value = previous[key]
        delta = (
            _round_money(float(current_value) - float(previous_value))
            if isinstance(current_value, float) or isinstance(previous_value, float)
            else int(current_value) - int(previous_value)
        )
        rows.append(
            {
                "metric": key,
                "label": label,
                "current": current_value,
                "previous": previous_value,
                "delta": delta,
                "growth_percent": _growth_percent(
                    float(current_value), float(previous_value)
                ),
            }
        )
    return pd.DataFrame(rows)


def customer_retention_summary(fato_vendas: pd.DataFrame) -> dict[str, float | int]:
    """Return repeat-customer KPIs from deduplicated completed orders."""

    orders = order_level_sales(fato_vendas)
    customers = orders.groupby("ID Cliente", as_index=False).agg(
        completed_orders=(ORDER_ID, "nunique"),
        revenue=(ORDER_TOTAL, "sum"),
        first_purchase=(DATE, "min"),
        last_purchase=(DATE, "max"),
    )
    active_customers = int(customers["ID Cliente"].nunique())
    repeat_customers = int((customers["completed_orders"] > 1).sum())
    revenue = float(customers["revenue"].sum())
    completed_orders = int(customers["completed_orders"].sum())

    return {
        "active_customers": active_customers,
        "repeat_customers": repeat_customers,
        "one_time_customers": active_customers - repeat_customers,
        "repeat_customer_rate_percent": _round_percent(
            repeat_customers / active_customers * 100 if active_customers else 0.0
        ),
        "orders_per_customer": _round_percent(
            completed_orders / active_customers if active_customers else 0.0
        ),
        "average_customer_revenue": _round_money(
            revenue / active_customers if active_customers else 0.0
        ),
    }


def top_customers(
    fato_vendas: pd.DataFrame,
    customers: pd.DataFrame | None = None,
    limit: int = 10,
) -> pd.DataFrame:
    """Rank customers by completed order revenue using deduplicated order totals."""

    orders = order_level_sales(fato_vendas)
    ranked = (
        orders.groupby(["ID Cliente", "Estado Cliente"], as_index=False)
        .agg(
            completed_orders=(ORDER_ID, "nunique"),
            revenue=(ORDER_TOTAL, "sum"),
            first_purchase=(DATE, "min"),
            last_purchase=(DATE, "max"),
        )
        .sort_values(
            ["revenue", "completed_orders", "ID Cliente"],
            ascending=[False, False, True],
        )
        .head(limit)
        .reset_index(drop=True)
    )
    ranked["average_ticket"] = ranked["revenue"] / ranked["completed_orders"]
    ranked["first_purchase"] = ranked["first_purchase"].dt.date.astype(str)
    ranked["last_purchase"] = ranked["last_purchase"].dt.date.astype(str)

    if customers is not None:
        profile_columns = ["ID Cliente", "Nome Cliente", "Email", "Estado", "Cidade"]
        missing = [column for column in profile_columns if column not in customers.columns]
        if missing:
            raise KeyError("Dimensão Clientes missing columns: " + ", ".join(missing))
        ranked = ranked.merge(customers[profile_columns], on="ID Cliente", how="left")
        ranked = ranked[
            [
                "ID Cliente",
                "Nome Cliente",
                "Email",
                "Estado",
                "Cidade",
                "completed_orders",
                "revenue",
                "average_ticket",
                "first_purchase",
                "last_purchase",
            ]
        ]

    return ranked.round({"revenue": 2, "average_ticket": 2})


def monthly_customer_cohorts(fato_vendas: pd.DataFrame) -> pd.DataFrame:
    """Build monthly customer cohorts from deduplicated completed orders."""

    orders = order_level_sales(fato_vendas)
    orders["order_month"] = orders[DATE].dt.to_period("M")
    first_month = (
        orders.groupby("ID Cliente")["order_month"]
        .min()
        .rename("cohort_month")
        .reset_index()
    )
    cohort_orders = orders.merge(first_month, on="ID Cliente", how="left")
    cohort_orders["months_since_first_purchase"] = (
        (cohort_orders["order_month"].dt.year - cohort_orders["cohort_month"].dt.year)
        * 12
        + cohort_orders["order_month"].dt.month
        - cohort_orders["cohort_month"].dt.month
    )
    grouped = (
        cohort_orders.groupby(
            ["cohort_month", "months_since_first_purchase"], as_index=False
        )
        .agg(
            active_customers=("ID Cliente", "nunique"),
            completed_orders=(ORDER_ID, "nunique"),
            revenue=(ORDER_TOTAL, "sum"),
        )
        .sort_values(["cohort_month", "months_since_first_purchase"])
    )
    grouped["cohort_month"] = grouped["cohort_month"].astype(str)
    return grouped.round({"revenue": 2})


def category_performance(fato_vendas: pd.DataFrame) -> pd.DataFrame:
    """Aggregate category revenue/profit using item-level fields."""

    grouped = (
        fato_vendas.groupby("Categoria", as_index=False)
        .agg(
            item_revenue=(ITEM_REVENUE, "sum"),
            gross_profit=(GROSS_PROFIT, "sum"),
            units_sold=(QUANTITY, "sum"),
        )
        .sort_values(["item_revenue", "units_sold", "Categoria"], ascending=[False, False, True])
    )
    grouped["gross_margin_percent"] = (
        grouped["gross_profit"] / grouped["item_revenue"] * 100
    ).round(2)
    return grouped.round({"item_revenue": 2, "gross_profit": 2})


def product_ranking(
    fato_vendas: pd.DataFrame,
    limit: int = 10,
    sort_by: str = "revenue",
) -> pd.DataFrame:
    """Return top products by item revenue, using item fields only."""

    if sort_by not in {"revenue", "units"}:
        raise ValueError("sort_by must be 'revenue' or 'units'")

    sort_columns = (
        ["units_sold", "item_revenue", "Produto"]
        if sort_by == "units"
        else ["item_revenue", "units_sold", "Produto"]
    )

    grouped = (
        fato_vendas.groupby(["Produto", "Categoria"], as_index=False)
        .agg(
            units_sold=(QUANTITY, "sum"),
            item_revenue=(ITEM_REVENUE, "sum"),
            gross_profit=(GROSS_PROFIT, "sum"),
        )
        .sort_values(
            sort_columns, ascending=[False, False, True]
        )
        .head(limit)
        .reset_index(drop=True)
    )
    grouped["gross_margin_percent"] = (
        grouped["gross_profit"] / grouped["item_revenue"] * 100
    ).round(2)
    return grouped.round({"item_revenue": 2, "gross_profit": 2})


def active_product_count(products: pd.DataFrame) -> int:
    """Count active catalog products from the raw product sheet."""

    return int((products["Ativo"] == "Sim").sum())


def monthly_revenue(fato_vendas: pd.DataFrame) -> pd.DataFrame:
    """Monthly completed order revenue with order totals deduplicated first."""

    orders = order_level_sales(fato_vendas)
    grouped = (
        orders.groupby("Mes", as_index=False)
        .agg(completed_orders=(ORDER_ID, "nunique"), revenue=(ORDER_TOTAL, "sum"))
        .sort_values("Mes")
    )
    grouped["average_ticket"] = grouped["revenue"] / grouped["completed_orders"]
    return grouped.round({"revenue": 2, "average_ticket": 2})


def monthly_units_sold(fato_vendas: pd.DataFrame) -> pd.DataFrame:
    """Monthly item demand from item-level fact rows."""

    df = fato_vendas.copy()
    df[DATE] = _purchase_datetime(df[DATE])
    df["Mes"] = df[DATE].dt.to_period("M").astype(str)
    return (
        df.groupby("Mes", as_index=False)
        .agg(units_sold=(QUANTITY, "sum"), item_revenue=(ITEM_REVENUE, "sum"))
        .sort_values("Mes")
        .round({"item_revenue": 2})
    )


def monthly_orders_by_status(purchases: pd.DataFrame) -> pd.DataFrame:
    """Monthly raw purchase counts by status, including pending pipeline."""

    df = purchases.copy()
    df["Data Compra"] = _purchase_datetime(df["Data Compra"])
    df["Mes"] = df["Data Compra"].dt.to_period("M").astype(str)
    return (
        df.groupby(["Mes", "Status"], as_index=False)
        .agg(orders=("ID", "nunique"), revenue=("Total (R$)", "sum"))
        .sort_values(["Mes", "Status"])
        .round({"revenue": 2})
    )


def monthly_gross_profit(fato_vendas: pd.DataFrame) -> pd.DataFrame:
    """Monthly gross profit from item-level profit fields."""

    df = fato_vendas.copy()
    df[DATE] = _purchase_datetime(df[DATE])
    df["Mes"] = df[DATE].dt.to_period("M").astype(str)
    grouped = (
        df.groupby("Mes", as_index=False)
        .agg(
            item_revenue=(ITEM_REVENUE, "sum"),
            gross_profit=(GROSS_PROFIT, "sum"),
            units_sold=(QUANTITY, "sum"),
        )
        .sort_values("Mes")
    )
    grouped["gross_margin_percent"] = (
        grouped["gross_profit"] / grouped["item_revenue"] * 100
    ).round(2)
    return grouped.round({"item_revenue": 2, "gross_profit": 2})


def revenue_profit_trend(fato_vendas: pd.DataFrame) -> pd.DataFrame:
    """Monthly item revenue and gross profit for profit-versus-revenue views."""

    return monthly_gross_profit(fato_vendas)[
        ["Mes", "item_revenue", "gross_profit", "gross_margin_percent"]
    ]


def shipping_discount_trend(fato_vendas: pd.DataFrame) -> pd.DataFrame:
    """Monthly order-level shipping and discount impact from deduplicated orders."""

    orders = order_level_sales(fato_vendas)
    return (
        orders.groupby("Mes", as_index=False)
        .agg(
            revenue=(ORDER_TOTAL, "sum"),
            shipping_total=("Frete (R$)", "sum"),
            discount_total=("Desconto Cupom (R$)", "sum"),
        )
        .sort_values("Mes")
        .round({"revenue": 2, "shipping_total": 2, "discount_total": 2})
    )


def category_trend(fato_vendas: pd.DataFrame) -> pd.DataFrame:
    """Monthly item revenue by category."""

    df = fato_vendas.copy()
    df[DATE] = _purchase_datetime(df[DATE])
    df["Mes"] = df[DATE].dt.to_period("M").astype(str)
    return (
        df.groupby(["Mes", "Categoria"], as_index=False)
        .agg(item_revenue=(ITEM_REVENUE, "sum"), units_sold=(QUANTITY, "sum"))
        .sort_values(["Mes", "Categoria"])
        .round({"item_revenue": 2})
    )


def product_trend(fato_vendas: pd.DataFrame, products: list[str] | None = None) -> pd.DataFrame:
    """Monthly item revenue and units by product."""

    df = fato_vendas.copy()
    if products:
        df = df.loc[df["Produto"].isin(products)]
    df[DATE] = _purchase_datetime(df[DATE])
    df["Mes"] = df[DATE].dt.to_period("M").astype(str)
    return (
        df.groupby(["Mes", "Produto"], as_index=False)
        .agg(item_revenue=(ITEM_REVENUE, "sum"), units_sold=(QUANTITY, "sum"))
        .sort_values(["Mes", "Produto"])
        .round({"item_revenue": 2})
    )


def revenue_by_state(fato_vendas: pd.DataFrame) -> pd.DataFrame:
    """State revenue from deduplicated order totals."""

    orders = order_level_sales(fato_vendas)
    return (
        orders.groupby("Estado Cliente", as_index=False)
        .agg(completed_orders=(ORDER_ID, "nunique"), revenue=(ORDER_TOTAL, "sum"))
        .sort_values(["revenue", "completed_orders", "Estado Cliente"], ascending=[False, False, True])
        .round({"revenue": 2})
    )


def state_revenue_trend(fato_vendas: pd.DataFrame) -> pd.DataFrame:
    """Monthly order-level revenue by customer state."""

    orders = order_level_sales(fato_vendas)
    return (
        orders.groupby(["Mes", "Estado Cliente"], as_index=False)
        .agg(completed_orders=(ORDER_ID, "nunique"), revenue=(ORDER_TOTAL, "sum"))
        .sort_values(["Mes", "Estado Cliente"])
        .round({"revenue": 2})
    )


def payment_method_summary(fato_vendas: pd.DataFrame) -> pd.DataFrame:
    """Payment mix from deduplicated order-level data."""

    orders = order_level_sales(fato_vendas)
    return (
        orders.groupby("Metodo Pagamento", as_index=False)
        .agg(completed_orders=(ORDER_ID, "nunique"), revenue=(ORDER_TOTAL, "sum"))
        .sort_values(["completed_orders", "revenue", "Metodo Pagamento"], ascending=[False, False, True])
        .round({"revenue": 2})
    )


def payment_method_trend(fato_vendas: pd.DataFrame) -> pd.DataFrame:
    """Monthly order-level payment method trend."""

    orders = order_level_sales(fato_vendas)
    return (
        orders.groupby(["Mes", "Metodo Pagamento"], as_index=False)
        .agg(completed_orders=(ORDER_ID, "nunique"), revenue=(ORDER_TOTAL, "sum"))
        .sort_values(["Mes", "Metodo Pagamento"])
        .round({"revenue": 2})
    )


def share_of_total(rows: pd.DataFrame, value_column: str, share_column: str = "share_percent") -> pd.DataFrame:
    """Add percent-of-total to a chart-ready table."""

    result = rows.copy()
    total = float(result[value_column].sum())
    result[share_column] = (
        result[value_column] / total * 100 if total else 0.0
    ).round(2)
    return result


def review_summary(reviews: pd.DataFrame) -> dict[str, float | int]:
    """Return simple review KPIs."""

    if reviews.empty:
        return {"review_count": 0, "average_rating": 0.0}
    return {
        "review_count": int(len(reviews)),
        "average_rating": round(float(reviews["Nota"].mean()), 2),
    }


def rating_distribution(reviews: pd.DataFrame) -> pd.DataFrame:
    """Count reviews by rating from one to five stars."""

    distribution = (
        reviews["Nota"]
        .value_counts()
        .rename_axis("rating")
        .reset_index(name="review_count")
        .sort_values("rating")
    )
    return distribution


def product_review_table(reviews: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """Rank products by review quality signals."""

    product_names = products[["ID", "Nome", "Categoria"]].rename(
        columns={"ID": "ID Produto", "Nome": "Produto"}
    )
    grouped = (
        reviews.groupby("ID Produto", as_index=False)
        .agg(review_count=("ID", "count"), average_rating=("Nota", "mean"))
        .merge(product_names, on="ID Produto", how="left")
        .sort_values(["average_rating", "review_count", "Produto"], ascending=[False, False, True])
        .reset_index(drop=True)
    )
    return grouped[
        ["ID Produto", "Produto", "Categoria", "review_count", "average_rating"]
    ].round({"average_rating": 2})


def customer_geography_table(
    fato_vendas: pd.DataFrame,
    customers: pd.DataFrame,
) -> pd.DataFrame:
    """Return order-level sales by customer state and city."""

    orders = order_level_sales(fato_vendas)
    geo = customers[["ID Cliente", "Estado", "Cidade"]]
    table = orders.merge(geo, on="ID Cliente", how="left")
    return (
        table.groupby(["Estado", "Cidade"], as_index=False)
        .agg(customers=("ID Cliente", "nunique"), completed_orders=(ORDER_ID, "nunique"), revenue=(ORDER_TOTAL, "sum"))
        .sort_values(["revenue", "completed_orders", "Estado", "Cidade"], ascending=[False, False, True, True])
        .round({"revenue": 2})
    )


def cart_summary(carts: pd.DataFrame, cart_items: pd.DataFrame) -> dict[str, float | int]:
    """Return cart counts and item subtotal value."""

    status_counts = carts["Status"].value_counts()
    return {
        "open_carts": int(status_counts.get("open", 0)),
        "abandoned_carts": int(status_counts.get("abandoned", 0)),
        "cart_item_value": _round_money(cart_items["Subtotal (R$)"].sum()),
    }


def cart_status_summary(carts: pd.DataFrame, cart_items: pd.DataFrame) -> pd.DataFrame:
    """Summarize cart count and item value by cart status."""

    item_totals = (
        cart_items.groupby("ID Carrinho", as_index=False)
        .agg(item_count=("ID", "count"), cart_value=("Subtotal (R$)", "sum"))
    )
    merged = carts.merge(item_totals, left_on="ID", right_on="ID Carrinho", how="left")
    merged[["item_count", "cart_value"]] = merged[["item_count", "cart_value"]].fillna(0)
    summary = (
        merged.groupby("Status", as_index=False)
        .agg(carts=("ID", "count"), items=("item_count", "sum"), cart_value=("cart_value", "sum"))
        .sort_values(["cart_value", "carts", "Status"], ascending=[False, False, True])
    )
    return summary.round({"cart_value": 2})


def cart_recovery_table(
    carts: pd.DataFrame,
    cart_items: pd.DataFrame,
    users: pd.DataFrame,
    limit: int = 15,
) -> pd.DataFrame:
    """Return high-value open/abandoned carts with customer context."""

    item_totals = (
        cart_items.groupby("ID Carrinho", as_index=False)
        .agg(item_count=("ID", "count"), units=("Quantidade", "sum"), subtotal=("Subtotal (R$)", "sum"))
    )
    customers = users[["ID", "Nome", "Email", "Estado", "Cidade"]].rename(
        columns={"ID": "ID Cliente"}
    )
    table = (
        carts.merge(item_totals, left_on="ID", right_on="ID Carrinho", how="left")
        .merge(customers, on="ID Cliente", how="left")
    )
    table[["item_count", "units", "subtotal"]] = table[
        ["item_count", "units", "subtotal"]
    ].fillna(0)
    columns = [
        "ID",
        "Status",
        "Nome",
        "Email",
        "Estado",
        "Cidade",
        "item_count",
        "units",
        "subtotal",
    ]
    return (
        table[columns]
        .sort_values(["subtotal", "item_count", "ID"], ascending=[False, False, True])
        .head(limit)
        .round({"subtotal": 2})
        .reset_index(drop=True)
    )
