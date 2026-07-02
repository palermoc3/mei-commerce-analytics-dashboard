"""Validate the workbook sheets and required columns."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.data_loader import workbook_contract_report


def main() -> None:
    report = workbook_contract_report()
    print(f"workbook={report.path}")
    print(f"sheet_count={report.sheet_count}")
    for sheet, rows in report.row_counts.items():
        print(f"{sheet}: {rows}")


if __name__ == "__main__":
    main()
