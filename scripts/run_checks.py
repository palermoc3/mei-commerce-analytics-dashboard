"""Run the standard local quality gates."""

from __future__ import annotations

import subprocess
import sys


COMMANDS = [
    [sys.executable, "-m", "compileall", "app", "scripts", "tests"],
    [sys.executable, "scripts/validate_workbook_contract.py"],
    [sys.executable, "scripts/validate_kpis.py"],
    [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
]


def main() -> None:
    for command in COMMANDS:
        print("+ " + " ".join(command), flush=True)
        subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
