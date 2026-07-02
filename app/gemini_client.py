"""Optional Gemini integration for governed business analytics answers."""

from __future__ import annotations

import os
from pathlib import Path


DEFAULT_MODEL = "gemini-1.5-flash"
DEFAULT_PROMPT_PATH = Path("prompts/system_prompt.md")
DEFAULT_ENV_PATH = Path(".env")
DEFAULT_SYSTEM_PROMPT = """
You are a business analytics assistant for a Brazilian MEI ecommerce workbook.
Use completed purchases (`paid` and `shipped`) for default sales analytics.
`Fato Vendas` is item-grain, so deduplicate by `ID Venda` before summing
order-level fields such as `Total do Pedido (R$)`, shipping, or discounts.
Use item fields for product and category analytics. State source, grain,
formula, filters, and limitations. Do not infer coupon-code attribution.
""".strip()


class GeminiConfigurationError(RuntimeError):
    """Raised when the Gemini client cannot be configured safely."""


def load_system_prompt(path: str | Path = DEFAULT_PROMPT_PATH) -> str:
    prompt_path = Path(path)
    if not prompt_path.exists():
        return DEFAULT_SYSTEM_PROMPT
    prompt = prompt_path.read_text(encoding="utf-8").strip()
    if not prompt:
        raise GeminiConfigurationError(f"System prompt is empty: {prompt_path}")
    return prompt


def load_env_file(path: str | Path = DEFAULT_ENV_PATH) -> dict[str, str]:
    """Load simple KEY=VALUE pairs without overriding existing environment."""

    env_path = Path(path)
    loaded: dict[str, str] = {}
    if not env_path.exists():
        return loaded

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key or key in os.environ:
            continue
        os.environ[key] = value
        loaded[key] = value
    return loaded


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

    load_env_file()
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
