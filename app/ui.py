"""Shared visual presentation helpers for the Streamlit app."""

from __future__ import annotations

from collections.abc import Sequence
from html import escape
from typing import Any

import pandas as pd
import streamlit as st


THEME = {
    "color_bg": "#f6f7f9",
    "color_surface": "#ffffff",
    "color_surface_alt": "#eef2f6",
    "color_text": "#172033",
    "color_muted": "#5d6678",
    "color_border": "#d9dee7",
    "color_primary": "#1f6feb",
    "color_primary_soft": "#e8f1ff",
    "color_accent": "#0f8b8d",
    "color_success": "#16833a",
    "color_warning": "#b7791f",
    "color_danger": "#c2410c",
    "shadow_sm": "0 1px 2px rgba(23, 32, 51, 0.06)",
    "shadow_md": "0 10px 24px rgba(23, 32, 51, 0.08)",
    "radius_sm": "6px",
    "radius_md": "8px",
    "space_xs": "0.25rem",
    "space_sm": "0.5rem",
    "space_md": "0.75rem",
    "space_lg": "1rem",
    "space_xl": "1.5rem",
}

PLOTLY_PALETTE = [
    THEME["color_primary"],
    THEME["color_accent"],
    THEME["color_success"],
    THEME["color_warning"],
    "#7c3aed",
    "#e11d48",
    "#64748b",
]


