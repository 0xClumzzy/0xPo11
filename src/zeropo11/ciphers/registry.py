"""Cipher registry - discovers and dispatches cipher modules."""

from __future__ import annotations

import importlib
import pkgutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zeropo11.ciphers.base import BaseCipher

_registry: dict[str, type[BaseCipher]] = {}
_loaded = False


def _discover_ciphers() -> None:
    """Auto-discover all cipher modules in the ciphers package."""
    global _loaded  # noqa: PLW0603
    if _loaded:
        return

    import zeropo11.ciphers as ciphers_pkg

    for _importer, modname, _ispkg in pkgutil.iter_modules(ciphers_pkg.__path__):
        if modname.startswith("_") or modname in ("base",):
            continue
        try:
            module = importlib.import_module(f"zeropo11.ciphers.{modname}")
        except ImportError:
            continue

        # Find the cipher class in the module (anything that subclasses BaseCipher)
        from zeropo11.ciphers.base import BaseCipher

        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, BaseCipher)
                and attr is not BaseCipher
            ):
                cipher = attr()
                if cipher.command:
                    _registry[cipher.command] = attr

    _loaded = True


def get_cipher(command: str) -> BaseCipher:
    """Get a cipher instance by its command name."""
    _discover_ciphers()
    if command not in _registry:
        available = ", ".join(sorted(_registry.keys()))
        raise KeyError(
            f"Cipher '{command}' not found. Available: {available}"
        )
    return _registry[command]()


def list_ciphers() -> list[str]:
    """Return sorted list of available cipher commands."""
    _discover_ciphers()
    return sorted(_registry.keys())


def get_cipher_info() -> list[tuple[str, str]]:
    """Return list of (command, name) tuples."""
    _discover_ciphers()
    return sorted(
        [(cmd, cls().name) for cmd, cls in _registry.items()],
        key=lambda x: x[0],
    )
