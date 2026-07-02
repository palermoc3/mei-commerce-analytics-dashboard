# AI Business Knowledge Base

## Project Overview

This project models a small Brazilian MEI-style ecommerce business and uses the analytics workbook at `data/dataset_analitico_mei.xlsx`. The business sells low-ticket retail products across six categories: `vestuario`, `casa`, `papelaria`, `eletronicos`, `beleza`, and `alimentos`.

Future AI agents should use this document as the business handoff for answering questions, explaining metrics, and generating charts. The source materials analyzed were:

- `data/dataset_analitico_mei.xlsx`: exported analytical dataset and raw operational tables.
- `db/seeds.rb`: deterministic synthetic business dataset generator.
- `test/`: authoritative expected behavior, validations, analytics formulas, and export requirements.

The workbook contains 24 months of transactions from `2024-07-01` through `2026-06-30`. It includes 2,208 purchases, of which 2,127 are completed (`paid` or `shipped`) and 81 are `pending`. The analytical fact sheet contains only completed purchases.

## Source Of Truth Priority

Use these sources in this order when resolving conflicts:

1. Tests in `test/`: authoritative behavior and business rules.
2. Model/query/service implementation implied by tests: exact formulas and associations.
3. `data/dataset_analitico_mei.xlsx`: current analytical data snapshot.
4. `db/seeds.rb`: deterministic generation rules, enumerations, default populations, and assumptions.

## Business Glossary

- Customer: A `User` who can purchase, review products, and own one cart.
- Product: Sellable item with category, sale price, cost price, stock, and active flag.
- Purchase / Order / Venda: Customer order with status, payment method, purchase date, subtotal, shipping, discount, and total.
- Completed purchase: A purchase with status `paid` or `shipped`. This is the default scope for revenue and profit analytics.
- Pending purchase: An order not yet completed. Present in raw `Purchases` and `Item Purchases`, excluded from `Fato Vendas` and business query revenue metrics.
- Item purchase: Product line item inside a purchase.
- Cart: Pre-purchase basket with status `open`, `checked_out`, or `abandoned`.
- Cart item: Product line item inside a cart.
- Coupon: Discount instrument with type `percentage` or `fixed_amount`.
- Review: Product rating from 1 to 5, unique per customer-product pair.
- Revenue: Usually `Purchase.total_amount` for order-level metrics; use item subtotal for product/category item sales.
- Gross profit / gross margin: Item subtotal minus product cost times quantity.
- Average ticket: Completed order revenue divided by completed order count.

## Workbook Structure

`data/dataset_analitico_mei.xlsx` has 11 sheets:

| Sheet | Rows | Purpose |
| --- | ---: | --- |
| `Fato Vendas` | 3,113 | Analytics fact table at completed purchase item grain. |
| `Dimensão Produtos` | 36 | Product dimension limited to products sold in completed purchases. |
| `Dimensão Clientes` | 180 | Customer dimension limited to customers with completed purchases. |
| `Users` | 180 | Raw users table. |
| `Products` | 36 | Raw products table. |
| `Purchases` | 2,208 | Raw purchases table, including `pending`. |
| `Item Purchases` | 3,237 | Raw purchase line items, including pending purchase items. |
| `Reviews` | 259 | Product reviews. |
| `Coupons` | 3 | Seeded coupons. |
| `Carts` | 55 | Active/abandoned carts. |
| `Cart Items` | 112 | Cart line items. |

### Important Grain Rules

- `Fato Vendas` grain is one row per item in a completed purchase.
- `ID Venda`, `Total do Pedido (R$)`, `Frete (R$)`, and `Desconto Cupom (R$)` repeat across multiple item rows for multi-item orders.
- Never sum `Total do Pedido (R$)` directly over `Fato Vendas` rows unless first deduplicating by `ID Venda`.
- For product and category charts, prefer `Subtotal Item (R$)`, `Quantidade Item`, and `Lucro Bruto Item (R$)`.
- For customer, payment, state, and monthly order revenue, deduplicate by `ID Venda` before summing order-level fields.

## Data Dictionary

### Fato Vendas

