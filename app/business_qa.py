"""Governed local answers for common MEI commerce business questions."""

from __future__ import annotations

from collections.abc import Mapping

import pandas as pd

from app.charts import (
    calculate_core_kpis,
    category_performance,
    customer_retention_summary,
    payment_method_summary,
    product_ranking,
    revenue_by_state,
    top_customers,
)


def _format_brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _normalize(text: str) -> str:
    replacements = {
        "á": "a",
        "à": "a",
        "â": "a",
        "ã": "a",
        "é": "e",
        "ê": "e",
        "í": "i",
        "ó": "o",
        "ô": "o",
        "õ": "o",
        "ú": "u",
        "ç": "c",
    }
    normalized = text.lower()
    for source, target in replacements.items():
        normalized = normalized.replace(source, target)
    return normalized


def answer_from_workbook(question: str, sheets: Mapping[str, pd.DataFrame]) -> str:
    """Answer common questions from workbook metrics without external APIs."""

    fato = sheets["Fato Vendas"]
    normalized = _normalize(question)
    kpis = calculate_core_kpis(fato)

    if any(token in normalized for token in ["receita", "faturamento", "vendas total"]):
        return (
            "Receita total de pedidos concluídos: "
            f"{_format_brl(kpis['revenue'])}. "
            "Grão: pedido. Fórmula: deduplicar `Fato Vendas` por `ID Venda` "
            "e somar `Total do Pedido (R$)`. Essa receita inclui frete e "
            "subtrai descontos; pedidos `pending` ficam fora do padrão."
        )

    if any(token in normalized for token in ["lucro", "margem"]):
        categories = category_performance(fato)
        leader = categories.iloc[0]
        return (
            f"Lucro bruto total: {_format_brl(kpis['gross_profit'])}, "
            f"com margem bruta de {kpis['gross_margin_percent']:.2f}%. "
            "Grão: item. Fórmula: somar `Lucro Bruto Item (R$)` e dividir "
            "por `Subtotal Item (R$)` para margem. A categoria com maior "
            f"lucro bruto é `{leader['Categoria']}` "
            f"({_format_brl(float(leader['gross_profit']))})."
        )

    if any(token in normalized for token in ["categoria", "departamento"]):
        categories = category_performance(fato)
        leader = categories.iloc[0]
        return (
            f"A principal categoria por receita item é `{leader['Categoria']}` "
            f"com {_format_brl(float(leader['item_revenue']))}. "
            "Grão: item. Fórmula: agrupar por `Categoria` e somar "
            "`Subtotal Item (R$)`. `Departamento` duplica `Categoria`, então "
            "não há hierarquia adicional confiável."
        )

    if any(token in normalized for token in ["produto", "ranking", "mais vendido"]):
        top = product_ranking(fato, limit=1).iloc[0]
        return (
            f"O produto líder por receita item é `{top['Produto']}` "
            f"({_format_brl(float(top['item_revenue']))}, "
            f"{int(top['units_sold'])} unidades). "
            "Grão: item. Fórmula: agrupar por `Produto` e somar "
            "`Subtotal Item (R$)`, ordenando por receita e depois unidades."
        )

    if any(
        token in normalized
        for token in ["cliente", "clientes", "retencao", "recorrente", "lifetime"]
    ):
        retention = customer_retention_summary(fato)
        leader = top_customers(fato, sheets.get("Dimensão Clientes"), limit=1).iloc[0]
        return (
            f"Clientes ativos com pedidos concluídos: {retention['active_customers']}. "
            f"Clientes recorrentes: {retention['repeat_customers']} "
            f"({retention['repeat_customer_rate_percent']:.2f}%). "
            f"Receita média por cliente: {_format_brl(retention['average_customer_revenue'])}. "
            f"O cliente líder por receita é `{leader['Nome Cliente']}` "
            f"({_format_brl(float(leader['revenue']))}, "
            f"{int(leader['completed_orders'])} pedidos). "
            "Grão: pedido. Fórmula: deduplicar `Fato Vendas` por `ID Venda`, "
            "agrupar por `ID Cliente` e somar `Total do Pedido (R$)`."
        )

    if any(token in normalized for token in ["estado", "uf", "regiao"]):
        state = revenue_by_state(fato).iloc[0]
        return (
            f"O estado líder por receita de pedidos é `{state['Estado Cliente']}` "
            f"com {_format_brl(float(state['revenue']))}. "
            "Grão: pedido. Fórmula: deduplicar por `ID Venda`, agrupar por "
            "`Estado Cliente` e somar `Total do Pedido (R$)`."
        )

    if any(token in normalized for token in ["pagamento", "pix", "cartao", "credito"]):
        payment = payment_method_summary(fato).iloc[0]
        return (
            f"O método de pagamento com mais pedidos concluídos é "
            f"`{payment['Metodo Pagamento']}` com "
            f"{int(payment['completed_orders'])} pedidos. "
            "Grão: pedido. Fórmula: deduplicar por `ID Venda`, agrupar por "
            "`Metodo Pagamento` e contar pedidos."
        )

    if any(token in normalized for token in ["cupom", "desconto"]):
        return (
            f"Descontos concedidos em pedidos concluídos: "
            f"{_format_brl(kpis['discount_total'])}. "
            "Grão: pedido. Fórmula: deduplicar por `ID Venda` e somar "
            "`Desconto Cupom (R$)`. Limitação: a atribuição de código de "
            "cupom não está disponível; `Cupom Utilizado` é `NENHUM`."
        )

    return (
        "Consigo responder com segurança sobre receita, lucro, margem, "
        "categoria, produto, clientes, retenção, estado, pagamento, descontos, carrinhos e reviews. "
        "Antes de calcular, identifique se a pergunta é de grão pedido, item "
        "ou operação. Para receita de pedido, deduplique por `ID Venda`; para "
        "produto/categoria, use campos de item."
    )