def apply_base_styles() -> None:
    """Apply the app-wide visual foundation without changing Streamlit behavior."""

    st.markdown(
        f"""
        <style>
        :root {{
            --mei-bg: {THEME["color_bg"]};
            --mei-surface: {THEME["color_surface"]};
            --mei-surface-alt: {THEME["color_surface_alt"]};
            --mei-text: {THEME["color_text"]};
            --mei-muted: {THEME["color_muted"]};
            --mei-border: {THEME["color_border"]};
            --mei-primary: {THEME["color_primary"]};
            --mei-primary-soft: {THEME["color_primary_soft"]};
            --mei-accent: {THEME["color_accent"]};
            --mei-success: {THEME["color_success"]};
            --mei-warning: {THEME["color_warning"]};
            --mei-danger: {THEME["color_danger"]};
            --mei-shadow-sm: {THEME["shadow_sm"]};
            --mei-shadow-md: {THEME["shadow_md"]};
            --mei-radius-sm: {THEME["radius_sm"]};
            --mei-radius-md: {THEME["radius_md"]};
            --mei-space-xs: {THEME["space_xs"]};
            --mei-space-sm: {THEME["space_sm"]};
            --mei-space-md: {THEME["space_md"]};
            --mei-space-lg: {THEME["space_lg"]};
            --mei-space-xl: {THEME["space_xl"]};
        }}

        .stApp {{
            background: var(--mei-bg);
            color: var(--mei-text);
        }}

        .block-container {{
            max-width: 1320px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }}

        h1, h2, h3, h4, h5, h6 {{
            color: var(--mei-text);
            letter-spacing: 0;
        }}

        h1 {{
            font-size: 2rem;
            line-height: 1.15;
            margin-bottom: var(--mei-space-sm);
        }}

        h2, h3 {{
            margin-top: 1.4rem;
        }}

        .mei-app-header {{
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 1.25rem;
            background: var(--mei-surface);
            border: 1px solid var(--mei-border);
            border-radius: var(--mei-radius-md);
            box-shadow: var(--mei-shadow-md);
            padding: 1.35rem 1.45rem;
            margin-bottom: 1.35rem;
        }}

        .mei-app-header__content {{
            min-width: 0;
        }}

        .mei-eyebrow {{
            color: var(--mei-accent);
            font-size: 0.74rem;
            font-weight: 700;
            letter-spacing: 0;
            line-height: 1.2;
            margin-bottom: 0.35rem;
            text-transform: uppercase;
        }}

        .mei-app-title {{
            color: var(--mei-text);
            font-size: 2.05rem;
            font-weight: 750;
            letter-spacing: 0;
            line-height: 1.1;
            margin: 0;
        }}

        .mei-app-description {{
            color: var(--mei-muted);
            font-size: 0.98rem;
            line-height: 1.55;
            margin: 0.55rem 0 0;
            max-width: 760px;
        }}

        .mei-header-meta,
        .mei-header-actions {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 0.9rem;
        }}

        .mei-header-actions {{
            justify-content: flex-end;
            margin-top: 0;
            min-width: 235px;
        }}

        .mei-status-pill,
        .mei-action-pill {{
            align-items: center;
            border-radius: 999px;
            display: inline-flex;
            font-size: 0.78rem;
            font-weight: 700;
            gap: 0.35rem;
            line-height: 1;
            min-height: 2rem;
            padding: 0.55rem 0.72rem;
            white-space: nowrap;
        }}

        .mei-status-pill {{
            background: var(--mei-surface-alt);
            border: 1px solid var(--mei-border);
            color: var(--mei-text);
        }}

        .mei-status-pill--success {{
            background: #eaf7ef;
            border-color: #bfe5cb;
            color: var(--mei-success);
        }}

        .mei-action-pill {{
            background: var(--mei-primary-soft);
            border: 1px solid #c7ddff;
            color: var(--mei-primary);
        }}

        .mei-section-title {{
            color: var(--mei-text);
            font-size: 1.22rem;
            font-weight: 750;
            letter-spacing: 0;
            line-height: 1.25;
            margin: 1.45rem 0 0.45rem;
        }}

        .mei-helper-text {{
            color: var(--mei-muted);
            font-size: 0.88rem;
            line-height: 1.45;
            margin: 0 0 0.75rem;
        }}

        .mei-empty-filter-state {{
            background: var(--mei-surface);
            border: 1px solid #f0d8a8;
            border-left: 0.28rem solid var(--mei-warning);
            border-radius: var(--mei-radius-md);
            box-shadow: var(--mei-shadow-md);
            margin: 0.25rem 0 1.35rem;
            padding: 1.1rem 1.15rem;
        }}

        .mei-empty-filter-state__eyebrow {{
            color: var(--mei-warning);
            display: block;
            font-size: 0.72rem;
            font-weight: 750;
            letter-spacing: 0;
            line-height: 1.15;
            margin-bottom: 0.35rem;
            text-transform: uppercase;
        }}

        .mei-empty-filter-state__title {{
            color: var(--mei-text);
            font-size: 1.15rem;
            font-weight: 750;
            line-height: 1.25;
            margin: 0;
        }}

        .mei-empty-filter-state__copy {{
            color: var(--mei-muted);
            font-size: 0.9rem;
            line-height: 1.5;
            margin: 0.5rem 0 0.9rem;
            max-width: 760px;
        }}

        .mei-empty-filter-state__grid {{
            display: grid;
            gap: 0.65rem;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            margin-top: 0.85rem;
        }}

        .mei-empty-filter-state__item {{
            background: #fff8eb;
            border: 1px solid #f0d8a8;
            border-radius: var(--mei-radius-sm);
            min-width: 0;
            padding: 0.62rem 0.68rem;
        }}

        .mei-empty-filter-state__label {{
            color: var(--mei-muted);
            display: block;
            font-size: 0.69rem;
            font-weight: 750;
            letter-spacing: 0;
            line-height: 1.15;
            margin-bottom: 0.24rem;
            text-transform: uppercase;
        }}

        .mei-empty-filter-state__value {{
            color: var(--mei-text);
            display: block;
            font-size: 0.84rem;
            font-weight: 650;
            line-height: 1.35;
            overflow-wrap: anywhere;
        }}

        p, li, label, [data-testid="stCaptionContainer"] {{
            color: var(--mei-muted);
        }}

        [data-testid="stSidebar"] {{
            background: #eef2f6;
            border-right: 1px solid var(--mei-border);
        }}

        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] label {{
            color: var(--mei-text);
        }}

        [data-testid="stSidebar"] .stButton > button {{
            width: 100%;
        }}

        .mei-sidebar-panel {{
            background: var(--mei-surface);
            border: 1px solid var(--mei-border);
            border-radius: var(--mei-radius-md);
            box-shadow: var(--mei-shadow-sm);
            margin: 0.35rem 0 0.9rem;
            padding: 0.95rem;
        }}

        .mei-sidebar-panel__eyebrow {{
            color: var(--mei-accent);
            font-size: 0.72rem;
            font-weight: 750;
            letter-spacing: 0;
            line-height: 1.2;
            margin-bottom: 0.25rem;
            text-transform: uppercase;
        }}

        .mei-sidebar-panel__title {{
            color: var(--mei-text);
            font-size: 1rem;
            font-weight: 750;
            line-height: 1.25;
            margin: 0;
        }}

        .mei-sidebar-panel__copy {{
            color: var(--mei-muted);
            font-size: 0.82rem;
            line-height: 1.45;
            margin: 0.45rem 0 0;
        }}

        .mei-sidebar-divider {{
            border-top: 1px solid var(--mei-border);
            margin: 0.8rem 0;
        }}

        .mei-filter-summary {{
            display: grid;
            gap: 0.55rem;
            margin-top: 0.8rem;
        }}

        .mei-filter-summary__item {{
            background: var(--mei-surface-alt);
            border: 1px solid var(--mei-border);
            border-radius: var(--mei-radius-sm);
            padding: 0.6rem 0.65rem;
        }}

        .mei-filter-summary__label {{
            color: var(--mei-muted);
            display: block;
            font-size: 0.7rem;
            font-weight: 750;
            letter-spacing: 0;
            line-height: 1.15;
            margin-bottom: 0.25rem;
            text-transform: uppercase;
        }}

        .mei-filter-summary__value {{
            color: var(--mei-text);
            display: block;
            font-size: 0.84rem;
            font-weight: 650;
            line-height: 1.35;
            overflow-wrap: anywhere;
        }}

        .mei-ai-status,
        .mei-ai-message,
        .mei-ai-empty {{
            background: var(--mei-surface);
            border: 1px solid var(--mei-border);
            border-radius: var(--mei-radius-md);
            box-shadow: var(--mei-shadow-sm);
            margin: 0.75rem 0;
            padding: 0.95rem 1rem;
        }}

        .mei-ai-status {{
            display: grid;
            gap: 0.55rem;
        }}

        .mei-ai-status__row {{
            align-items: center;
            display: flex;
            gap: 0.55rem;
            justify-content: space-between;
        }}

        .mei-ai-status__label,
        .mei-ai-message__label {{
            color: var(--mei-muted);
            display: block;
            font-size: 0.72rem;
            font-weight: 750;
            letter-spacing: 0;
            line-height: 1.15;
            text-transform: uppercase;
        }}

        .mei-ai-status__value {{
            color: var(--mei-text);
            font-size: 0.86rem;
            font-weight: 700;
            line-height: 1.25;
            text-align: right;
        }}

        .mei-ai-status__value--success {{
            color: var(--mei-success);
        }}

        .mei-ai-status__value--warning {{
            color: var(--mei-warning);
        }}

        .mei-ai-message {{
            border-left: 0.28rem solid var(--mei-primary);
        }}

        .mei-ai-message--gemini {{
            border-left-color: var(--mei-accent);
        }}

        .mei-ai-message--warning {{
            border-left-color: var(--mei-warning);
        }}

        .mei-ai-message--error {{
            border-left-color: var(--mei-danger);
        }}

        .mei-ai-message__title {{
            color: var(--mei-text);
            font-size: 1rem;
            font-weight: 750;
            line-height: 1.25;
            margin: 0.18rem 0 0.5rem;
        }}

        .mei-ai-message__body {{
            color: var(--mei-text);
            font-size: 0.92rem;
            line-height: 1.55;
            margin: 0;
            white-space: pre-wrap;
        }}

        .mei-ai-empty {{
            background: var(--mei-surface-alt);
            color: var(--mei-muted);
            font-size: 0.9rem;
            line-height: 1.45;
        }}

        .mei-kpi-domain {{
            margin: 1rem 0 0.85rem;
        }}

        .mei-period-control__label,
        .mei-primary-action__label {{
            color: var(--mei-muted);
            display: block;
            font-size: 0.72rem;
            font-weight: 750;
            letter-spacing: 0;
            line-height: 1.15;
            margin-bottom: 0.38rem;
            text-transform: uppercase;
        }}

        div[role="radiogroup"] {{
            background: var(--mei-surface);
            border: 1px solid var(--mei-border);
            border-radius: var(--mei-radius-md);
            box-shadow: var(--mei-shadow-sm);
            display: inline-flex;
            flex-wrap: wrap;
            gap: 0.25rem;
            padding: 0.25rem;
        }}

        div[role="radiogroup"] label {{
            align-items: center;
            border-radius: var(--mei-radius-sm);
            color: var(--mei-muted);
            display: inline-flex;
            font-size: 0.86rem;
            font-weight: 700;
            justify-content: center;
            line-height: 1.15;
            margin: 0;
            min-height: 2.35rem;
            padding: 0.4rem 0.75rem;
            transition: background 140ms ease, color 140ms ease, box-shadow 140ms ease;
        }}

        div[role="radiogroup"] label:has(input:checked) {{
            background: var(--mei-primary);
            box-shadow: 0 6px 14px rgba(31, 111, 235, 0.2);
            color: #ffffff;
        }}

        div[role="radiogroup"] label > div:first-child {{
            display: none;
        }}

        .mei-kpi-domain__title {{
            color: var(--mei-text);
            font-size: 0.9rem;
            font-weight: 750;
            letter-spacing: 0;
            line-height: 1.2;
            margin: 0 0 0.55rem;
        }}

        .mei-kpi-grid {{
            display: grid;
            gap: 0.75rem;
            grid-template-columns: repeat(auto-fit, minmax(185px, 1fr));
        }}

        .mei-kpi-card {{
            background: var(--mei-surface);
            border: 1px solid var(--mei-border);
            border-radius: var(--mei-radius-md);
            box-shadow: var(--mei-shadow-sm);
            min-height: 8.2rem;
            padding: 0.9rem 0.95rem;
        }}

        .mei-kpi-card--primary {{
            border-color: #b7d1ff;
            box-shadow: var(--mei-shadow-md);
            position: relative;
        }}

        .mei-kpi-card--primary::before {{
            background: var(--mei-primary);
            border-radius: 999px;
            content: "";
            height: calc(100% - 1.55rem);
            left: 0.55rem;
            position: absolute;
            top: 0.775rem;
            width: 0.22rem;
        }}

        .mei-kpi-card__label {{
            color: var(--mei-muted);
            display: block;
            font-size: 0.75rem;
            font-weight: 750;
            letter-spacing: 0;
            line-height: 1.2;
            margin-bottom: 0.45rem;
            text-transform: uppercase;
        }}

        .mei-kpi-card--primary .mei-kpi-card__label,
        .mei-kpi-card--primary .mei-kpi-card__value,
        .mei-kpi-card--primary .mei-kpi-card__context,
        .mei-kpi-card--primary .mei-kpi-card__delta {{
            margin-left: 0.45rem;
        }}

        .mei-kpi-card__value {{
            color: var(--mei-text);
            display: block;
            font-size: 1.45rem;
            font-weight: 780;
            letter-spacing: 0;
            line-height: 1.12;
            overflow-wrap: anywhere;
        }}

        .mei-kpi-card--secondary .mei-kpi-card__value {{
            font-size: 1.22rem;
            font-weight: 720;
        }}

        .mei-kpi-card__context {{
            color: var(--mei-muted);
            display: block;
            font-size: 0.78rem;
            line-height: 1.35;
            margin-top: 0.55rem;
        }}

        .mei-kpi-card__delta {{
            color: var(--mei-accent);
            display: block;
            font-size: 0.78rem;
            font-weight: 750;
            line-height: 1.25;
            margin-top: 0.5rem;
        }}

        div[data-testid="stMetric"] {{
            background: var(--mei-surface);
            border: 1px solid var(--mei-border);
            border-radius: var(--mei-radius-md);
            box-shadow: var(--mei-shadow-sm);
            padding: 0.9rem 1rem;
        }}

        div[data-testid="stMetric"] label {{
            color: var(--mei-muted);
            font-size: 0.78rem;
        }}

        div[data-testid="stMetricValue"] {{
            color: var(--mei-text);
            font-size: 1.55rem;
            line-height: 1.2;
        }}

        div[data-testid="stExpander"],
        [data-testid="stDataFrame"],
        [data-testid="stPlotlyChart"] {{
            border-radius: var(--mei-radius-md);
        }}

        div[data-testid="stExpander"] {{
            border-color: var(--mei-border);
            box-shadow: var(--mei-shadow-sm);
        }}

        .stButton > button,
        .stDownloadButton > button {{
            border-radius: var(--mei-radius-sm);
            border-color: var(--mei-border);
            font-weight: 600;
        }}

        .stButton > button[kind="primary"],
        .stDownloadButton > button[kind="primary"] {{
            background: var(--mei-primary);
            border-color: var(--mei-primary);
            color: #ffffff;
        }}

        .stTabs [data-baseweb="tab-list"] {{
            gap: var(--mei-space-sm);
            border-bottom: 1px solid var(--mei-border);
        }}

        .stTabs [data-baseweb="tab"] {{
            border-radius: var(--mei-radius-sm) var(--mei-radius-sm) 0 0;
            color: var(--mei-muted);
            font-weight: 600;
        }}

        .stTabs [aria-selected="true"] {{
            color: var(--mei-primary);
            background: var(--mei-primary-soft);
        }}

        .stAlert {{
            border-radius: var(--mei-radius-md);
        }}

        hr {{
            border-color: var(--mei-border);
        }}

        @media (max-width: 760px) {{
            .mei-app-header {{
                display: block;
                padding: 1.1rem;
            }}

            .mei-app-title {{
                font-size: 1.65rem;
            }}

            .mei-header-actions {{
                justify-content: flex-start;
                margin-top: 0.85rem;
                min-width: 0;
            }}

            .mei-empty-filter-state {{
                padding: 0.95rem;
            }}

            div[role="radiogroup"] {{
                width: 100%;
            }}

            div[role="radiogroup"] label {{
                flex: 1 1 9rem;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_plotly_theme(
    fig: Any,
    *,
    currency_axes: Sequence[str] = (),
    percent_axes: Sequence[str] = (),
    count_axes: Sequence[str] = (),
    height: int = 390,
) -> Any:
    """Apply the dashboard Plotly theme, including common BRL and percent formats."""

    fig.update_layout(
        autosize=True,
        colorway=PLOTLY_PALETTE,
        font={
            "family": "Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
            "color": THEME["color_text"],
            "size": 13,
        },
        height=height,
        hoverlabel={
            "bgcolor": THEME["color_surface"],
            "bordercolor": THEME["color_border"],
            "font_color": THEME["color_text"],
        },
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
            "title_text": "",
        },
        margin={"l": 24, "r": 18, "t": 58, "b": 32},
        paper_bgcolor=THEME["color_surface"],
        plot_bgcolor=THEME["color_surface"],
        title={
            "font": {"size": 16, "color": THEME["color_text"]},
            "x": 0,
            "xanchor": "left",
        },
    )
    fig.update_xaxes(
        automargin=True,
        gridcolor="rgba(217, 222, 231, 0.45)",
        linecolor=THEME["color_border"],
        tickfont={"color": THEME["color_muted"]},
        title_font={"color": THEME["color_muted"]},
        zeroline=False,
    )
    fig.update_yaxes(
        automargin=True,
        gridcolor="rgba(217, 222, 231, 0.7)",
        linecolor=THEME["color_border"],
        tickfont={"color": THEME["color_muted"]},
        title_font={"color": THEME["color_muted"]},
        zerolinecolor="rgba(217, 222, 231, 0.8)",
    )

    for axis in currency_axes:
        fig.update_layout({axis: {"tickprefix": "R$ ", "tickformat": ",.0f"}})
    for axis in percent_axes:
        fig.update_layout({axis: {"ticksuffix": "%", "tickformat": ",.1f"}})
    for axis in count_axes:
        fig.update_layout({axis: {"tickformat": ",.0f"}})

    fig.update_traces(
        hoverlabel={"namelength": -1},
        marker_line_color=THEME["color_surface"],
        marker_line_width=0.5,
    )
    fig.update_layout(hovermode="x unified")
    return fig


def render_dashboard_header(
    *,
    title: str,
    description: str,
    status_items: Sequence[str],
    actions: Sequence[str],
) -> None:
    """Render the executive page header with source status and action chips."""

    status_html = "".join(
        f'<span class="mei-status-pill mei-status-pill--success">{escape(item)}</span>'
        for item in status_items
    )
    action_html = "".join(
        f'<span class="mei-action-pill">{escape(action)}</span>'
        for action in actions
    )
    st.markdown(
        f"""
        <section class="mei-app-header">
            <div class="mei-app-header__content">
                <div class="mei-eyebrow">Produto analítico governado</div>
                <h1 class="mei-app-title">{escape(title)}</h1>
                <p class="mei-app-description">{escape(description)}</p>
                <div class="mei-header-meta">{status_html}</div>
            </div>
            <div class="mei-header-actions">{action_html}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_section_title(title: str, helper: str | None = None) -> None:
    """Render a compact section heading with optional helper copy."""

    helper_html = f'<p class="mei-helper-text">{escape(helper)}</p>' if helper else ""
    st.markdown(
        f"""
        <h2 class="mei-section-title">{escape(title)}</h2>
        {helper_html}
        """,
        unsafe_allow_html=True,
    )


def render_empty_filter_state(
    *,
    period: str,
    states: str,
    payments: str,
    categories: str,
) -> None:
    """Render the empty sales state for a filter combination with no rows."""

    items = [
        ("Período", period),
        ("Estados", states),
        ("Pagamentos", payments),
        ("Categorias", categories),
    ]
    items_html = "".join(
        f"""
        <div class="mei-empty-filter-state__item">
            <span class="mei-empty-filter-state__label">{escape(label)}</span>
            <span class="mei-empty-filter-state__value">{escape(value)}</span>
        </div>
        """
        for label, value in items
    )
    st.markdown(
        f"""
        <section class="mei-empty-filter-state">
            <span class="mei-empty-filter-state__eyebrow">Sem vendas no recorte</span>
            <h2 class="mei-empty-filter-state__title">Nenhuma venda encontrada para os filtros selecionados.</h2>
            <p class="mei-empty-filter-state__copy">
                Revise a combinação abaixo ou use <strong>Resetar filtros</strong> no painel lateral
                para voltar ao período completo da base antes de continuar a análise.
            </p>
            <div class="mei-empty-filter-state__grid">{items_html}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _table_column_config(rows: pd.DataFrame) -> dict[str, Any]:
    """Infer Streamlit column formatting from the already localized table labels."""

    column_config: dict[str, Any] = {}
    currency_terms = (
        "Receita",
        "Lucro",
        "Ticket",
        "Frete",
        "Desconto",
        "Subtotal",
        "Valor",
    )
    percent_terms = ("%", "Taxa", "Margem", "Participação", "Crescimento")
    count_terms = (
        "Pedidos",
        "Unidades",
        "Clientes",
        "Carrinhos",
        "Avaliações",
        "Itens",
        "Nota",
    )
    date_terms = ("Data", "Primeira compra", "Última compra")

    for column in rows.columns:
        series = rows[column]
        if column == "Ranking":
            column_config[column] = st.column_config.TextColumn(column, width="small")
        elif any(term in column for term in currency_terms):
            column_config[column] = st.column_config.NumberColumn(column, format="R$ %.2f")
        elif any(term in column for term in percent_terms):
            column_config[column] = st.column_config.NumberColumn(column, format="%.2f%%")
        elif pd.api.types.is_datetime64_any_dtype(series) or column in date_terms:
            column_config[column] = st.column_config.DateColumn(column, format="DD/MM/YYYY")
        elif pd.api.types.is_numeric_dtype(series) and any(term in column for term in count_terms):
            column_config[column] = st.column_config.NumberColumn(column, format="%d")
        elif pd.api.types.is_numeric_dtype(series):
            column_config[column] = st.column_config.NumberColumn(column, format="%.2f")
        else:
            column_config[column] = st.column_config.TextColumn(column)

    return column_config


def render_table(
    rows: pd.DataFrame,
    *,
    height: int,
    column_order: Sequence[str] | None = None,
    sort_by: str | None = None,
    sort_ascending: bool = False,
    rank: bool = False,
    hide_columns: Sequence[str] = (),
) -> None:
    """Render a formatted Streamlit dataframe for dashboard tables."""

    display = rows.copy()
    if sort_by and sort_by in display.columns:
        display = display.sort_values(sort_by, ascending=sort_ascending)
    if rank:
        display.insert(0, "Ranking", [f"#{index}" for index in range(1, len(display) + 1)])

    hidden = set(hide_columns)
    visible_columns = [column for column in display.columns if column not in hidden]
    if column_order:
        ordered = [column for column in column_order if column in display.columns and column not in hidden]
        ordered.extend(column for column in visible_columns if column not in ordered)
        visible_columns = ordered

    st.dataframe(
        display,
        width="stretch",
        hide_index=True,
        height=height,
        column_order=visible_columns,
        column_config=_table_column_config(display),
    )


def render_ai_status(*, use_gemini: bool, gemini_ready: bool) -> None:
    """Render the local/Gemini mode status for the QA panel."""

    gemini_text = "Ativado e configurado" if use_gemini and gemini_ready else "Aguardando configuração"
    if not use_gemini:
        gemini_text = "Desativado nesta pergunta"
    gemini_class = "success" if use_gemini and gemini_ready else "warning"
    st.markdown(
        f"""
        <section class="mei-ai-status">
            <div class="mei-ai-status__row">
                <span class="mei-ai-status__label">Modo local</span>
                <span class="mei-ai-status__value mei-ai-status__value--success">Sempre disponível</span>
            </div>
            <div class="mei-ai-status__row">
                <span class="mei-ai-status__label">Gemini</span>
                <span class="mei-ai-status__value mei-ai-status__value--{gemini_class}">
                    {escape(gemini_text)}
                </span>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_ai_empty_state(message: str) -> None:
    """Render a quiet empty state for the QA panel."""

    st.markdown(f'<section class="mei-ai-empty">{escape(message)}</section>', unsafe_allow_html=True)


def render_ai_message(*, label: str, title: str, body: str, tone: str = "local") -> None:
    """Render an AI answer container, then stream the markdown body below its heading."""

    body_html = escape(body)
    st.markdown(
        f"""
        <section class="mei-ai-message mei-ai-message--{escape(tone)}">
            <span class="mei-ai-message__label">{escape(label)}</span>
            <h3 class="mei-ai-message__title">{escape(title)}</h3>
            <p class="mei-ai-message__body">{body_html}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_period_selector(*, label: str, options: Sequence[str], key: str) -> str:
    """Render a session-state backed period selector with segmented-control styling."""

    st.markdown(
        f'<span class="mei-period-control__label">{escape(label)}</span>',
        unsafe_allow_html=True,
    )
    return st.radio(
        label,
        options,
        key=key,
        horizontal=True,
        label_visibility="collapsed",
    )


def render_primary_action_label(label: str) -> None:
    """Render a compact label above a primary Streamlit action."""

    st.markdown(
        f'<span class="mei-primary-action__label">{escape(label)}</span>',
        unsafe_allow_html=True,
    )


def render_kpi_groups(groups: Sequence[tuple[str, Sequence[dict[str, str | bool]]]]) -> None:
    """Render KPI cards grouped by business domain."""

    group_html = []
    for title, cards in groups:
        cards_html = []
        for card in cards:
            is_primary = bool(card.get("primary", False))
            emphasis_class = "mei-kpi-card--primary" if is_primary else "mei-kpi-card--secondary"
            delta = str(card.get("delta", "") or "")
            context = str(card.get("context", "") or "")
            delta_html = f'<span class="mei-kpi-card__delta">{escape(delta)}</span>' if delta else ""
            context_html = (
                f'<span class="mei-kpi-card__context">{escape(context)}</span>' if context else ""
            )
            cards_html.append(
                f"""
                <article class="mei-kpi-card {emphasis_class}">
                    <span class="mei-kpi-card__label">{escape(str(card["label"]))}</span>
                    <span class="mei-kpi-card__value">{escape(str(card["value"]))}</span>
                    {context_html}
                    {delta_html}
                </article>
                """
            )
        group_html.append(
            f"""
            <section class="mei-kpi-domain">
                <h3 class="mei-kpi-domain__title">{escape(title)}</h3>
                <div class="mei-kpi-grid">{''.join(cards_html)}</div>
            </section>
            """
        )

    st.html("".join(group_html))


def render_sidebar_filter_panel_intro() -> None:
    """Render the sidebar filter panel heading."""

    st.sidebar.markdown(
        """
        <section class="mei-sidebar-panel">
            <div class="mei-sidebar-panel__eyebrow">Filtros globais</div>
            <h2 class="mei-sidebar-panel__title">Recorte da análise</h2>
            <p class="mei-sidebar-panel__copy">
                Ajuste período, praça, pagamento e categoria para atualizar todas as abas.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_filter_summary(items: Sequence[tuple[str, str]]) -> None:
    """Render a compact summary of the active sidebar filters."""

    summary_html = "".join(
        f"""
        <div class="mei-filter-summary__item">
            <span class="mei-filter-summary__label">{escape(label)}</span>
            <span class="mei-filter-summary__value">{escape(value)}</span>
        </div>
        """
        for label, value in items
    )
    st.sidebar.markdown(
        f"""
        <section class="mei-sidebar-panel">
            <div class="mei-sidebar-panel__eyebrow">Estado atual</div>
            <div class="mei-filter-summary">{summary_html}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_divider() -> None:
    """Render a subtle divider inside the sidebar."""

    st.sidebar.markdown('<div class="mei-sidebar-divider"></div>', unsafe_allow_html=True)