Completed sales fact table. Source scope is `Purchase.completed`, where completed means `paid` or `shipped`.

| Field | Type | Meaning |
| --- | --- | --- |
| `ID Venda` | integer | Purchase ID. Repeats once per item. |
| `Data Compra` | timestamp ISO8601 | Purchase datetime. |
| `Ano` | integer | Purchase year. |
| `Mes` | integer | Purchase month number. |
| `Dia` | integer | Purchase day. |
| `Hora` | integer | Purchase hour, generated from 8 to 21. |
| `ID Cliente` | integer | Customer/user ID. |
| `Estado Cliente` | string | Customer state code. |
| `Metodo Pagamento` | enum | `pix`, `credit_card`, `debit_card`. |
| `Status Venda` | enum | `paid` or `shipped` in this sheet. |
| `Cupom Utilizado` | string | Always `NENHUM` in current export. |
| `Desconto Cupom (R$)` | decimal | Order-level discount amount, repeated per item row. |
| `Frete (R$)` | decimal | Order-level shipping cost, repeated per item row. |
| `Total do Pedido (R$)` | decimal | Order-level total, repeated per item row. |
| `Produto` | string | Product name. |
| `Categoria` | string | Product category. |
| `Departamento` | string | Same value as category in current export. |
| `Preco Unitario Venda (R$)` | decimal | Unit sale price on the line item. |
| `Preco Unitario Custo (R$)` | decimal | Product cost price. |
| `Quantidade Item` | integer | Quantity sold on the line item. |
| `Subtotal Item (R$)` | decimal | `Preco Unitario Venda * Quantidade Item`. |
| `Lucro Bruto Item (R$)` | decimal | `(Preco Unitario Venda - Preco Unitario Custo) * Quantidade Item`. |

Current fact snapshot:

- Completed orders: 2,127
- Fact rows: 3,113
- Item units sold: 3,279
- Completed order revenue: R$ 160,692.02
- Item revenue: R$ 151,081.10
- Shipping charged: R$ 12,090.00
- Discounts granted: R$ 2,479.08
- Gross profit: R$ 73,807.63
- Average ticket: R$ 75.55
- Gross margin on item revenue: 48.85%

### Dimensão Produtos / Products

Product catalog. There are 36 products, six per category. All products are active in the seed snapshot.

| Field | Meaning |
| --- | --- |
| `ID Produto` / `ID` | Product ID. |
| `Produto` / `Nome` | Product name. |
| `Categoria` | Product category. |
| `Departamento` | Same as category in analytical sheet. |
| `Preco Venda (R$)` | Current sale price. |
| `Preco Custo (R$)` | Current unit cost. |
| `Margem Bruta Unit (R$)` | `Preco Venda - Preco Custo`. |
| `Estoque` | Current stock, non-negative integer. |
| `Ativo` | `Sim` or `Nao`; current seed uses `Sim`. |

Categories:

- `vestuario`: Camiseta Essencial, Regata Leve, Moletom Basico, Calca Jogger, Meia Algodao, Bone Urban.
- `casa`: Caneca Ceramica, Garrafa Termica, Organizador Mesa, Luminaria Led, Kit Toalhas, Almofada Decor.
- `papelaria`: Caderno Pontilhado, Planner Mensal, Caneta Gel Kit, Marcador Texto, Estojo Slim, Bloco Adesivo.
- `eletronicos`: Fone Bluetooth, Cabo Usb C, Carregador Turbo, Mouse Sem Fio, Suporte Notebook, Power Bank.
- `beleza`: Sabonete Artesanal, Hidratante Corporal, Necessaire, Escova Facial, Oleo Capilar, Kit Skincare.
- `alimentos`: Cafe Especial, Granola Premium, Mel Silvestre, Chocolate 70, Castanhas Mix, Cha Sortido.

### Dimensão Clientes / Users

Customer table. There are 180 customers distributed evenly across 12 Brazilian states, 15 per state.

