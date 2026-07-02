"""Streamlit dashboard for the MEI commerce analytics workbook."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.charts import (
    calculate_core_kpis,
    cart_summary,
    cart_recovery_table,
    cart_status_summary,
    category_performance,
    filter_sales,
    monthly_gross_profit,
    monthly_revenue,
    payment_method_summary,
    product_ranking,
    rating_distribution,
    revenue_by_state,
    review_summary,
)
from app.business_qa import answer_from_workbook
from app.data_loader import DEFAULT_WORKBOOK_PATH, load_workbook
from app.gemini_client import GeminiConfigurationError, answer_business_question
from app.reporting import build_markdown_report_from_sheets, write_markdown_report


def _format_brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _print_cli_report(path: Path = DEFAULT_WORKBOOK_PATH) -> None:
    sheets = load_workbook(path)
    fato = sheets["Fato Vendas"]
    kpis = calculate_core_kpis(fato)
    print("MEI Commerce AI Analytics")
    print(f"Workbook: {path}")
    print(f"Completed orders: {kpis['completed_orders']}")
    print(f"Revenue: {_format_brl(kpis['revenue'])}")
    print(f"Item revenue: {_format_brl(kpis['item_revenue'])}")
    print(f"Gross profit: {_format_brl(kpis['gross_profit'])}")
    print(f"Gross margin: {kpis['gross_margin_percent']:.2f}%")
    print(f"Average ticket: {_format_brl(kpis['average_ticket'])}")
    print(f"Units sold: {kpis['units_sold']}")


def _filter_note(
    start_date,
    end_date,
    states: list[str],
    payments: list[str],
    categories: list[str],
) -> str:
    return "\n".join(
        [
            f"- Period: {start_date} to {end_date}",
            f"- States: {', '.join(states) if states else 'all'}",
            f"- Payment methods: {', '.join(payments) if payments else 'all'}",
            f"- Categories: {', '.join(categories) if categories else 'all'}",
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
    st.title("MEI Commerce AI Analytics")
    st.caption(
        "Dashboard governado por `docs/AI_BUSINESS_KNOWLEDGE_BASE.md` e pela planilha analítica."
    )

    try:
        sheets = load_workbook(DEFAULT_WORKBOOK_PATH)
    except Exception as exc:
        st.error(f"Não foi possível carregar a planilha: {exc}")
        st.stop()

    fato = sheets["Fato Vendas"]
    full_dates = pd.to_datetime(fato["Data Compra"], utc=True).dt.date

    st.sidebar.header("Filtros")
    date_range = st.sidebar.date_input(
        "Período",
        value=(full_dates.min(), full_dates.max()),
        min_value=full_dates.min(),
        max_value=full_dates.max(),
    )
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = full_dates.min()
        end_date = full_dates.max()

    selected_states = st.sidebar.multiselect(
        "Estados",
        sorted(fato["Estado Cliente"].dropna().unique()),
    )
    selected_payments = st.sidebar.multiselect(
        "Pagamentos",
        sorted(fato["Metodo Pagamento"].dropna().unique()),
    )
    selected_categories = st.sidebar.multiselect(
        "Categorias",
        sorted(fato["Categoria"].dropna().unique()),
    )

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

    kpis = calculate_core_kpis(fato)
    reviews = review_summary(sheets["Reviews"])
    carts = cart_summary(sheets["Carts"], sheets["Cart Items"])

    st.subheader("KPIs principais")
    report_text = build_markdown_report_from_sheets(
        sheets,
        fato_override=fato,
        filter_note=_filter_note(
            start_date,
            end_date,
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

    tab_sales, tab_products, tab_ops, tab_ai = st.tabs(
        ["Vendas", "Produtos", "Operação", "AI QA"]
    )

    with tab_sales:
        monthly = monthly_revenue(fato)
        profit = monthly_gross_profit(fato)
        states = revenue_by_state(fato)
        payments = payment_method_summary(fato)

        st.plotly_chart(
            px.line(
                monthly,
                x="Mes",
                y="revenue",
                markers=True,
                title="Receita mensal de pedidos concluídos",
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
            ),
            width="stretch",
        )
        col_b.plotly_chart(
            px.bar(
                payments,
                x="Metodo Pagamento",
                y="completed_orders",
                title="Pedidos por método de pagamento",
            ),
            width="stretch",
        )
        st.dataframe(profit, width="stretch", hide_index=True)

    with tab_products:
        categories = category_performance(fato)
        products = product_ranking(fato, limit=12)
        col_a, col_b = st.columns(2)
        col_a.plotly_chart(
            px.bar(
                categories,
                x="Categoria",
                y="item_revenue",
                title="Receita item por categoria",
            ),
            width="stretch",
        )
        col_b.plotly_chart(
            px.bar(
                categories,
                x="Categoria",
                y="gross_profit",
                title="Lucro bruto por categoria",
            ),
            width="stretch",
        )
        st.dataframe(products, width="stretch", hide_index=True)

    with tab_ops:
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Carrinhos abertos", carts["open_carts"])
        col_b.metric("Carrinhos abandonados", carts["abandoned_carts"])
        col_c.metric("Valor em carrinhos", _format_brl(carts["cart_item_value"]))
        col_a, col_b = st.columns(2)
        col_a.plotly_chart(
            px.bar(
                cart_status_summary(sheets["Carts"], sheets["Cart Items"]),
                x="Status",
                y="cart_value",
                title="Valor de carrinhos por status",
            ),
            width="stretch",
        )
        col_b.plotly_chart(
            px.bar(
                rating_distribution(sheets["Reviews"]),
                x="rating",
                y="review_count",
                title="Distribuição de avaliações",
            ),
            width="stretch",
        )
        st.dataframe(
            cart_recovery_table(sheets["Carts"], sheets["Cart Items"], sheets["Users"]),
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
