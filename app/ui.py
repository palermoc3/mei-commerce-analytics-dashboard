"""Shared visual presentation helpers for the Streamlit app."""

from __future__ import annotations

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
        </style>
        """,
        unsafe_allow_html=True,
    )