| Field | Meaning |
| --- | --- |
| `ID Cliente` / `ID` | User/customer ID. |
| `Nome Cliente` / `Nome` | Customer name. |
| `Email` | Unique email. |
| `Estado` | State code. |
| `Cidade` | City. |
| `Data Nascimento` | Birth date. |
| `Idade` | Age as of export date. |
| `Total Pedidos` | Count of completed purchases for that customer. |
| `Receita Total (R$)` | Sum of completed `Purchase.total_amount` for that customer. |

States present: `SP`, `RJ`, `MG`, `PR`, `SC`, `RS`, `BA`, `PE`, `CE`, `GO`, `DF`, `ES`.

### Purchases

Raw orders table. Includes completed and pending purchases.

| Field | Meaning |
| --- | --- |
| `ID` | Purchase ID. |
| `ID Cliente` | User/customer ID. |
| `Status` | `pending`, `paid`, `shipped`, or `canceled`. Current snapshot has `paid`, `shipped`, `pending`. |
| `Metodo Pagamento` | `pix`, `credit_card`, or `debit_card`. |
| `Data Compra` | Purchase datetime. |
| `Subtotal (R$)` | Order subtotal before shipping and discount. |
| `Frete (R$)` | Shipping cost. |
| `Desconto (R$)` | Discount amount. |
| `Total (R$)` | `Subtotal + Frete - Desconto`. |
| `Criado Em`, `Atualizado Em` | Record timestamps. |

Current status counts:

- `paid`: 1,570
- `shipped`: 557
- `pending`: 81

Completed payment counts:

- `credit_card`: 903
- `pix`: 901
- `debit_card`: 323

### Item Purchases

Raw line items for all purchases, including pending.

| Field | Meaning |
| --- | --- |
| `ID` | Item purchase ID. |
| `ID Compra` | Purchase ID. |
| `ID Produto` | Product ID. |
| `Quantidade` | Positive integer quantity. |
| `Preco Unitario (R$)` | Unit price used for the item. |
| `Subtotal (R$)` | `Quantidade * Preco Unitario`. |
| `Criado Em`, `Atualizado Em` | Record timestamps. |

### Reviews

Product ratings and optional comments.

| Field | Meaning |
| --- | --- |
| `ID` | Review ID. |
| `ID Cliente` | User/customer ID. |
| `ID Produto` | Product ID. |
| `Nota` | Integer rating from 1 to 5. |
| `Comentario` | Optional review text. |
| `Criado Em`, `Atualizado Em` | Record timestamps. |

Current review snapshot:

- Reviews: 259
- Average rating: 4.29
- Rating counts: 5 stars = 130, 4 stars = 87, 3 stars = 33, 2 stars = 6, 1 star = 3

### Coupons

Seeded coupons:

| Code | Type | Value | Expiration | Meaning |
| --- | --- | ---: | --- | --- |
| `BEMVINDO10` | `fixed_amount` | 10.00 | One year after seed run | R$ 10 discount. |
| `MEI5OFF` | `percentage` | 5.00 | Six months after seed run | 5% discount. |
| `FRETEGRATIS` | `fixed_amount` | 8.90 | None | Free-shipping-like fixed discount. |

Current export does not associate coupon codes to purchases. `Fato Vendas.Cupom Utilizado` is always `NENHUM`; discount amounts are still present on purchases.

### Carts And Cart Items

Current carts:

- Carts: 55
- `open`: 41
- `abandoned`: 14
- Cart items: 112
- Cart item subtotal value: R$ 8,015.80

Cart status enum supports `open`, `checked_out`, and `abandoned`; the seed snapshot uses `open` and `abandoned`.

## Entity Relationships

- User has many purchases.
- User has many reviews.
- User has one cart.
- Product has many item purchases.
- Product has many reviews.
- Product has many cart items.
- Purchase belongs to user.
- Purchase has many item purchases and destroys them when destroyed.
- Item purchase belongs to purchase and product.
- Cart belongs to user.
- Cart has many cart items and destroys them when destroyed.
- Cart item belongs to cart and product.
- Review belongs to user and product.
- Review uniqueness is scoped to one review per user-product pair.

Deletion behavior:

