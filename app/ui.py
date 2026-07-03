"""Shared visual presentation helpers for the Streamlit app."""

from __future__ import annotations

from collections.abc import Sequence
from html import escape

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
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


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
