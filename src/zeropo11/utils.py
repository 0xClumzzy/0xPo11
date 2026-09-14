"""Shared utilities for output and file handling."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from zeropo11.config import END, FAIL, SUCCESS


def handle_output(result: Any, output_path: str | None = None) -> None:
    """Print or write cipher operation result.

    Args:
        result: Tuple of (output_str, success_bool) or CipherResult.
        output_path: Optional file path to write output to.
    """
    data, success = result[0], result[1]

    if success:
        if output_path and ".png" not in output_path:
            Path(output_path).write_text(data)
            print(f"{SUCCESS}[✓] File Output Successful{END}")
        else:
            print(f"\n{SUCCESS}[✓] Output:{END}\n{data}\n")
    else:
        print(f"\n{FAIL}[✖] Failed:{END}\n{data}\n")


def read_input_file(path: str) -> str:
    """Read and return contents of an input file."""
    return Path(path).read_text()


def read_wordlist(path: str) -> list[str]:
    """Read a wordlist file, returning non-empty lines."""
    lines = Path(path).read_text().split("\n")
    return [line for line in lines if line]
