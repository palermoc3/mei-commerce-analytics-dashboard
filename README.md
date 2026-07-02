# MEI Commerce AI Analytics

Dashboard e assistente analítico para uma base sintética de ecommerce MEI brasileira.

O projeto usa `data/dataset_analitico_mei.xlsx` como snapshot analítico e `docs/AI_BUSINESS_KNOWLEDGE_BASE.md` como contrato de negócio. A regra mais importante: `Fato Vendas` está em grão de item, então receita de pedido deve deduplicar por `ID Venda` antes de somar `Total do Pedido (R$)`.

## Funcionalidades

- Dashboard Streamlit com KPIs, vendas, produtos, operação e QA.
- Filtros por período, estado, método de pagamento e categoria.
- Comparação entre dois períodos com delta e crescimento percentual.
- Validação de contrato da planilha.
- KPIs governados por fórmulas documentadas.
- Testes contra regressões de grão e receita.
- Respostas locais para perguntas comuns de negócio.
- Integração Gemini opcional via `GEMINI_API_KEY`.
- Export de relatório Markdown.
- Download de relatório Markdown filtrado no dashboard.
- CI GitHub Actions com o gate padrão.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Para usar Gemini, copie `.env.example` para `.env` e configure `GEMINI_API_KEY`. O app carrega `.env` local sem sobrescrever variáveis já exportadas no ambiente. O dashboard funciona sem Gemini usando respostas locais governadas.

## Rodar o Dashboard

```bash
streamlit run app/main.py --server.address 0.0.0.0 --server.port 8502
```

Abra:

```text
http://localhost:8502
```

## Verificar o Projeto

```bash
python scripts/run_checks.py
```

Esse comando compila o app, valida a planilha, valida KPIs e roda os testes.
Ele também executa `scripts/smoke_app.py`, que percorre loader, KPIs, QA local, filtros e relatório.

Para rodar apenas o smoke test:

```bash
python scripts/smoke_app.py
```

## Exportar Relatório

```bash
python scripts/export_report.py reports/mei_commerce_report.md
```

Também é possível usar o entrypoint do app:

```bash
python app/main.py --cli
python app/main.py --export-report reports/mei_commerce_report.md
```

## Métricas Principais Esperadas

- Pedidos concluídos: `2.127`
- Receita de pedidos: `R$ 160.692,02`
- Receita item: `R$ 151.081,10`
- Lucro bruto: `R$ 73.807,63`
- Margem bruta: `48,85%`
- Ticket médio: `R$ 75,55`
- Unidades vendidas: `3.279`

## Estrutura

```text
app/
  business_qa.py      respostas locais governadas
  charts.py           KPIs e tabelas para gráficos
  data_loader.py      loader e validação da planilha
  gemini_client.py    integração Gemini opcional
  main.py             dashboard Streamlit
  reporting.py        export Markdown
docs/
  AI_BUSINESS_KNOWLEDGE_BASE.md
  agents/
prompts/
  system_prompt.md
scripts/
  run_checks.py
  validate_workbook_contract.py
  validate_kpis.py
  export_report.py
tests/
  test_analytics.py
```

## Regras Analíticas

- Use `paid` e `shipped` como escopo padrão de vendas concluídas.
- Deduplicate `Fato Vendas` por `ID Venda` para receita, frete e desconto de pedido.
- Use `Subtotal Item (R$)`, `Quantidade Item` e `Lucro Bruto Item (R$)` para produto/categoria.
- Em comparação de períodos, crescimento é `(período atual - período anterior) / período anterior * 100`.
- Não inferir código de cupom: a atribuição não existe no snapshot.
- `Departamento` duplica `Categoria`.
