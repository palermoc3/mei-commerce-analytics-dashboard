"""Export a Markdown analytics report."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.reporting import write_markdown_report


def main() -> None:
    output_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("reports/mei_commerce_report.md")
    path = write_markdown_report(output_path)
    print(f"report={path}")


if __name__ == "__main__":
    main()