- Destroying a purchase destroys its item purchases.
- Destroying a cart destroys its cart items.
- Destroying a user destroys purchases, reviews, and cart.
- Products are restricted from deletion if referenced by item purchases or cart items, and destroy related reviews.

## Business Rules And Validations

### Users

- `name`, `email`, `birth_date`, and `state` are required.
- `city` is stored but not required by validation.
- Email must be unique case-insensitively and must match email format.
- Customers must be at least 18 years old. A user is invalid if their 18th birthday is after `Date.current`.

### Products

- `name`, `category`, `price`, and `cost_price` are required.
- `stock` must be an integer greater than or equal to 0.
- `price` and `cost_price` must be greater than or equal to 0.
- `price` must be greater than `cost_price`.
- Unit gross margin is `price - cost_price`.

### Purchases

- Status enum: `pending`, `paid`, `shipped`, `canceled`; default is `pending`.
- Payment method enum: `pix`, `credit_card`, `debit_card`.
- `status`, `payment_method`, and `purchase_date` are required.
- `subtotal`, `shipping_cost`, `discount_amount`, and `total_amount` must be greater than or equal to 0.
- `total_amount` must equal `subtotal + shipping_cost - discount_amount`, with tolerance of R$ 0.01.
- Completed purchases are exactly `paid` and `shipped`. Analytics queries must exclude `pending` and `canceled`.

### Item Purchases

- `quantity` must be a positive integer.
- `unit_price` and `subtotal` must be greater than or equal to 0.
- `subtotal` must equal `quantity * unit_price`, with tolerance of R$ 0.01.

### Carts And Cart Items

- Cart status enum: `open`, `checked_out`, `abandoned`; default is `open`.
- Cart status is required.
- Cart item `quantity` must be a positive integer.
- Cart item `unit_price` and `subtotal` must be greater than or equal to 0.
- Cart item `subtotal` must equal `quantity * unit_price`, with tolerance of R$ 0.01.

### Coupons

- Discount type enum: `percentage`, `fixed_amount`.
- `code`, `discount_type`, and `discount_value` are required.
- `code` must be unique case-insensitively.
- `discount_value` must be greater than 0.
- A coupon is usable only when active and either has no expiration or `expires_at >= Time.current`.

### Reviews

- Rating must be an integer in `1..5`.
- Only one review is allowed per user-product pair.
- Comment is optional.

## Metrics And KPI Definitions

Use completed purchases unless the question explicitly asks about pending, carts, or raw operational records.

| Metric | Formula | Preferred Source |
| --- | --- | --- |
| Completed orders | Count purchases where status in `paid`, `shipped` | `Purchases` or distinct `Fato Vendas.ID Venda` |
| Revenue | Sum completed `Purchase.total_amount` | Deduplicated `Fato Vendas` or `Purchases` |
| Item revenue | Sum item subtotals | `Fato Vendas.Subtotal Item (R$)` |
| Gross profit | Sum item gross profit | `Fato Vendas.Lucro Bruto Item (R$)` |
| Gross margin % | `gross_profit / item_revenue * 100` | `Fato Vendas` |
| Average ticket | `revenue / completed_orders` | Deduplicated order data |
| Units sold | Sum `Quantidade Item` | `Fato Vendas` |
| Discount total | Sum completed order discounts | Deduplicated order data |
| Shipping total | Sum completed order shipping | Deduplicated order data |
| Product ranking revenue | Sum item subtotal by product | `Fato Vendas` or query |
| Category margin | Item revenue, item cost, gross margin by category | `Fato Vendas` or query |
| Top customers | Sum completed order totals by customer | `Purchases` joined to users |
| Review average | Average `Nota` | `Reviews` |
| Cart value | Sum cart item subtotal | `Cart Items` |
| Abandoned cart count | Count carts where status `abandoned` | `Carts` |

### Tested Query Formulas

