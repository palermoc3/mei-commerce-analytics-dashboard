# MEI Commerce AI Analytics

Dashboard e assistente analítico em Python para uma base sintética de ecommerce MEI brasileira. O projeto transforma uma planilha Excel com vendas, clientes, produtos, carrinhos, avaliações e cupons em um painel Streamlit com KPIs confiáveis, análises de negócio, relatório Markdown e respostas locais governadas por regra de negócio.

Este repositório foi organizado para portfólio: mostra produto funcionando, cuidado com qualidade de dados, testes automatizados, documentação de domínio e uso responsável de IA no fluxo de desenvolvimento.

## Demonstração Do Produto

- Dashboard Streamlit com abas de vendas, comparação de períodos, produtos, clientes, operação e AI QA.
- Filtros por período, estado, método de pagamento e categoria.
- KPIs de pedidos concluídos, receita, ticket médio, lucro bruto, margem, unidades, produtos ativos, avaliações e carrinhos.
- Análises de retenção com clientes ativos, recorrentes, receita média por cliente, top clientes e coortes mensais.
- Visões operacionais de carrinhos, reviews, pedidos pending e impacto de frete/desconto.
- Respostas locais para perguntas de negócio sem depender de API externa.
- Integração Gemini opcional via `GEMINI_API_KEY`.
- Exportação de relatório Markdown pela UI ou CLI.
- CI com um gate único de qualidade.

## Stack

- Python
- Pandas
- Streamlit
- Plotly
- OpenPyXL
- Unittest
- GitHub Actions
- Gemini opcional

## O Problema Técnico

A planilha principal, `Fato Vendas`, está em grão de item: uma venda com vários produtos aparece em várias linhas. Isso cria um risco clássico de BI: somar `Total do Pedido (R$)` direto nas linhas infla a receita.

A solução implementada separa métricas por grão:

- Receita, frete, desconto, ticket médio, clientes e pagamento: deduplicam por `ID Venda`.
- Produto e categoria: usam `Subtotal Item (R$)`, `Quantidade Item` e `Lucro Bruto Item (R$)`.
- Pipeline operacional: usa `Purchases`, porque pedidos `pending` não entram em vendas concluídas.
- Cupons: o app informa a limitação em vez de inventar atribuição de código.

## Por Que Este Projeto Mostra Prontidão Júnior

- Entendo regra de negócio antes de codar: o projeto tem um KB em `docs/AI_BUSINESS_KNOWLEDGE_BASE.md` explicando fontes, grãos, fórmulas e limitações.
- Sei proteger métricas com testes: há regressões para impedir soma errada de receita em tabela item-grain.
- Sei transformar dados em produto: não é só notebook; existe dashboard, CLI, relatório exportável e QA local.
- Sei trabalhar com qualidade: `scripts/run_checks.py` roda compile, contratos de dados, validação de KPIs, smoke test, auditoria de completude e testes unitários.
- Sei lidar com incerteza: quando a planilha não permite atribuir cupom por código, o app comunica a limitação.
- Sei usar IA com responsabilidade: IA apoia o fluxo, mas as respostas são ancoradas em dados, testes e regras explícitas.

## Como Usei IA Neste Projeto

Usei agentes de IA como apoio de desenvolvimento para organizar tarefas, revisar regras de negócio, mapear riscos de métricas e acelerar documentação. Mantive os bastidores de agente fora da vitrine do portfólio em `trash/`, mas preservei no projeto o que importa para avaliação técnica: código, testes, contrato de negócio, validações e README.

A parte de IA do produto também foi tratada com cuidado: o dashboard funciona sem Gemini usando respostas locais governadas. Quando Gemini é ativado, ele recebe contexto calculado pelo app e instruções para respeitar grão, fórmulas, filtros e limitações.

## Como Rodar

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
streamlit run app/main.py --server.address 0.0.0.0 --server.port 8502
```

Abra:

```text
http://localhost:8502
```

Para usar Gemini, copie `.env.example` para `.env` e configure `GEMINI_API_KEY`. O app continua funcionando sem essa chave.

## Qualidade E Verificação

```bash
python scripts/run_checks.py
```

Esse comando executa:

- Compile de `app`, `scripts` e `tests`.
- Validação da knowledge base.
- Validação do contrato da planilha.
- Validação de contratos de negócio.
- Validação dos KPIs esperados.
- Smoke test do app.
- Auditoria de completude com `python scripts/validate_project_completion.py`.
- Testes unitários.

## Exportar Relatório

```bash
python scripts/export_report.py reports/mei_commerce_report.md
```

Também é possível usar o entrypoint do app:

```bash
python app/main.py --cli
python app/main.py --export-report reports/mei_commerce_report.md
```

## Métricas Validadas

- Pedidos concluídos: `2.127`
- Receita de pedidos: `R$ 160.692,02`
- Receita item: `R$ 151.081,10`
- Lucro bruto: `R$ 73.807,63`
- Margem bruta: `48,85%`
- Ticket médio: `R$ 75,55`
- Unidades vendidas: `3.279`
- Clientes ativos: `180`
- Clientes recorrentes: `180`
- Receita média por cliente: `R$ 892,73`

## Estrutura

```text
app/
  business_qa.py      respostas locais governadas
  charts.py           KPIs, retenção e tabelas para gráficos
  data_loader.py      loader e validação da planilha
  gemini_client.py    integração Gemini opcional
  main.py             dashboard Streamlit
  reporting.py        export Markdown
data/
  dataset_analitico_mei.xlsx
docs/
  AI_BUSINESS_KNOWLEDGE_BASE.md
scripts/
  run_checks.py
  validate_workbook_contract.py
  validate_business_contracts.py
  validate_knowledge_base.py
  validate_kpis.py
  validate_project_completion.py
  smoke_app.py
  export_report.py
tests/
  test_analytics.py
trash/
  materiais internos de planejamento/agentes movidos para revisão manual
```
