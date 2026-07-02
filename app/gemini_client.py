"""Optional Gemini integration for governed business analytics answers."""

from __future__ import annotations

import os
from pathlib import Path


DEFAULT_MODEL = "gemini-1.5-flash"
DEFAULT_PROMPT_PATH = Path("prompts/system_prompt.md")


class GeminiConfigurationError(RuntimeError):
    """Raised when the Gemini client cannot be configured safely."""


def load_system_prompt(path: str | Path = DEFAULT_PROMPT_PATH) -> str:
    prompt_path = Path(path)
    if not prompt_path.exists():
        raise FileNotFoundError(f"System prompt not found: {prompt_path}")
    prompt = prompt_path.read_text(encoding="utf-8").strip()
    if not prompt:
        raise GeminiConfigurationError(f"System prompt is empty: {prompt_path}")
    return prompt


def build_business_context(kpi_summary: dict[str, float | int]) -> str:
    """Create a compact context block with computed, sourced metrics."""

    lines = [
        "Computed workbook metrics:",
        f"- Completed orders: {kpi_summary['completed_orders']}",
        f"- Completed order revenue: R$ {kpi_summary['revenue']:,.2f}",
        f"- Item revenue: R$ {kpi_summary['item_revenue']:,.2f}",
        f"- Gross profit: R$ {kpi_summary['gross_profit']:,.2f}",
        f"- Gross margin: {kpi_summary['gross_margin_percent']:.2f}%",
        f"- Average ticket: R$ {kpi_summary['average_ticket']:,.2f}",
        f"- Units sold: {kpi_summary['units_sold']}",
        "",
        "Revenue uses deduplicated Fato Vendas by ID Venda.",
        "Product and category analytics use item-level fields.",
    ]
    return "\n".join(lines)


def answer_business_question(
    question: str,
    kpi_summary: dict[str, float | int],
    model_name: str = DEFAULT_MODEL,
) -> str:
    """Answer a question with Gemini using the governed system prompt.

    The function imports the SDK lazily so the dashboard can run without AI
    features when `google-generativeai` or the API key are absent.
    """

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise GeminiConfigurationError("Set GEMINI_API_KEY to enable Gemini answers.")

    try:
        import google.generativeai as genai
    except ModuleNotFoundError as exc:
        raise GeminiConfigurationError(
            "Install google-generativeai to enable Gemini answers."
        ) from exc

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=load_system_prompt(),
    )
    prompt = f"{build_business_context(kpi_summary)}\n\nUser question:\n{question}"
    response = model.generate_content(prompt)
    return getattr(response, "text", "").strip()
