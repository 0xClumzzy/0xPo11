"""Cryptographic Payloads - copy pre-made payload files."""
from __future__ import annotations

import shutil
from pathlib import Path

from zeropo11.ciphers.base import BaseCipher, CipherResult

# Bundled default templates are shipped with the package and seeded into the
# user payload dir on first use. Users can drop their own payloads into
# PAYLOADS_DIR later — those take precedence over the bundled defaults.
TEMPLATES_DIR = Path(__file__).parent / "templates" / "payloads"
PAYLOADS_DIR = Path.home() / ".0xPo11" / "resources" / "payloads"

HELP = """USAGE:
  key cp [FLAGS] [OPTIONS]
FLAGS:
  -g, --generate <name>     Payload template name (alias for -p)
  -p, --payload <name>      Payload name to copy
OPTIONS:
  -o, --output <path>       Output directory (default: current)
PAYLOADS:
  duckyscript.txt  powershell.ps1  bash.sh  python.py
EXAMPLES:
  key cp -p duckyscript.txt -o ~/Desktop
"""


def seed_payloads() -> None:
    """Copy bundled payload templates into PAYLOADS_DIR on first use."""
    if not TEMPLATES_DIR.is_dir():
        return
    try:
        PAYLOADS_DIR.mkdir(parents=True, exist_ok=True)
        for src in TEMPLATES_DIR.iterdir():
            if src.is_file() and not (PAYLOADS_DIR / src.name).exists():
                shutil.copy2(src, PAYLOADS_DIR / src.name)
    except OSError:
        pass  # Non-fatal: PAYLOADS_DIR is only a convenience cache.


class Cipher(BaseCipher):
    """Cryptographic Payloads cipher."""

    name = "Cryptographic Payloads"
    command = "cp"
    help_menu = HELP

    def encode(self, args):
        return CipherResult("Payloads does not support encoding", False)

    def decode(self, args):
        return CipherResult("Payloads does not support decoding", False)

    def payload(self, args):
        seed_payloads()
        payload_name = getattr(args, "payload", None)
        output = getattr(args, "output", None) or "."
        if not payload_name:
            return CipherResult("Please provide -p <payload>", False)
        src = PAYLOADS_DIR / payload_name
        if not src.exists():
            return CipherResult(f"Payload '{payload_name}' not found", False)
        try:
            dest_dir = Path(output)
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / payload_name
            if src.is_dir():
                shutil.copytree(src, dest)
            else:
                shutil.copy2(src, dest)
            return CipherResult(f"Payload copied to {dest}", True)
        except Exception as e:
            return CipherResult(f"Copy failed: {e}", False)
