"""Streamlit dashboard for the MEI commerce analytics workbook."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.charts import (
    active_product_count,
    calculate_core_kpis,
    cart_summary,
    cart_recovery_table,
    cart_status_summary,
    category_trend,
    category_performance,
    compare_periods,
    customer_retention_summary,
    filter_sales,
    customer_geography_table,
    monthly_customer_cohorts,
    monthly_gross_profit,
    monthly_orders_by_status,
    monthly_revenue,
    monthly_units_sold,
    payment_method_summary,
    payment_method_trend,
    product_review_table,
    product_ranking,
    rating_distribution,
    revenue_by_state,
    revenue_profit_trend,
    review_summary,
    share_of_total,
    shipping_discount_trend,
    state_revenue_trend,
    top_customers,
)
from app.business_qa import answer_from_workbook
from app.data_loader import DEFAULT_WORKBOOK_PATH, load_workbook
from app.gemini_client import GeminiConfigurationError, answer_business_question
from app.reporting import build_markdown_report_from_sheets, write_markdown_report
from app.ui import (
    apply_base_styles,
    render_dashboard_header,
    render_section_title,
    render_sidebar_divider,
    render_sidebar_filter_panel_intro,
    render_sidebar_filter_summary,
)


def _format_brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


PLOT_LABELS = {
    "active_customers": "Clientes ativos",
    "average_rating": "Avaliação média",
    "average_ticket": "Ticket médio",
    "cart_value": "Valor do carrinho",
    "carts": "Carrinhos",
    "cohort_month": "Mês da coorte",
    "completed_orders": "Pedidos concluídos",
    "current": "Atual",
    "delta": "Variação",
    "discount_total": "Desconto total",
    "gross_margin_percent": "Margem bruta (%)",
    "gross_profit": "Lucro bruto",
    "growth_percent": "Crescimento (%)",
    "item_count": "Itens",
    "item_revenue": "Receita item",
    "items": "Itens",
    "label": "Métrica",
    "Mes": "Mês",
    "Metodo Pagamento": "Método de pagamento",
    "metric": "Código",
    "months_since_first_purchase": "Meses desde a primeira compra",
    "orders": "Pedidos",
    "previous": "Anterior",
    "rating": "Nota",
    "revenue": "Receita",
    "review_count": "Avaliações",
    "share_percent": "Participação (%)",
    "shipping_total": "Frete total",
    "Status": "Status",
    "units": "Unidades",
    "units_sold": "Unidades vendidas",
    "value": "Valor",
    "variable": "Indicador",
}

TABLE_LABELS = {
    **PLOT_LABELS,
    "average_customer_revenue": "Receita média por cliente",
    "Cidade": "Cidade",
    "cohort_month": "Mês da coorte",
    "Email": "Email",
    "Estado": "Estado",
    "Estado Cliente": "Estado do cliente",
    "first_purchase": "Primeira compra",
    "ID": "ID",
    "ID Cliente": "ID Cliente",
    "ID Produto": "ID Produto",
    "last_purchase": "Última compra",
    "Nome": "Nome",
    "Nome Cliente": "Nome do cliente",
    "one_time_customers": "Clientes de compra única",
    "Produto": "Produto",
    "repeat_customer_rate_percent": "Taxa de recorrência (%)",
    "repeat_customers": "Clientes recorrentes",
    "subtotal": "Subtotal",
}

METRIC_LABELS = {
    "average_ticket": "Ticket médio",
    "completed_orders": "Pedidos concluídos",
    "discount_total": "Desconto total",
    "gross_margin_percent": "Margem bruta (%)",
    "gross_profit": "Lucro bruto",
    "item_revenue": "Receita item",
    "revenue": "Receita de pedidos",
    "shipping_total": "Frete total",
    "units_sold": "Unidades vendidas",
}

PAYMENT_LABELS = {
    "credit_card": "Cartão de crédito",
    "debit_card": "Cartão de débito",
    "pix": "Pix",
}

CATEGORY_LABELS = {
    "alimentos": "Alimentos",
    "beleza": "Beleza",
    "casa": "Casa",
    "eletronicos": "Eletrônicos",
    "papelaria": "Papelaria",
    "vestuario": "Vestuário",
}

STATUS_LABELS = {
    "abandoned": "Abandonado",
    "checked_out": "Finalizado",
    "open": "Aberto",
    "paid": "Pago",
    "pending": "Pendente",
    "shipped": "Enviado",
}

KPI_PERIOD_OPTIONS = ["Mês", "Trimestre", "Semestre", "Ano", "Todos os tempos"]

FILTER_STATE_KEYS = [
    "global_date_range",
    "global_states",
    "global_payments",
    "global_categories",
]


def _localize_values(rows: pd.DataFrame, column: str, labels: dict[str, str]) -> pd.DataFrame:
    localized = rows.copy()
    if column in localized.columns:
        localized[column] = localized[column].replace(labels)
    return localized


def _display_table(rows: pd.DataFrame) -> pd.DataFrame:
    display = rows.copy()
    if "label" in display.columns and "metric" in display.columns:
        display["label"] = display["metric"].map(METRIC_LABELS).fillna(display["label"])
    display = _localize_values(display, "Metodo Pagamento", PAYMENT_LABELS)
    display = _localize_values(display, "Status", STATUS_LABELS)
    return display.rename(columns=TABLE_LABELS)


def _display_list(values: list[str], labels: dict[str, str] | None = None) -> str:
    if not values:
        return "Todos"
    display_values = [labels.get(value, value) if labels else value for value in values]
    return ", ".join(display_values)


def _kpi_period_bounds(fato_vendas: pd.DataFrame, period: str) -> tuple[date, date]:
    dates = pd.to_datetime(fato_vendas["Data Compra"], utc=True).dt.date
    end_date = dates.max()
    if period == "Todos os tempos":
        return dates.min(), end_date

    if period == "Mês":
        start_date = end_date.replace(day=1)
    elif period == "Trimestre":
        start_month = ((end_date.month - 1) // 3) * 3 + 1
        start_date = end_date.replace(month=start_month, day=1)
    elif period == "Semestre":
        start_month = 1 if end_date.month <= 6 else 7
        start_date = end_date.replace(month=start_month, day=1)
    elif period == "Ano":
        start_date = end_date.replace(month=1, day=1)
    else:
        raise ValueError(f"Unsupported KPI period: {period}")

    return start_date, end_date


def _print_cli_report(path: Path = DEFAULT_WORKBOOK_PATH) -> None:
    sheets = load_workbook(path)
    fato = sheets["Fato Vendas"]
    kpis = calculate_core_kpis(fato)
    print("MEI Commerce AI Analytics")
    print(f"Workbook: {path}")
    print(f"Pedidos concluídos: {kpis['completed_orders']}")
    print(f"Receita de pedidos: {_format_brl(kpis['revenue'])}")
    print(f"Receita item: {_format_brl(kpis['item_revenue'])}")
    print(f"Lucro bruto: {_format_brl(kpis['gross_profit'])}")
    print(f"Margem bruta: {kpis['gross_margin_percent']:.2f}%")
    print(f"Ticket médio: {_format_brl(kpis['average_ticket'])}")
    print(f"Unidades vendidas: {kpis['units_sold']}")


def _filter_note(
    start_date,
    end_date,
    states: list[str],
    payments: list[str],
    categories: list[str],
) -> str:
    return "\n".join(
        [
            f"- Período: {start_date} a {end_date}",
            f"- Estados: {', '.join(states) if states else 'todos'}",
            f"- Pagamentos: {', '.join(payments) if payments else 'todos'}",
            f"- Categorias: {', '.join(categories) if categories else 'todas'}",
        ]
    )


def _run_streamlit() -> None:
    import plotly.express as px
    import streamlit as st

    st.set_page_config(
        page_title="MEI Commerce AI Analytics",
        page_icon="📊",
        layout="wide",
    )
    apply_base_styles()

    try:
        sheets = load_workbook(DEFAULT_WORKBOOK_PATH)
    except Exception as exc:
        st.error(f"Não foi possível carregar a planilha: {exc}")
        st.stop()

    fato = sheets["Fato Vendas"]
    full_dates = pd.to_datetime(fato["Data Compra"], utc=True).dt.date
    render_dashboard_header(
        title="MEI Commerce AI Analytics",
        description=(
            "Painel executivo para acompanhar receita, margem, clientes e operação "
            "a partir da planilha analítica governada."
        ),
        status_items=[
            "Base carregada",
            f"{full_dates.min()} a {full_dates.max()}",
            f"{len(fato):,} linhas de venda".replace(",", "."),
        ],
        actions=[
            DEFAULT_WORKBOOK_PATH.name,
            "Knowledge base ativa",
        ],
    )

    def reset_global_filters() -> None:
        st.session_state["global_date_range"] = (full_dates.min(), full_dates.max())
        st.session_state["global_states"] = []
        st.session_state["global_payments"] = []
        st.session_state["global_categories"] = []

    for filter_key in FILTER_STATE_KEYS:
        if filter_key not in st.session_state:
            st.session_state[filter_key] = (
                (full_dates.min(), full_dates.max()) if filter_key == "global_date_range" else []
            )

    state_options = sorted(fato["Estado Cliente"].dropna().unique())
    payment_options = sorted(fato["Metodo Pagamento"].dropna().unique())
    category_options = sorted(fato["Categoria"].dropna().unique())
    render_sidebar_filter_panel_intro()
    date_range = st.sidebar.date_input(
        "Período",
        min_value=full_dates.min(),
        max_value=full_dates.max(),
        key="global_date_range",
    )
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = full_dates.min()
        end_date = full_dates.max()

    render_sidebar_divider()
    selected_states = st.sidebar.multiselect(
        "Estados",
        state_options,
        key="global_states",
    )
    render_sidebar_divider()
    selected_payments = st.sidebar.multiselect(
        "Métodos de pagamento",
        payment_options,
        format_func=lambda payment: PAYMENT_LABELS.get(payment, payment),
        key="global_payments",
    )
    render_sidebar_divider()
    selected_categories = st.sidebar.multiselect(
        "Categorias",
        category_options,
        format_func=lambda category: CATEGORY_LABELS.get(category, category),
        key="global_categories",
    )
    render_sidebar_filter_summary(
        [
            ("Período", f"{start_date} a {end_date}"),
            ("Estados", _display_list(selected_states)),
            ("Pagamentos", _display_list(selected_payments, PAYMENT_LABELS)),
            ("Categorias", _display_list(selected_categories, CATEGORY_LABELS)),
        ]
    )
    st.sidebar.button("Resetar filtros", on_click=reset_global_filters, use_container_width=True)

    fato = filter_sales(
        fato,
        start_date=start_date,
        end_date=end_date,
        categories=selected_categories,
        states=selected_states,
        payment_methods=selected_payments,
    )
    if fato.empty:
        st.warning("Nenhuma venda encontrada para os filtros selecionados.")
        st.stop()

    reviews = review_summary(sheets["Reviews"])
    carts = cart_summary(sheets["Carts"], sheets["Cart Items"])
    active_products = active_product_count(sheets["Products"])

    render_section_title(
        "KPIs principais",
        "Indicadores calculados com as regras governadas da base analítica.",
    )
    if "kpi_period" not in st.session_state:
        st.session_state["kpi_period"] = "Todos os tempos"

    def set_kpi_period(period: str) -> None:
        st.session_state["kpi_period"] = period

    period_buttons = st.columns(len(KPI_PERIOD_OPTIONS))
    for period_column, period_option in zip(period_buttons, KPI_PERIOD_OPTIONS):
        period_column.button(
            period_option,
            key=f"kpi_period_{period_option}",
            on_click=set_kpi_period,
            args=(period_option,),
            type="primary" if st.session_state["kpi_period"] == period_option else "secondary",
            use_container_width=True,
        )

    kpi_period = st.session_state["kpi_period"]
    kpi_start_date, kpi_end_date = _kpi_period_bounds(fato, kpi_period)
    kpi_fato = filter_sales(fato, start_date=kpi_start_date, end_date=kpi_end_date)
    kpis = calculate_core_kpis(kpi_fato)
    st.caption(f"Visão dos KPIs: {kpi_start_date} a {kpi_end_date}")
    report_text = build_markdown_report_from_sheets(
        sheets,
        fato_override=kpi_fato,
        filter_note=_filter_note(
            kpi_start_date,
            kpi_end_date,
            selected_states,
            selected_payments,
            selected_categories,
        ),
    )
    st.download_button(
        "Baixar relatório Markdown",
        data=report_text,
        file_name="mei_commerce_report.md",
        mime="text/markdown",
    )
    first_row = st.columns(4)
    first_row[0].metric("Pedidos concluídos", f"{kpis['completed_orders']:,}".replace(",", "."))
    first_row[1].metric("Receita de pedidos", _format_brl(kpis["revenue"]))
    first_row[2].metric("Ticket médio", _format_brl(kpis["average_ticket"]))
    first_row[3].metric("Unidades vendidas", f"{kpis['units_sold']:,}".replace(",", "."))

    second_row = st.columns(4)
    second_row[0].metric("Receita item", _format_brl(kpis["item_revenue"]))
    second_row[1].metric("Lucro bruto", _format_brl(kpis["gross_profit"]))
    second_row[2].metric("Margem bruta", f"{kpis['gross_margin_percent']:.2f}%")
    second_row[3].metric("Avaliação média", f"{reviews['average_rating']:.2f}")

    third_row = st.columns(4)
    third_row[0].metric("Produtos ativos", active_products)
    third_row[1].metric("Carrinhos abertos", carts["open_carts"])
    third_row[2].metric("Carrinhos abandonados", carts["abandoned_carts"])
    third_row[3].metric("Valor em carrinhos", _format_brl(carts["cart_item_value"]))

    with st.expander("Contrato das métricas", expanded=False):
        st.markdown(
            """