- AverageTicketQuery groups completed purchases by `strftime('%Y-%m', purchase_date)` and returns month, purchase count, sum total amount, and rounded average ticket.
- ProductRankingQuery groups completed item purchases by product and orders by revenue descending, quantity sold descending, product name ascending.
- CategoryMarginQuery groups completed item purchases by product category and returns revenue, cost, gross margin, and margin percent. Cost is `products.cost_price * item_purchases.quantity`. Sort by gross margin descending, then category ascending.
- MonthlyProfitQuery groups completed item purchases by month and returns distinct purchase count, item revenue, item cost, and gross profit.
- TopCustomersQuery groups completed purchases by customer and orders by revenue descending, purchase count descending, customer name ascending.

## Current Analytical Highlights

Category item revenue and gross profit:

| Category | Item Revenue | Gross Profit | Units |
| --- | ---: | ---: | ---: |
| `eletronicos` | 37,409.10 | 18,146.97 | 559 |
| `casa` | 29,660.70 | 14,781.35 | 543 |
| `vestuario` | 26,195.70 | 13,027.15 | 543 |
| `beleza` | 23,947.20 | 11,207.57 | 518 |
| `alimentos` | 16,966.90 | 8,463.53 | 531 |
| `papelaria` | 16,901.50 | 8,181.06 | 585 |

Top products by item revenue:

| Product | Category | Units | Item Revenue | Gross Profit |
| --- | --- | ---: | ---: | ---: |
| Fone Bluetooth | `eletronicos` | 98 | 9,790.20 | 4,405.10 |
| Calca Jogger | `vestuario` | 104 | 8,309.60 | 3,738.80 |
| Kit Skincare | `beleza` | 85 | 8,066.50 | 3,307.35 |
| Kit Toalhas | `casa` | 88 | 7,471.20 | 4,258.32 |
| Suporte Notebook | `eletronicos` | 93 | 6,965.70 | 3,413.10 |

Revenue by customer state uses deduplicated order totals. Current leading states are `SP` (R$ 15,234.73), `PR` (R$ 14,522.51), `GO` (R$ 13,549.25), and `MG` (R$ 13,524.29).

## Reporting Rules

- Default reporting period: use the latest 12 months only if matching application query defaults; otherwise use all workbook data when users ask about the dataset.
- Time grouping: monthly keys should use `YYYY-MM`.
- Use `Data Compra` for sales time-series, not `Criado Em`.
- `Criado Em` / `Atualizado Em` describe record generation/persistence, not business sale timing.
- Use `Status Venda` or `Purchases.Status` to filter completed orders.
- For product/category performance, use item-level fields.
- For order totals, deduplicate by `ID Venda` before summing.
- Explain whether revenue includes shipping and discounts. `Purchase.total_amount` includes shipping and subtracts discounts; `Subtotal Item` excludes shipping and discounts.
- Coupon code attribution is not available in the current export; only discount amount is reliable.
- `Departamento` currently duplicates `Categoria`; do not infer a separate hierarchy.

## Chart Specification

### KPI Cards

| Chart | Purpose | Source | Fields | Aggregation |
| --- | --- | --- | --- | --- |
| Completed Orders | Show sales volume. | `Fato Vendas` | `ID Venda` | Count distinct IDs. |
| Revenue | Show completed order revenue. | `Fato Vendas` | `ID Venda`, `Total do Pedido (R$)` | Deduplicate by `ID Venda`, sum total. |
| Average Ticket | Show average completed order value. | `Fato Vendas` | `ID Venda`, `Total do Pedido (R$)` | Revenue / distinct orders. |
| Gross Profit | Show product-level gross profit. | `Fato Vendas` | `Lucro Bruto Item (R$)` | Sum. |
| Gross Margin % | Show profitability. | `Fato Vendas` | `Lucro Bruto Item (R$)`, `Subtotal Item (R$)` | Profit / item revenue * 100. |
| Units Sold | Show item demand. | `Fato Vendas` | `Quantidade Item` | Sum. |
| Active Products | Show catalog breadth. | `Products` | `Ativo` | Count where `Sim`. |
| Average Rating | Show satisfaction. | `Reviews` | `Nota` | Average. |
| Open Carts | Show current cart pipeline. | `Carts` | `Status` | Count where `open`. |
| Abandoned Carts | Show recovery opportunity. | `Carts` | `Status` | Count where `abandoned`. |

### Line Charts

