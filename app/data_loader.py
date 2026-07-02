"""Workbook loading and contract validation for MEI commerce analytics."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


DEFAULT_WORKBOOK_PATH = Path("data/dataset_analitico_mei.xlsx")

REQUIRED_COLUMNS: dict[str, tuple[str, ...]] = {
    "Fato Vendas": (
        "ID Venda",
        "Data Compra",
        "Ano",
        "Mes",
        "Dia",
        "Hora",
        "ID Cliente",
        "Estado Cliente",
        "Metodo Pagamento",
        "Status Venda",
        "Cupom Utilizado",
        "Desconto Cupom (R$)",
        "Frete (R$)",
        "Total do Pedido (R$)",
        "Produto",
        "Categoria",
        "Departamento",
        "Preco Unitario Venda (R$)",
        "Preco Unitario Custo (R$)",
        "Quantidade Item",
        "Subtotal Item (R$)",
        "Lucro Bruto Item (R$)",
    ),
    "Dimensão Produtos": (
        "ID Produto",
        "Produto",
        "Categoria",
        "Departamento",
        "Preco Venda (R$)",
        "Preco Custo (R$)",
        "Margem Bruta Unit (R$)",
        "Estoque",
        "Ativo",
    ),
    "Dimensão Clientes": (
        "ID Cliente",
        "Nome Cliente",
        "Email",
        "Estado",
        "Cidade",
        "Data Nascimento",
        "Idade",
        "Total Pedidos",
        "Receita Total (R$)",
    ),
    "Users": (
        "ID",
        "Nome",
        "Email",
        "Data Nascimento",
        "Estado",
        "Cidade",
        "Criado Em",
        "Atualizado Em",
    ),
    "Products": (
        "ID",
        "Nome",
        "Categoria",
        "Preco Venda (R$)",
        "Preco Custo (R$)",
        "Estoque",
        "Ativo",
        "Criado Em",
        "Atualizado Em",
    ),
    "Purchases": (
        "ID",
        "ID Cliente",
        "Status",
        "Metodo Pagamento",
        "Data Compra",
        "Subtotal (R$)",
        "Frete (R$)",
        "Desconto (R$)",
        "Total (R$)",
        "Criado Em",
        "Atualizado Em",
    ),
    "Item Purchases": (
        "ID",
        "ID Compra",
        "ID Produto",
        "Quantidade",
        "Preco Unitario (R$)",
        "Subtotal (R$)",
        "Criado Em",
        "Atualizado Em",
    ),
    "Reviews": (
        "ID",
        "ID Cliente",
        "ID Produto",
        "Nota",
        "Comentario",
        "Criado Em",
        "Atualizado Em",
    ),
    "Coupons": (
        "ID",
        "Codigo",
        "Tipo Desconto",
        "Valor Desconto",
        "Ativo",
        "Expira Em",
        "Criado Em",
        "Atualizado Em",
    ),
    "Carts": ("ID", "ID Cliente", "Status", "Criado Em", "Atualizado Em"),
    "Cart Items": (
        "ID",
        "ID Carrinho",
        "ID Produto",
        "Quantidade",
        "Preco Unitario (R$)",
        "Subtotal (R$)",
        "Criado Em",
        "Atualizado Em",
    ),
}

REQUIRED_SHEETS: tuple[str, ...] = tuple(REQUIRED_COLUMNS)


class WorkbookContractError(ValueError):
    """Raised when the workbook does not match the documented contract."""


@dataclass(frozen=True)
class WorkbookContractReport:
    """Small immutable summary used by validation scripts and app status."""

    path: Path
    sheet_count: int
    row_counts: dict[str, int]


def load_workbook(path: str | Path = DEFAULT_WORKBOOK_PATH) -> dict[str, pd.DataFrame]:
    """Load and validate all required workbook sheets.

    Column names are preserved exactly because the knowledge base uses the
    workbook as a business-facing contract.
    """

    workbook_path = Path(path)
    if not workbook_path.exists():
        raise FileNotFoundError(f"Workbook not found: {workbook_path}")

    try:
        with pd.ExcelFile(workbook_path) as excel:
            missing_sheets = sorted(set(REQUIRED_SHEETS) - set(excel.sheet_names))
            if missing_sheets:
                raise WorkbookContractError(
                    "Workbook is missing required sheets: " + ", ".join(missing_sheets)
                )

            sheets = {sheet: excel.parse(sheet) for sheet in REQUIRED_SHEETS}
    except WorkbookContractError:
        raise
    except Exception as exc:
        raise WorkbookContractError(
            f"Unable to read workbook {workbook_path}: {exc}"
        ) from exc
    validate_workbook_contract(sheets)
    return sheets


def validate_workbook_contract(
    sheets: dict[str, pd.DataFrame],
    required_columns: dict[str, tuple[str, ...]] = REQUIRED_COLUMNS,
) -> None:
    """Validate required sheets and columns.

    The function intentionally validates only the public contract, not every
    business formula. Formula regression belongs in analytics validation.
    """

    missing_sheets = sorted(set(required_columns) - set(sheets))
    if missing_sheets:
        raise WorkbookContractError(
            "Missing loaded sheets: " + ", ".join(missing_sheets)
        )

    errors: list[str] = []
    for sheet_name, columns in required_columns.items():
        df = sheets[sheet_name]
        missing_columns = [column for column in columns if column not in df.columns]
        if missing_columns:
            errors.append(
                f"{sheet_name}: missing columns {', '.join(missing_columns)}"
            )

    if errors:
        raise WorkbookContractError("; ".join(errors))


def workbook_contract_report(
    path: str | Path = DEFAULT_WORKBOOK_PATH,
) -> WorkbookContractReport:
    """Load the workbook and return row counts for each required sheet."""

    workbook_path = Path(path)
    sheets = load_workbook(workbook_path)
    row_counts = {sheet: len(df) for sheet, df in sheets.items()}
    return WorkbookContractReport(
        path=workbook_path, sheet_count=len(sheets), row_counts=row_counts
    )