- Receita de pedidos deduplica `Fato Vendas` por `ID Venda` antes de somar `Total do Pedido (R$)`.
- Produto e categoria usam `Subtotal Item (R$)`, `Quantidade Item` e `Lucro Bruto Item (R$)`.
- `Fato Vendas` contém apenas pedidos concluídos (`paid` e `shipped`).
- Receita de pedido inclui frete e subtrai desconto; receita item não inclui frete nem desconto.
            """.strip()
        )
        if selected_categories:
            st.info(
                "Com filtro de categoria, KPIs de pedido representam pedidos que contêm a categoria selecionada. "
                "Receita de categoria/produto continua usando `Subtotal Item (R$)`."
            )

    tab_sales, tab_compare, tab_products, tab_customers, tab_ops, tab_ai = st.tabs(
        ["Vendas", "Comparação", "Produtos", "Clientes", "Operação", "AI QA"]
    )

    with tab_sales:
        monthly = monthly_revenue(fato)
        units = monthly_units_sold(fato)
        profit = monthly_gross_profit(fato)
        profit_trend = revenue_profit_trend(fato)
        shipping_discount = shipping_discount_trend(fato)
        states = revenue_by_state(fato)
        state_trend = state_revenue_trend(fato)
        payments = payment_method_summary(fato)
        payment_trend = payment_method_trend(fato)
        raw_status = monthly_orders_by_status(sheets["Purchases"])
        payments_display = _localize_values(payments, "Metodo Pagamento", PAYMENT_LABELS)
        payment_trend_display = _localize_values(payment_trend, "Metodo Pagamento", PAYMENT_LABELS)
        raw_status_display = _localize_values(raw_status, "Status", STATUS_LABELS)

        st.plotly_chart(
            px.line(
                monthly,
                x="Mes",
                y="revenue",
                markers=True,
                title="Receita mensal de pedidos concluídos",
                labels=PLOT_LABELS,
            ),
            width="stretch",
        )
        col_a, col_b = st.columns(2)
        col_a.plotly_chart(
            px.line(
                units,
                x="Mes",
                y="units_sold",
                markers=True,
                title="Unidades vendidas por mês",
                labels=PLOT_LABELS,
            ),
            width="stretch",
        )
        col_b.plotly_chart(
            px.line(
                profit_trend,
                x="Mes",
                y=["item_revenue", "gross_profit"],
                markers=True,
                title="Receita item versus lucro bruto",
                labels=PLOT_LABELS,
            ),
            width="stretch",
        )
        col_a, col_b = st.columns(2)
        col_a.plotly_chart(
            px.bar(
                states,
                x="Estado Cliente",
                y="revenue",
                title="Receita por estado",
                labels=PLOT_LABELS,
            ),
            width="stretch",
        )
        col_b.plotly_chart(
            px.bar(
                payments_display,
                x="Metodo Pagamento",
                y="completed_orders",
                title="Pedidos por método de pagamento",
                labels=PLOT_LABELS,
            ),
            width="stretch",
        )
        col_a, col_b = st.columns(2)
        col_a.plotly_chart(
            px.line(
                shipping_discount,
                x="Mes",
                y=["shipping_total", "discount_total"],
                markers=True,
                title="Frete e desconto por mês",
                labels=PLOT_LABELS,
            ),
            width="stretch",
        )
        col_b.plotly_chart(
            px.bar(
                raw_status_display,
                x="Mes",
                y="orders",
                color="Status",
                title="Pedidos brutos por status",
                labels=PLOT_LABELS,
            ),
            width="stretch",
        )
        with st.expander("Tendências por estado e pagamento", expanded=False):
            col_a, col_b = st.columns(2)
            col_a.plotly_chart(
                px.line(
                    state_trend,
                    x="Mes",
                    y="revenue",
                    color="Estado Cliente",
                    title="Receita por estado ao longo do tempo",
                    labels=PLOT_LABELS,
                ),
                width="stretch",
            )
            col_b.plotly_chart(
                px.line(
                    payment_trend_display,
                    x="Mes",
                    y="completed_orders",
                    color="Metodo Pagamento",
                    title="Pedidos por pagamento ao longo do tempo",
                    labels=PLOT_LABELS,
                ),
                width="stretch",
            )
        st.dataframe(_display_table(profit), width="stretch", hide_index=True)

    with tab_compare:
        st.caption("Comparação período contra período usando as mesmas regras de grão dos KPIs.")
        default_current_start = pd.Timestamp(full_dates.max()).replace(day=1).date()
        default_previous_end = default_current_start - pd.Timedelta(days=1)
        default_previous_start = pd.Timestamp(default_previous_end).replace(day=1).date()
        current_period = st.date_input(
            "Período atual",
            value=(default_current_start, full_dates.max()),
            min_value=full_dates.min(),
            max_value=full_dates.max(),
            key="comparison_current_period",
        )
        previous_period = st.date_input(
            "Período anterior",
            value=(default_previous_start, default_previous_end),
            min_value=full_dates.min(),
            max_value=full_dates.max(),
            key="comparison_previous_period",
        )
        if (
            isinstance(current_period, tuple)
            and len(current_period) == 2
            and isinstance(previous_period, tuple)
            and len(previous_period) == 2
        ):
            comparison = compare_periods(
                sheets["Fato Vendas"],
                current_start=current_period[0],
                current_end=current_period[1],
                previous_start=previous_period[0],
                previous_end=previous_period[1],
            )
            st.dataframe(_display_table(comparison), width="stretch", hide_index=True)
            comparison_chart = comparison.copy()
            comparison_chart["label"] = (
                comparison_chart["metric"].map(METRIC_LABELS).fillna(comparison_chart["label"])
            )
            st.plotly_chart(
                px.bar(
                    comparison_chart,
                    x="label",
                    y="delta",
                    title="Variação absoluta por métrica",
                    labels=PLOT_LABELS,
                ),
                width="stretch",
            )
        else:
            st.warning("Selecione dois intervalos completos para comparar.")

    with tab_products:
        categories = category_performance(fato)
        products = product_ranking(fato, limit=12)
        products_by_units = product_ranking(fato, limit=12, sort_by="units")
        category_share = share_of_total(categories, "item_revenue")
        category_monthly = category_trend(fato)
        col_a, col_b = st.columns(2)
        col_a.plotly_chart(
            px.bar(
                categories,
                x="Categoria",
                y="item_revenue",
                title="Receita item por categoria",
                labels=PLOT_LABELS,
            ),
            width="stretch",
        )
        col_b.plotly_chart(
            px.bar(
                categories,
                x="Categoria",
                y="gross_profit",
                title="Lucro bruto por categoria",
                labels=PLOT_LABELS,
            ),
            width="stretch",
        )
        col_a, col_b = st.columns(2)
        col_a.plotly_chart(
            px.bar(
                categories.sort_values("gross_margin_percent", ascending=False),
                x="Categoria",
                y="gross_margin_percent",
                title="Margem por categoria",
                labels=PLOT_LABELS,
            ),
            width="stretch",
        )
        col_b.plotly_chart(
            px.bar(
                products_by_units,
                x="Produto",
                y="units_sold",
                title="Top produtos por unidades",
                labels=PLOT_LABELS,
            ),
            width="stretch",
        )
        col_a, col_b = st.columns(2)
        col_a.plotly_chart(
            px.pie(
                category_share,
                names="Categoria",
                values="item_revenue",
                hole=0.45,
                title="Share de receita item por categoria",
                labels=PLOT_LABELS,
            ),
            width="stretch",
        )
        col_b.plotly_chart(
            px.line(
                category_monthly,
                x="Mes",
                y="item_revenue",
                color="Categoria",
                title="Tendência mensal por categoria",
                labels=PLOT_LABELS,
            ),
            width="stretch",
        )
        st.dataframe(_display_table(products), width="stretch", hide_index=True)

    with tab_customers:
        retention = customer_retention_summary(fato)
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("Clientes ativos", retention["active_customers"])
        col_b.metric("Clientes recorrentes", retention["repeat_customers"])
        col_c.metric(
            "Taxa recorrente",
            f"{retention['repeat_customer_rate_percent']:.2f}%",
        )
        col_d.metric(
            "Receita média/cliente",
            _format_brl(retention["average_customer_revenue"]),
        )
        st.caption(
            "Retenção usa pedidos concluídos deduplicados por `ID Venda` e agrupados por `ID Cliente`."
        )
        st.dataframe(
            _display_table(top_customers(fato, sheets["Dimensão Clientes"], limit=15)),
            width="stretch",
            hide_index=True,
        )
        st.dataframe(
            _display_table(customer_geography_table(fato, sheets["Dimensão Clientes"]).head(15)),
            width="stretch",
            hide_index=True,
        )
        cohorts = monthly_customer_cohorts(fato)
        st.plotly_chart(
            px.line(
                cohorts,
                x="months_since_first_purchase",
                y="active_customers",
                color="cohort_month",
                markers=True,
                title="Clientes ativos por coorte mensal",
                labels=PLOT_LABELS,
            ),
            width="stretch",
        )
        st.plotly_chart(
            px.bar(
                cohorts,
                x="months_since_first_purchase",
                y="active_customers",
                color="cohort_month",
                title="Clientes ativos por coorte",
                labels=PLOT_LABELS,
            ),
            width="stretch",
        )

    with tab_ops:
        cart_status = cart_status_summary(sheets["Carts"], sheets["Cart Items"])
        rating_counts = rating_distribution(sheets["Reviews"])
        cart_share = share_of_total(cart_status, "carts")
        rating_share = share_of_total(rating_counts, "review_count")
        payment_share = share_of_total(payment_method_summary(fato), "completed_orders")
        cart_status_display = _localize_values(cart_status, "Status", STATUS_LABELS)
        cart_share_display = _localize_values(cart_share, "Status", STATUS_LABELS)
        payment_share_display = _localize_values(payment_share, "Metodo Pagamento", PAYMENT_LABELS)
        col_a, col_b = st.columns(2)
        col_a.plotly_chart(
            px.bar(
                cart_status_display,
                x="Status",
                y="carts",
                title="Carrinhos por status",
                labels=PLOT_LABELS,
            ),
            width="stretch",
        )
        col_b.plotly_chart(
            px.bar(
                cart_status_display,
                x="Status",
                y="cart_value",
                title="Valor de carrinhos por status",
                labels=PLOT_LABELS,
            ),
            width="stretch",
        )
        col_a, col_b = st.columns(2)
        col_a.plotly_chart(
            px.pie(
                payment_share_display,
                names="Metodo Pagamento",
                values="completed_orders",
                hole=0.45,
                title="Share de pedidos por pagamento",
                labels=PLOT_LABELS,
            ),
            width="stretch",
        )
        col_b.plotly_chart(
            px.bar(
                rating_counts,
                x="rating",
                y="review_count",
                title="Distribuição de avaliações",
                labels=PLOT_LABELS,
            ),
            width="stretch",
        )
        col_a, col_b = st.columns(2)
        col_a.plotly_chart(
            px.pie(
                rating_share,
                names="rating",
                values="review_count",
                hole=0.45,
                title="Share de avaliações",
                labels=PLOT_LABELS,
            ),
            width="stretch",
        )
        col_b.plotly_chart(
            px.pie(
                cart_share_display,
                names="Status",
                values="carts",
                hole=0.45,
                title="Share de carrinhos",
                labels=PLOT_LABELS,
            ),
            width="stretch",
        )
        st.dataframe(
            _display_table(product_review_table(sheets["Reviews"], sheets["Products"]).head(15)),
            width="stretch",
            hide_index=True,
        )
        st.dataframe(
            _display_table(cart_recovery_table(sheets["Carts"], sheets["Cart Items"], sheets["Users"])),
            width="stretch",
            hide_index=True,
        )

    with tab_ai:
        st.caption("Respostas locais usam fórmulas governadas. Gemini é opcional.")
        question = st.text_area(
            "Pergunta de negócio",
            placeholder="Ex.: Qual categoria gera mais lucro bruto?",
        )
        use_gemini = st.toggle("Usar Gemini quando configurado", value=False)
        if st.button("Responder", disabled=not question.strip()):
            local_answer = answer_from_workbook(question, sheets)
            st.markdown(local_answer)
            if use_gemini:
                try:
                    answer = answer_business_question(question, kpis)
                except GeminiConfigurationError as exc:
                    st.warning(str(exc))
                except Exception as exc:
                    st.error(f"Erro ao consultar Gemini: {exc}")
                else:
                    st.divider()
                    st.markdown(answer)


def main() -> None:
    if "--cli" in sys.argv:
        _print_cli_report()
        return
    if "--export-report" in sys.argv:
        output_index = sys.argv.index("--export-report") + 1
        output_path = (
            Path(sys.argv[output_index])
            if output_index < len(sys.argv)
            else Path("reports/mei_commerce_report.md")
        )
        path = write_markdown_report(output_path)
        print(f"report={path}")
        return

    try:
        _run_streamlit()
    except ModuleNotFoundError:
        _print_cli_report()


if __name__ == "__main__":
    main()