| Chart | Purpose | Source | X-axis | Y-axis | Grouping | Filters | Interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Monthly Revenue | Track sales trend. | Deduplicated `Fato Vendas` | `YYYY-MM` from `Data Compra` | Sum `Total do Pedido (R$)` | Optional status/payment/state | Date range, payment, state | Rising line means higher completed order revenue. |
| Monthly Average Ticket | Track order value. | Deduplicated `Fato Vendas` | `YYYY-MM` | Revenue / orders | Optional state/payment | Date range | Separates basket value from order count. |
| Monthly Gross Profit | Track profitability. | `Fato Vendas` | `YYYY-MM` | Sum `Lucro Bruto Item (R$)` | Optional category | Date range, category | Shows product margin contribution over time. |
| Monthly Units Sold | Track volume. | `Fato Vendas` | `YYYY-MM` | Sum `Quantidade Item` | Optional category/product | Date range | Demand trend independent of price. |
| Monthly Orders By Status | Monitor operations. | `Purchases` | `YYYY-MM` from `Data Compra` | Count orders | `Status` | Date range | Shows pending versus completed pipeline. |

### Bar Charts

| Chart | Purpose | Source | X-axis | Y-axis | Sorting | Filters | Interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Revenue By Category | Compare category sales. | `Fato Vendas` | `Categoria` | Sum `Subtotal Item (R$)` | Desc revenue | Date, state, payment | Best categories by item sales. |
| Gross Profit By Category | Compare category contribution. | `Fato Vendas` | `Categoria` | Sum `Lucro Bruto Item (R$)` | Desc profit | Date | Best categories by profit. |
| Margin % By Category | Compare profitability. | `Fato Vendas` | `Categoria` | Profit / item revenue * 100 | Desc margin % | Date | Highest-margin categories, not necessarily highest revenue. |
| Top Products By Revenue | Rank products. | `Fato Vendas` | `Produto` | Sum `Subtotal Item (R$)` | Desc revenue, then units | Date, category | Product sales leaderboard. |
| Top Products By Units | Rank demand volume. | `Fato Vendas` | `Produto` | Sum `Quantidade Item` | Desc units | Date, category | Most frequently sold products. |
| Revenue By State | Geographic comparison. | Deduplicated `Fato Vendas` | `Estado Cliente` | Sum `Total do Pedido (R$)` | Desc revenue | Date | Revenue concentration by customer state. |
| Orders By Payment Method | Payment mix volume. | Deduplicated `Fato Vendas` | `Metodo Pagamento` | Count orders | Desc count | Date | Preferred payment methods. |
| Revenue By Payment Method | Payment mix value. | Deduplicated `Fato Vendas` | `Metodo Pagamento` | Sum order total | Desc revenue | Date | Monetary value by payment method. |
| Reviews By Rating | Satisfaction distribution. | `Reviews` | `Nota` | Count reviews | Rating asc | Product/category | Rating distribution. |
| Cart Count By Status | Cart health. | `Carts` | `Status` | Count carts | Status | None | Open and abandoned cart volume. |

### Pie / Donut Charts

Use pie/donut charts only for a small number of categories and share-of-total questions.

| Chart | Purpose | Source | Slice | Value | Notes |
| --- | --- | --- | --- | --- | --- |
| Revenue Share By Category | Show sales mix. | `Fato Vendas` | `Categoria` | Sum item subtotal | Six categories, suitable for donut. |
| Payment Method Share | Show payment preference. | Deduplicated `Fato Vendas` | `Metodo Pagamento` | Count orders or sum revenue | State whether count or revenue share. |
| Status Share | Show operational order mix. | `Purchases` | `Status` | Count purchases | Include pending if using raw purchases. |
| Rating Share | Show review sentiment. | `Reviews` | `Nota` | Count reviews | Five slices max. |
| Cart Status Share | Show cart composition. | `Carts` | `Status` | Count carts | Current snapshot has open/abandoned. |

### Tables And Rankings

