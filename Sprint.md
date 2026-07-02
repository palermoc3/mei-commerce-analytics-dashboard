# Sprint Roadmap

## Project State

- Product: AI analytics assistant for a Brazilian MEI ecommerce workbook.
- Data source: `data/dataset_analitico_mei.xlsx`, 11 sheets, schema validated.
- Business source: `docs/AI_BUSINESS_KNOWLEDGE_BASE.md`.
- Current app state: dashboard, analytics, local QA, optional Gemini, report export, tests, and CI are implemented.
- Delivery mode: CI/CD, small branches, evidence-first PRs, Conventional Commits.

## Non-Negotiable Rules

- Default sales analytics use only completed purchases: `paid` and `shipped`.
- `Fato Vendas` is item-grain; order totals repeat by item row.
- Deduplicate by `ID Venda` before summing `Total do Pedido (R$)`.
- Product/category analytics use `Subtotal Item (R$)`, `Quantidade Item`, and `Lucro Bruto Item (R$)`.
- Coupon code attribution is unavailable; discount amount is the reliable field.
- Every task must include an acceptance command and CI evidence.

## Team

| Agent | Role |
| --- | --- |
| Lider | Roadmap, dispatch, scope control, merge approval |
| MARCO | Python implementation, data loading, charts, app, tests |
| LENA | Technical review, formulas, CI gates, security |
| DIANA | Knowledge base, prompt, user-facing AI behavior |

## Sprint 0 - Baseline

Goal: make the workspace buildable and verifiable.

| Task | Agent | Branch | Commit | Gate |
| --- | --- | --- | --- | --- |
| `project-health-check` | LENA | `chore/project-health-check` | `chore(app): document project baseline` | `python -m compileall app` |
| `add-dependencies` | MARCO | `chore/dependencies` | `chore(deps): add analytics dependencies` | clean install succeeds |
| `validate-workbook-contract` | MARCO | `test/workbook-contract` | `test(data): validate workbook contract` | sheet and column check passes |
| `seed-system-prompt` | DIANA | `docs/system-prompt` | `docs(prompt): add analytics system prompt` | prompt mentions grain and dedup rules |

Exit: CI installs dependencies, compiles app, and validates the workbook schema.

## Sprint 1 - Analytics Core

Goal: implement trusted metrics before UI or AI answers.

| Task | Agent | Branch | Commit | Gate |
| --- | --- | --- | --- | --- |
| `load-workbook-sheets` | MARCO | `feat/load-workbook-sheets` | `feat(data-loader): load workbook sheets into dataframes` | loader smoke test passes |
| `calculate-core-kpis` | MARCO | `feat/core-kpis` | `feat(charts): calculate core ecommerce kpis` | KPI values match KB |
| `add-analytics-tests` | MARCO | `test/analytics-formulas` | `test(charts): validate analytics formulas` | tests catch repeated order-total sums |
| `review-metric-contract` | LENA | `review/metric-contract` | `docs(agents): record metric review` | no P0 formula findings |

Exit: KPIs match the knowledge base: 2,127 orders, R$ 160,692.02 revenue, R$ 73,807.63 gross profit, 48.85% margin.

## Sprint 2 - Dashboard MVP

Goal: ship a usable analytics dashboard.

| Task | Agent | Branch | Commit | Gate |
| --- | --- | --- | --- | --- |
| `render-kpi-dashboard` | MARCO | `feat/kpi-dashboard` | `feat(app): render ecommerce kpi dashboard` | app renders without crash |
| `add-product-category-charts` | MARCO | `feat/product-category-charts` | `feat(charts): add product and category charts` | charts use item fields |
| `add-payment-state-views` | MARCO | `feat/payment-state-views` | `feat(charts): add payment and state views` | order data is deduplicated |
| `document-dashboard-scope` | DIANA | `docs/dashboard-scope` | `docs(knowledge-base): document dashboard scope` | docs list shipped views |

Exit: users can inspect KPIs, category performance, product ranking, payment mix, and state revenue.

## Sprint 3 - AI Business QA

Goal: answer business questions with governed context.

| Task | Agent | Branch | Commit | Gate |
| --- | --- | --- | --- | --- |
| `build-context-pack` | DIANA | `docs/context-pack` | `docs(prompt): add business context pack` | source priority is explicit |
| `add-gemini-client` | MARCO | `feat/gemini-client` | `feat(gemini): add env-based ai client` | missing key fails clearly |
| `answer-business-questions` | MARCO | `feat/business-qa` | `feat(app): answer business analytics questions` | sample answers cite formulas |
| `review-ai-behavior` | LENA + DIANA | `review/ai-behavior` | `docs(agents): record ai behavior review` | no unsupported coupon/status claims |

Exit: AI answers state grain, metric formula, filters, period, and limitations when relevant.

## Sprint 4 - CI/CD Hardening

Goal: protect main with repeatable checks.

| Task | Agent | Branch | Commit | Gate |
| --- | --- | --- | --- | --- |
| `add-test-command` | MARCO | `chore/test-command` | `chore(tests): add standard test command` | one command runs all checks |
| `add-ci-workflow` | MARCO | `chore/ci-workflow` | `chore(deps): add ci workflow` | CI runs install, compile, tests, schema |
| `add-pr-template` | DIANA | `docs/pr-template` | `docs(agents): add pr evidence template` | PRs require command output |
| `enforce-merge-protocol` | Lider | `docs/merge-protocol` | `docs(agents): define merge protocol` | LENA and Lider approvals required |

Exit: every PR is small, tested, reviewed, and traceable.

## Sprint 5 - Completion

Goal: finish the demo-quality product.

| Task | Agent | Branch | Commit | Gate |
| --- | --- | --- | --- | --- |
| `handle-workbook-errors` | MARCO | `fix/workbook-errors` | `fix(data-loader): handle workbook errors clearly` | negative tests pass |
| `add-cart-review-insights` | MARCO | `feat/cart-review-insights` | `feat(charts): add cart and review insights` | formulas match KB |
| `add-report-export` | MARCO | `feat/report-export` | `feat(app): export analytics report` | export smoke test passes |
| `final-docs-sync` | DIANA | `docs/final-sync` | `docs(knowledge-base): sync shipped behavior` | no stale prompt/docs behavior |

Exit: the project has data loading, validated metrics, dashboard, AI QA, tests, CI/CD, docs, and review workflow.

## Sprint 6 - Post-MVP Packaging

Goal: make the project easy to run, inspect, and version.

| Task | Agent | Branch | Commit | Gate |
| --- | --- | --- | --- | --- |
| `add-readme` | DIANA | `docs/readme` | `docs(app): document setup and usage` | README explains setup, run, checks, export |
| `add-env-example` | MARCO | `chore/env-example` | `chore(app): add environment example` | no secrets committed |
| `mark-python-package` | MARCO | `chore/package-init` | `chore(app): mark app as python package` | imports work from Streamlit and scripts |
| `initial-versioning` | Lider | `chore/initial-versioning` | `chore(repo): create initial project snapshot` | `python scripts/run_checks.py` passes before commit |

Exit: a new developer can clone, install, run the dashboard, run checks, export a report, and review the analytics rules from docs.

## CI Gates

Required on every PR:

```bash
python scripts/run_checks.py
```

This command runs compile checks, workbook contract validation, KPI validation, and the analytics unit test suite.

## Merge Policy

- One task per branch.
- One Conventional Commit per task when practical.
- No merge without CI evidence.
- No merge if revenue, margin, status filtering, or grain handling is disputed.
- Docs and prompt must change with behavior changes.
