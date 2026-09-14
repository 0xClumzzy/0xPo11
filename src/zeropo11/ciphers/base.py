"""Base cipher interface and result types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CipherResult:
    """Result of a cipher operation."""

    output: str
    success: bool

    def __iter__(self):  # noqa: ANN204
        """Allow unpacking as [output, success] for backward compat."""
        yield self.output
        yield self.success

    def __getitem__(self, index: int) -> Any:  # noqa: ANN401
        """Allow indexing as result[0] / result[1]."""
        return (self.output, self.success)[index]


class BaseCipher:
    """Base class for all cipher modules.

    Subclasses must define:
        - name: Human-readable cipher name
        - command: CLI command name (e.g. "cc", "b64")
        - help_menu: Usage string shown with --help

    Subclasses should override at least one of encode/decode/brute.
    """

    name: str = "Unknown"
    command: str = ""
    help_menu: str = ""

    def encode(self, args: Any) -> CipherResult:
        """Encode plaintext. Override in subclass."""
        raise NotImplementedError(f"{self.name} does not support encoding")

    def decode(self, args: Any) -> CipherResult:
        """Decode ciphertext. Override in subclass."""
        raise NotImplementedError(f"{self.name} does not support decoding")

    def brute(self, args: Any) -> CipherResult:
        """Brute-force attack. Override in subclass."""
        raise NotImplementedError(f"{self.name} does not support brute-forcing")