| Table | Purpose | Source | Required Fields | Sorting |
| --- | --- | --- | --- | --- |
| Top Customers | Identify highest-value customers. | `Dimensão Clientes` or `Purchases` + `Users` | Customer, email, state, order count, revenue | Revenue desc, order count desc, name asc. |
| Product Ranking | Product leaderboard. | `Fato Vendas` | Product, category, units, item revenue, gross profit, margin % | Revenue desc, units desc, product asc. |
| Category Margin Table | Profitability by category. | `Fato Vendas` | Category, item revenue, cost, gross profit, margin % | Gross profit desc. |
| Monthly Profit Table | Month-level P&L. | `Fato Vendas` | Month, orders, item revenue, item cost, gross profit | Month asc. |
| Customer Geography Table | State/city sales. | `Fato Vendas` + customers | State, city, orders, revenue | Revenue desc. |
| Product Review Table | Quality signal. | `Reviews` + products | Product, review count, average rating | Average rating desc, review count desc. |
| Cart Recovery Table | Recovery opportunity. | `Carts`, `Cart Items`, `Users` | Cart, customer, status, item count, subtotal | Subtotal desc. |

### Comparisons And Time-Series Analyses

- Period-over-period revenue: compare completed order revenue between two date ranges using deduplicated order totals.
- Month-over-month growth: `(current_month_revenue - previous_month_revenue) / previous_month_revenue * 100`.
- Category trend: monthly item revenue grouped by `Categoria`.
- Product trend: monthly item revenue or units grouped by `Produto`.
- Profit versus revenue: grouped bar or dual-axis line using item revenue and gross profit.
- Shipping and discount impact: monthly deduplicated sums of `Frete` and `Desconto`, compared to revenue.
- State ranking over time: monthly revenue by `Estado Cliente`, deduplicated by order.
- Payment method trend: monthly completed order count/revenue grouped by `Metodo Pagamento`.
- Cart abandonment: count carts by status and cart item value by status.

## Common Business Questions And Expected AI Reasoning

### "What was total revenue?"

Use completed purchases. In `Fato Vendas`, deduplicate by `ID Venda` and sum `Total do Pedido (R$)`. State that this includes shipping and subtracts discounts. Current workbook total: R$ 160,692.02.

### "What was product/category revenue?"

Use item-level revenue: sum `Subtotal Item (R$)` grouped by `Produto` or `Categoria`. Do not use `Total do Pedido (R$)` because it repeats per item.

### "What is gross profit or margin?"

Use `Lucro Bruto Item (R$)` or compute `(unit sale price - unit cost price) * quantity`. Margin percent is gross profit divided by item revenue, multiplied by 100.

### "Which customers are best?"

Use completed order totals grouped by customer. Prefer `Dimensão Clientes` if only snapshot-level totals are needed; otherwise use deduplicated `Fato Vendas` or raw `Purchases` joined to `Users` for filters and date ranges.

### "Are pending purchases included?"

No for default sales analytics. Pending purchases appear in raw `Purchases` and `Item Purchases`, but `Fato Vendas` and tested business queries use only `paid` and `shipped`.

### "What chart should I generate?"

Choose the grain based on the question:

- Order-level question: deduplicate by `ID Venda`.
- Item/product/category question: use item rows.
- Operational cart question: use `Carts` and `Cart Items`.
- Review/satisfaction question: use `Reviews`.
- Catalog question: use `Products` or `Dimensão Produtos`.

### "Why does item revenue differ from total revenue?"

Item revenue is merchandise subtotal only. Total order revenue includes shipping and subtracts discounts. Current workbook has item revenue R$ 151,081.10, shipping R$ 12,090.00, discounts R$ 2,479.08, resulting in completed total revenue R$ 160,692.02.

## Implemented Application Scope

The current Python app implements a dashboard and governed local QA flow over `data/dataset_analitico_mei.xlsx`.

Implemented files:

