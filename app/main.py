"""Streamlit dashboard for the MEI commerce analytics workbook."""

from __future__ import annotations

from datetime import date
from importlib.util import find_spec
import os
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
from app.gemini_client import GeminiConfigurationError, answer_business_question, load_env_file
from app.reporting import build_markdown_report_from_sheets, write_markdown_report
from app.ui import (
    apply_base_styles,
    apply_plotly_theme,
    render_dashboard_header,
    render_ai_empty_state,
    render_ai_message,
    render_ai_status,
    render_control_label,
    render_empty_filter_state,
    render_insight_callout,
    render_kpi_groups,
    render_period_comparison_summary,
    render_period_selector,
    render_report_export_panel,
    render_section_title,
    render_sidebar_divider,
    render_sidebar_filter_panel_intro,
    render_sidebar_filter_summary,
    render_table,
)


def _format_brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


PLOT_LABELS = {
    "active_customers": "Clientes ativos",
    "average_rating": "Avaliação média",
    "average_ticket": "Ticket médio",
    "cart_value": "Valor do carrinho",
    "carts": "Carrinhos",
    "Categoria": "Categoria",
    "cohort_month": "Mês da coorte",
    "completed_orders": "Pedidos concluídos",
    "current": "Atual",
    "delta": "Variação",
    "discount_total": "Desconto total",
    "Estado Cliente": "Estado do cliente",
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
    "customers": "Clientes ativos",
    "Email": "Email",
    "Estado": "Estado",
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
    "subtotal": "Valor do carrinho",
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
ANALYTICS_CHART_HEIGHT = 380
ANALYTICS_TABLE_HEIGHT = 360

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


def _gemini_is_ready() -> bool:
    load_env_file()
    return bool(os.getenv("GEMINI_API_KEY")) and find_spec("google.generativeai") is not None


def _format_chart(
    fig,
    *,
    currency: bool = False,
    percent: bool = False,
    count: bool = False,
    height: int = ANALYTICS_CHART_HEIGHT,
    x_tick_angle: int | None = None,
    y_tick_angle: int | None = None,
    legend_orientation: str = "h",
    margin: dict[str, int] | None = None,
):
    return apply_plotly_theme(
        fig,
        currency_axes=("yaxis",) if currency else (),
        percent_axes=("yaxis",) if percent else (),
        count_axes=("yaxis",) if count else (),
        height=height,
        x_tick_angle=x_tick_angle,
        y_tick_angle=y_tick_angle,
        legend_orientation=legend_orientation,
        margin=margin,
    )


def _format_horizontal_chart(
    fig,
    *,
    currency: bool = False,
    percent: bool = False,
    count: bool = False,
    height: int = ANALYTICS_CHART_HEIGHT,
    legend_orientation: str = "h",
    margin: dict[str, int] | None = None,
):
    return apply_plotly_theme(
        fig,
        currency_axes=("xaxis",) if currency else (),
        percent_axes=("xaxis",) if percent else (),
        count_axes=("xaxis",) if count else (),
        height=height,
        legend_orientation=legend_orientation,
        margin=margin,
    )


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

    @st.cache_data(show_spinner="Carregando planilha governada...")
    def load_streamlit_workbook(path: str) -> dict[str, pd.DataFrame]:
        return load_workbook(Path(path))

    st.set_page_config(
        page_title="MEI Commerce AI Analytics",
        page_icon="📊",
        layout="wide",
    )
    apply_base_styles()

    try:
        sheets = load_streamlit_workbook(str(DEFAULT_WORKBOOK_PATH))
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
        render_empty_filter_state(
            period=f"{start_date} a {end_date}",
            states=_display_list(selected_states),
            payments=_display_list(selected_payments, PAYMENT_LABELS),
            categories=_display_list(selected_categories, CATEGORY_LABELS),
        )
        st.stop()

    reviews = review_summary(sheets["Reviews"])
    carts = cart_summary(sheets["Carts"], sheets["Cart Items"])
    active_products = active_product_count(sheets["Products"])
    payment_summary = payment_method_summary(fato)

    render_section_title(
        "KPIs principais",
        "Indicadores calculados com as regras governadas da base analítica.",
    )
    if "kpi_period" not in st.session_state:
        st.session_state["kpi_period"] = "Todos os tempos"
    if st.session_state["kpi_period"] not in KPI_PERIOD_OPTIONS:
        st.session_state["kpi_period"] = "Todos os tempos"

    period_column, report_column = st.columns([4, 1.45])
    with period_column:
        render_period_selector(
            label="Visão dos KPIs",
            options=KPI_PERIOD_OPTIONS,
            key="kpi_period",
        )

    kpi_period = st.session_state["kpi_period"]
    kpi_start_date, kpi_end_date = _kpi_period_bounds(fato, kpi_period)
    kpi_fato = filter_sales(fato, start_date=kpi_start_date, end_date=kpi_end_date)
    kpis = calculate_core_kpis(kpi_fato)
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
    with report_column:
        render_report_export_panel(
            period=f"{kpi_start_date} a {kpi_end_date}",
            report_text=report_text,
            file_name="mei_commerce_report.md",
        )
    st.caption(f"Visão dos KPIs: {kpi_start_date} a {kpi_end_date}")
    render_kpi_groups(
        [
            (
                "Receita",
                [
                    {
                        "label": "Receita de pedidos",
                        "value": _format_brl(kpis["revenue"]),
                        "context": "Pedidos concluídos, deduplicados por venda.",
                        "primary": True,
                    },
                    {
                        "label": "Receita item",
                        "value": _format_brl(kpis["item_revenue"]),
                        "context": "Subtotal de itens, sem frete e desconto.",
                    },
                    {
                        "label": "Ticket médio",
                        "value": _format_brl(kpis["average_ticket"]),
                        "context": "Receita média por pedido concluído.",
                    },
                ],
            ),
            (
                "Rentabilidade",
                [
                    {
                        "label": "Lucro bruto",
                        "value": _format_brl(kpis["gross_profit"]),
                        "context": "Lucro calculado no grão de item.",
                        "primary": True,
                    },
                    {
                        "label": "Margem bruta",
                        "value": f"{kpis['gross_margin_percent']:.2f}%",
                        "context": "Lucro bruto sobre receita item.",
                    },
                ],
            ),
            (
                "Operação",
                [
                    {
                        "label": "Pedidos concluídos",
                        "value": f"{kpis['completed_orders']:,}".replace(",", "."),
                        "context": "Pedidos pagos e enviados no período.",
                        "primary": True,
                    },
                    {
                        "label": "Unidades vendidas",
                        "value": f"{kpis['units_sold']:,}".replace(",", "."),
                        "context": "Quantidade total de itens vendidos.",
                    },
                    {
                        "label": "Produtos ativos",
                        "value": str(active_products),
                        "context": "Catálogo disponível para venda.",
                    },
                ],
            ),
            (
                "Clientes",
                [
                    {
                        "label": "Avaliação média",
                        "value": f"{reviews['average_rating']:.2f}",
                        "context": "Média das notas registradas.",
                    },
                    {
                        "label": "Carrinhos abertos",
                        "value": str(carts["open_carts"]),
                        "context": "Carrinhos ainda sem checkout.",
                    },
                    {
                        "label": "Carrinhos abandonados",
                        "value": str(carts["abandoned_carts"]),
                        "context": "Oportunidades de recuperação.",
                    },
                    {
                        "label": "Valor em carrinhos",
                        "value": _format_brl(carts["cart_item_value"]),
                        "context": "Valor potencial nos itens de carrinho.",
                    },
                ],
            ),
        ]
    )

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
        [
            "📈 Vendas",
            "↔️ Comparação",
            "🏷️ Produtos",
            "👥 Clientes",
            "⚙️ Operação",
            "✨ AI QA",
        ]
    )

    with tab_sales:
        render_section_title(
            "Vendas e receita",
            "Acompanhe receita, unidades, lucro bruto e canais com a mesma janela de filtros.",
        )
        monthly = monthly_revenue(fato)
        units = monthly_units_sold(fato)
        profit = monthly_gross_profit(fato)
        profit_trend = revenue_profit_trend(fato)
        shipping_discount = shipping_discount_trend(fato)
        states = revenue_by_state(fato)
        state_trend = state_revenue_trend(fato)
        payments = payment_summary
        payment_trend = payment_method_trend(fato)
        raw_status = monthly_orders_by_status(sheets["Purchases"])
        payments_display = _localize_values(payments, "Metodo Pagamento", PAYMENT_LABELS)
        payment_trend_display = _localize_values(payment_trend, "Metodo Pagamento", PAYMENT_LABELS)
        raw_status_display = _localize_values(raw_status, "Status", STATUS_LABELS)
        leading_state = states.sort_values("revenue", ascending=False).iloc[0]
        render_insight_callout(
            label="Leitura rápida",
            title=f"{leading_state['Estado Cliente']} lidera a receita do recorte",
            body=f"O estado concentra {_format_brl(leading_state['revenue'])} em pedidos concluídos.",
        )

        st.plotly_chart(
            _format_chart(
                px.line(
                    monthly,
                    x="Mes",
                    y="revenue",
                    markers=True,
                    title="Receita mensal de pedidos concluídos",
                    labels=PLOT_LABELS,
                ),
                currency=True,
                x_tick_angle=-25,
                margin={"l": 42, "r": 24, "t": 64, "b": 76},
            ),
            width="stretch",
        )
        render_section_title(
            "Composição comercial",
            "Veja a distribuição por território, pagamento, frete, desconto e status de pedidos.",
        )
        col_a, col_b = st.columns(2)
        col_a.plotly_chart(
            _format_chart(
                px.line(
                    units,
                    x="Mes",
                    y="units_sold",
                    markers=True,
                    title="Unidades vendidas por mês",
                    labels=PLOT_LABELS,
                ),
                count=True,
                height=410,
                x_tick_angle=-30,
                legend_orientation="v",
                margin={"l": 42, "r": 120, "t": 64, "b": 78},
            ),
            width="stretch",
        )
        col_b.plotly_chart(
            _format_chart(
                px.line(
                    profit_trend,
                    x="Mes",
                    y=["item_revenue", "gross_profit"],
                    markers=True,
                    title="Receita item versus lucro bruto",
                    labels=PLOT_LABELS,
                ),
                currency=True,
                height=410,
                x_tick_angle=-25,
                margin={"l": 48, "r": 24, "t": 64, "b": 78},
            ),
            width="stretch",
        )
        col_a, col_b = st.columns(2)
        col_a.plotly_chart(
            _format_chart(
                px.bar(
                    states.sort_values("revenue", ascending=False),
                    x="Estado Cliente",
                    y="revenue",
                    title="Receita por estado",
                    labels=PLOT_LABELS,
                ),
                currency=True,
                height=410,
                x_tick_angle=-25,
                margin={"l": 48, "r": 24, "t": 64, "b": 78},
            ),
            width="stretch",
        )
        col_b.plotly_chart(
            _format_chart(
                px.bar(
                    payments_display.sort_values("completed_orders", ascending=False),
                    x="Metodo Pagamento",
                    y="completed_orders",
                    title="Pedidos por método de pagamento",
                    labels=PLOT_LABELS,
                ),
                count=True,
                height=430,
                x_tick_angle=-30,
                legend_orientation="v",
                margin={"l": 48, "r": 132, "t": 64, "b": 82},
            ),
            width="stretch",
        )
        col_a, col_b = st.columns(2)
        col_a.plotly_chart(
            _format_chart(
                px.line(
                    shipping_discount,
                    x="Mes",
                    y=["shipping_total", "discount_total"],
                    markers=True,
                    title="Frete e desconto por mês",
                    labels=PLOT_LABELS,
                ),
                currency=True,
                height=410,
                x_tick_angle=-25,
                margin={"l": 54, "r": 24, "t": 64, "b": 78},
            ),
            width="stretch",
        )
        col_b.plotly_chart(
            _format_chart(
                px.bar(
                    raw_status_display,
                    x="Mes",
                    y="orders",
                    color="Status",
                    title="Pedidos brutos por status",
                    labels=PLOT_LABELS,
                ),
                count=True,
                height=410,
                x_tick_angle=-25,
                legend_orientation="v",
                margin={"l": 42, "r": 118, "t": 64, "b": 78},
            ),
            width="stretch",
        )
        with st.expander("Tendências por estado e pagamento", expanded=False):
            col_a, col_b = st.columns(2)
            col_a.plotly_chart(
                _format_chart(
                    px.line(
                        state_trend,
                        x="Mes",
                        y="revenue",
                        color="Estado Cliente",
                        title="Receita por estado ao longo do tempo",
                        labels=PLOT_LABELS,
                    ),
                    currency=True,
                    height=430,
                    x_tick_angle=-30,
                    legend_orientation="v",
                    margin={"l": 54, "r": 118, "t": 64, "b": 78},
                ),
                width="stretch",
            )
            col_b.plotly_chart(
                _format_chart(
                    px.line(
                        payment_trend_display,
                        x="Mes",
                        y="completed_orders",
                        color="Metodo Pagamento",
                        title="Pedidos por pagamento ao longo do tempo",
                        labels=PLOT_LABELS,
                    ),
                    count=True,
                    height=430,
                    x_tick_angle=-30,
                    legend_orientation="v",
                    margin={"l": 44, "r": 118, "t": 64, "b": 78},
                ),
                width="stretch",
            )
        render_section_title(
            "Lucro bruto mensal",
            "Tabela de apoio para leitura dos valores que alimentam a série financeira.",
        )
        render_table(
            _display_table(profit),
            height=ANALYTICS_TABLE_HEIGHT,
            column_order=["Mês", "Lucro bruto", "Receita item", "Margem bruta (%)"],
        )

    with tab_compare:
        render_section_title(
            "Comparação de períodos",
            "Compare duas janelas usando as mesmas regras de grão dos KPIs.",
        )
        default_current_start = pd.Timestamp(full_dates.max()).replace(day=1).date()
        default_previous_end = default_current_start - pd.Timedelta(days=1)
        default_previous_start = pd.Timestamp(default_previous_end).replace(day=1).date()
        current_column, previous_column = st.columns(2)
        with current_column:
            render_control_label("Período atual")
            current_period = st.date_input(
                "Período atual",
                value=(default_current_start, full_dates.max()),
                min_value=full_dates.min(),
                max_value=full_dates.max(),
                key="comparison_current_period",
                label_visibility="collapsed",
            )
        with previous_column:
            render_control_label("Período anterior")
            previous_period = st.date_input(
                "Período anterior",
                value=(default_previous_start, default_previous_end),
                min_value=full_dates.min(),
                max_value=full_dates.max(),
                key="comparison_previous_period",
                label_visibility="collapsed",
            )
        if (
            isinstance(current_period, tuple)
            and len(current_period) == 2
            and isinstance(previous_period, tuple)
            and len(previous_period) == 2
        ):
            render_period_comparison_summary(
                current_period=current_period,
                previous_period=previous_period,
            )
            comparison = compare_periods(
                sheets["Fato Vendas"],
                current_start=current_period[0],
                current_end=current_period[1],
                previous_start=previous_period[0],
                previous_end=previous_period[1],
            )
            render_table(
                _display_table(comparison),
                height=ANALYTICS_TABLE_HEIGHT,
                column_order=["Métrica", "Atual", "Anterior", "Variação", "Crescimento (%)"],
                hide_columns=["Código"],
            )
            comparison_chart = comparison.copy()
            comparison_chart["label"] = (
                comparison_chart["metric"].map(METRIC_LABELS).fillna(comparison_chart["label"])
            )
            st.plotly_chart(
                _format_chart(
                    px.bar(
                        comparison_chart,
                        x="label",
                        y="delta",
                        title="Variação absoluta por métrica",
                        labels=PLOT_LABELS,
                    ),
                    currency=True,
                ),
                width="stretch",
            )
        else:
            st.warning("Selecione dois intervalos completos para comparar.")

    with tab_products:
        render_section_title(
            "Categorias e produtos",
            "Leia receita, lucro, margem e participação do catálogo vendido.",
        )
        categories = category_performance(fato)
        products = product_ranking(fato, limit=12)
        products_by_units = product_ranking(fato, limit=12, sort_by="units")
        category_share = share_of_total(categories, "item_revenue")
        category_monthly = category_trend(fato)
        leading_category = categories.sort_values("item_revenue", ascending=False).iloc[0]
        leading_category_name = CATEGORY_LABELS.get(
            leading_category["Categoria"],
            leading_category["Categoria"],
        )
        render_insight_callout(
            label="Leitura rápida",
            title=f"{leading_category_name} é a categoria líder",
            body=f"Receita item de {_format_brl(leading_category['item_revenue'])} no recorte filtrado.",
        )
        col_a, col_b = st.columns(2)
        col_a.plotly_chart(
            _format_chart(
                px.bar(
                    categories.sort_values("item_revenue", ascending=False),
                    x="Categoria",
                    y="item_revenue",
                    title="Receita item por categoria",
                    labels=PLOT_LABELS,
                ),
                currency=True,
                height=410,
                x_tick_angle=-25,
                margin={"l": 54, "r": 24, "t": 64, "b": 78},
            ),
            width="stretch",
        )
        col_b.plotly_chart(
            _format_chart(
                px.bar(
                    categories.sort_values("gross_profit", ascending=False),
                    x="Categoria",
                    y="gross_profit",
                    title="Lucro bruto por categoria",
                    labels=PLOT_LABELS,
                ),
                currency=True,
                height=410,
                x_tick_angle=-25,
                margin={"l": 54, "r": 24, "t": 64, "b": 78},
            ),
            width="stretch",
        )
        col_a, col_b = st.columns(2)
        col_a.plotly_chart(
            _format_chart(
                px.bar(
                    categories.sort_values("gross_margin_percent", ascending=False),
                    x="Categoria",
                    y="gross_margin_percent",
                    title="Margem por categoria",
                    labels=PLOT_LABELS,
                ),
                percent=True,
                height=410,
                x_tick_angle=-25,
                margin={"l": 42, "r": 24, "t": 64, "b": 78},
            ),
            width="stretch",
        )
        col_b.plotly_chart(
            _format_chart(
                px.bar(
                    products_by_units.sort_values("units_sold", ascending=False),
                    x="Produto",
                    y="units_sold",
                    title="Top produtos por unidades",
                    labels=PLOT_LABELS,
                ),
                count=True,
                height=450,
                x_tick_angle=-30,
                margin={"l": 42, "r": 24, "t": 64, "b": 112},
            ),
            width="stretch",
        )
        col_a, col_b = st.columns(2)
        col_a.plotly_chart(
            _format_horizontal_chart(
                px.bar(
                    category_share.sort_values("share_percent"),
                    x="share_percent",
                    y="Categoria",
                    orientation="h",
                    title="Participação da receita item por categoria",
                    labels=PLOT_LABELS,
                ),
                percent=True,
                height=410,
                margin={"l": 92, "r": 24, "t": 64, "b": 48},
            ),
            width="stretch",
        )
        col_b.plotly_chart(
            _format_chart(
                px.line(
                    category_monthly,
                    x="Mes",
                    y="item_revenue",
                    color="Categoria",
                    title="Tendência mensal por categoria",
                    labels=PLOT_LABELS,
                ),
                currency=True,
                height=440,
                x_tick_angle=-30,
                legend_orientation="v",
                margin={"l": 54, "r": 132, "t": 64, "b": 78},
            ),
            width="stretch",
        )
        render_section_title(
            "Ranking de produtos",
            "Produtos líderes no período filtrado, ordenados pela regra de ranking do dashboard.",
        )
        render_table(
            _display_table(products),
            height=ANALYTICS_TABLE_HEIGHT,
            column_order=[
                "Ranking",
                "Produto",
                "Categoria",
                "Receita item",
                "Lucro bruto",
                "Margem bruta (%)",
                "Unidades vendidas",
            ],
            sort_by="Receita item",
            rank=True,
            hide_columns=["ID Produto"],
        )

    with tab_customers:
        render_section_title(
            "Clientes e retenção",
            "Métricas de recorrência, valor médio por cliente e evolução de coortes.",
        )
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
        render_section_title(
            "Rankings de clientes",
            "Retenção considera pedidos concluídos deduplicados por venda e agrupados por cliente.",
        )
        render_table(
            _display_table(top_customers(fato, sheets["Dimensão Clientes"], limit=15)),
            height=ANALYTICS_TABLE_HEIGHT,
            column_order=[
                "Ranking",
                "Nome do cliente",
                "Estado",
                "Cidade",
                "Receita",
                "Pedidos concluídos",
                "Primeira compra",
                "Última compra",
            ],
            sort_by="Receita",
            rank=True,
            hide_columns=["ID Cliente", "Email"],
        )
        render_table(
            _display_table(customer_geography_table(fato, sheets["Dimensão Clientes"]).head(15)),
            height=ANALYTICS_TABLE_HEIGHT,
            column_order=["Ranking", "Estado", "Cidade", "Receita", "Pedidos", "Clientes ativos"],
            sort_by="Receita",
            rank=True,
        )
        render_section_title(
            "Coortes mensais",
            "Acompanhe a atividade de clientes por mês de primeira compra.",
        )
        cohorts = monthly_customer_cohorts(fato)
        leading_cohort = cohorts.sort_values("active_customers", ascending=False).iloc[0]
        render_insight_callout(
            label="Leitura rápida",
            title=f"Coorte {leading_cohort['cohort_month']} tem maior atividade",
            body=(
                f"{int(leading_cohort['active_customers'])} clientes ativos "
                f"no mês {int(leading_cohort['months_since_first_purchase'])}."
            ),
        )
        st.plotly_chart(
            _format_chart(
                px.line(
                    cohorts,
                    x="months_since_first_purchase",
                    y="active_customers",
                    color="cohort_month",
                    markers=True,
                    title="Clientes ativos por coorte mensal",
                    labels=PLOT_LABELS,
                ),
                count=True,
                height=440,
                legend_orientation="v",
                margin={"l": 48, "r": 132, "t": 64, "b": 54},
            ),
            width="stretch",
        )

    with tab_ops:
        render_section_title(
            "Operação e experiência",
            "Monitore carrinhos, pagamentos e avaliações para identificar fricções operacionais.",
        )
        cart_status = cart_status_summary(sheets["Carts"], sheets["Cart Items"])
        rating_counts = rating_distribution(sheets["Reviews"])
        cart_share = share_of_total(cart_status, "carts")
        rating_share = share_of_total(rating_counts, "review_count")
        payment_share = share_of_total(payment_summary, "completed_orders")
        cart_status_display = _localize_values(cart_status, "Status", STATUS_LABELS)
        cart_share_display = _localize_values(cart_share, "Status", STATUS_LABELS)
        payment_share_display = _localize_values(payment_share, "Metodo Pagamento", PAYMENT_LABELS)
        abandoned_carts = cart_status_display.loc[cart_status_display["Status"] == "Abandonado"]
        if not abandoned_carts.empty:
            abandoned_row = abandoned_carts.iloc[0]
            render_insight_callout(
                label="Leitura rápida",
                title=f"{int(abandoned_row['carts'])} carrinhos abandonados",
                body=f"Valor potencial de {_format_brl(abandoned_row['cart_value'])} para recuperação.",
            )
        col_a, col_b = st.columns(2)
        col_a.plotly_chart(
            _format_chart(
                px.bar(
                    cart_status_display.sort_values("carts", ascending=False),
                    x="Status",
                    y="carts",
                    title="Carrinhos por status",
                    labels=PLOT_LABELS,
                ),
                count=True,
                height=410,
                x_tick_angle=-25,
                margin={"l": 42, "r": 24, "t": 64, "b": 78},
            ),
            width="stretch",
        )
        col_b.plotly_chart(
            _format_chart(
                px.bar(
                    cart_status_display.sort_values("cart_value", ascending=False),
                    x="Status",
                    y="cart_value",
                    title="Valor de carrinhos por status",
                    labels=PLOT_LABELS,
                ),
                currency=True,
                height=410,
                x_tick_angle=-25,
                margin={"l": 54, "r": 24, "t": 64, "b": 78},
            ),
            width="stretch",
        )
        col_a, col_b = st.columns(2)
        col_a.plotly_chart(
            _format_horizontal_chart(
                px.bar(
                    payment_share_display.sort_values("share_percent"),
                    x="share_percent",
                    y="Metodo Pagamento",
                    orientation="h",
                    title="Participação de pedidos por pagamento",
                    labels=PLOT_LABELS,
                ),
                percent=True,
                height=400,
                margin={"l": 112, "r": 24, "t": 64, "b": 48},
            ),
            width="stretch",
        )
        col_b.plotly_chart(
            _format_chart(
                px.bar(
                    rating_counts,
                    x="rating",
                    y="review_count",
                    title="Distribuição de avaliações",
                    labels=PLOT_LABELS,
                ),
                count=True,
            ),
            width="stretch",
        )
        col_a, col_b = st.columns(2)
        col_a.plotly_chart(
            _format_horizontal_chart(
                px.bar(
                    rating_share.sort_values("share_percent"),
                    x="share_percent",
                    y="rating",
                    orientation="h",
                    title="Participação de avaliações",
                    labels=PLOT_LABELS,
                ),
                percent=True,
                height=400,
                margin={"l": 94, "r": 24, "t": 64, "b": 48},
            ),
            width="stretch",
        )
        col_b.plotly_chart(
            _format_horizontal_chart(
                px.bar(
                    cart_share_display.sort_values("share_percent"),
                    x="share_percent",
                    y="Status",
                    orientation="h",
                    title="Participação de carrinhos",
                    labels=PLOT_LABELS,
                ),
                percent=True,
            ),
            width="stretch",
        )
        render_section_title(
            "Listas operacionais",
            "Produtos com avaliações recentes e carrinhos com potencial de recuperação.",
        )
        render_table(
            _display_table(product_review_table(sheets["Reviews"], sheets["Products"]).head(15)),
            height=ANALYTICS_TABLE_HEIGHT,
            column_order=["Ranking", "Produto", "Avaliação média", "Avaliações"],
            sort_by="Avaliação média",
            rank=True,
            hide_columns=["ID Produto"],
        )
        render_table(
            _display_table(cart_recovery_table(sheets["Carts"], sheets["Cart Items"], sheets["Users"])),
            height=ANALYTICS_TABLE_HEIGHT,
            column_order=["Ranking", "Nome", "Email", "Valor do carrinho", "Itens", "Status"],
            sort_by="Valor do carrinho",
            rank=True,
            hide_columns=["ID", "ID Cliente"],
        )

    with tab_ai:
        render_section_title(
            "Perguntas de negócio",
            "Respostas locais usam fórmulas governadas. Gemini é opcional quando configurado.",
        )
        col_question, col_mode = st.columns([0.68, 0.32])
        with col_question:
            question = st.text_area(
                "Pergunta de negócio",
                placeholder="Ex.: Qual categoria gera mais lucro bruto?",
            )
        with col_mode:
            use_gemini = st.toggle("Usar Gemini quando configurado", value=False)
            render_ai_status(use_gemini=use_gemini, gemini_ready=_gemini_is_ready())
        if not question.strip():
            render_ai_empty_state(
                "Digite uma pergunta para receber uma resposta local governada. "
                "Ative Gemini apenas quando quiser complementar a análise."
            )
        if st.button("Responder", disabled=not question.strip()):
            local_answer = answer_from_workbook(question, sheets)
            render_ai_message(
                label="Resposta local",
                title="Fórmulas governadas do workbook",
                body=local_answer,
            )
            if use_gemini:
                try:
                    answer = answer_business_question(question, kpis)
                except GeminiConfigurationError as exc:
                    render_ai_message(
                        label="Gemini",
                        title="Configuração necessária",
                        body=str(exc),
                        tone="warning",
                    )
                except Exception as exc:
                    render_ai_message(
                        label="Gemini",
                        title="Não foi possível consultar o modelo",
                        body=f"Erro ao consultar Gemini: {exc}",
                        tone="error",
                    )
                else:
                    render_ai_message(
                        label="Gemini",
                        title="Complemento generativo",
                        body=answer,
                        tone="gemini",
                    )


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