- `app/data_loader.py`: loads all required workbook sheets and validates required columns.
- `app/charts.py`: calculates KPIs, monthly revenue/profit, category/product performance, state/payment summaries, cart status, cart recovery, and review distribution.
- `app/business_qa.py`: answers common business questions locally from governed formulas before any external AI call.
- `app/gemini_client.py`: optionally calls Gemini when `GEMINI_API_KEY` and `google-generativeai` are available.
- `app/reporting.py`: exports a Markdown analytics report.
- `app/main.py`: Streamlit dashboard with sales, product, operation, and AI QA tabs.
- `scripts/run_checks.py`: standard local quality gate.
- `scripts/smoke_app.py`: end-to-end smoke validation for loader, KPIs, QA, filters, and report generation.
- `scripts/validate_workbook_contract.py`: workbook schema gate.
- `scripts/validate_kpis.py`: KPI regression gate.

Standard verification:

```bash
python scripts/run_checks.py
python scripts/export_report.py /tmp/mei_commerce_report.md
```

The shipped dashboard supports:

- KPI cards for completed orders, order revenue, item revenue, gross profit, gross margin, average ticket, units, and average rating.
- Sidebar filters for period, state, payment method, and category.
- Sales charts for monthly revenue, state revenue, payment method volume, and monthly gross profit table.
- Product/category charts and ranking tables using item-level fields.
- Operational cart/review views for cart value by status, cart recovery candidates, and review rating distribution.
- Local governed answers for revenue, profit/margin, category, product, state, payment, discount/coupon, and supported-question discovery.
- Markdown report download from the dashboard using the currently filtered fact rows.
- CLI entrypoints: `python app/main.py --cli` and `python app/main.py --export-report <path>`.
- Local `.env` loading for optional Gemini configuration. Existing exported environment variables take priority.
- Optional Gemini enhancement that must not override the workbook grain and formula rules.

When category filters are applied in the dashboard, order-level KPIs describe orders that contain the selected categories. Product/category charts still use item-level fields and remain the preferred view for category revenue.

## Known Assumptions And Limitations

- Data is synthetic and deterministic, generated by `db/seeds.rb`.
- The seed uses deterministic randomness (`Random.new(20260628)`) and creates 24 months with 92 purchases per month before filtering completion status.
- The workbook is a snapshot; IDs and timestamps reflect the database state at export time.
- Coupon usage is not modeled as a purchase association. Discount amounts exist, but coupon code attribution is unavailable.
- `Departamento` is not a true separate hierarchy; it duplicates `Categoria`.
- Shipping is stored at order level, not item level.
- Discounts are stored at order level, not item level.
- Cost uses current product `cost_price`, including in tested margin queries. Historical cost changes are not modeled.
- There is no tax, refund, return, or cancellation financial logic beyond the `canceled` status enum.
- There is no inventory decrement workflow in the tested purchase flow.
- There are no permission or role rules in the analyzed tests.

## AI Handoff

Future AI agents should answer business questions from the definitions in this document first. If a metric requires source data, use `data/dataset_analitico_mei.xlsx`; if behavior or formulas are disputed, treat `test/` as the authority.

Use completed purchases (`paid`, `shipped`) for sales, revenue, average ticket, product ranking, category margin, monthly profit, and top-customer analytics. Include `pending` only when the user explicitly asks about pipeline, raw purchases, or operational status.

Always identify the grain before calculating:

- Order-level: deduplicate `Fato Vendas` by `ID Venda`.
- Item-level: use every `Fato Vendas` row.
- Raw operational: use raw model sheets.

When explaining calculations, include the formula in business terms and mention inclusions/exclusions. For example, "average ticket is completed order revenue divided by completed order count; revenue includes shipping and subtracts discounts."

When generating charts, specify:

- Source sheet.
- Required fields.
- Filters.
- Grouping and time granularity.
- Whether the metric is order-level or item-level.
- Sorting rules.

Best practices:

- Use monthly `YYYY-MM` time buckets for sales trends.
- Prefer bar charts for rankings and category comparisons.
- Prefer line charts for time-series.
- Prefer KPI cards for single totals and averages.
- Avoid pie charts unless there are few slices and the question is share-of-total.
- Never sum repeated order totals from item-grain fact rows without deduplication.
- Be explicit when using item revenue versus order revenue.
- Do not infer coupon code usage from discount amount.
- Do not treat `Criado Em` as purchase timing.
