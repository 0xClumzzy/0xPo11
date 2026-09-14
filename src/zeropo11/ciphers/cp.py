"""Cryptographic Payloads - copy pre-made payload files."""
from __future__ import annotations

import shutil
from pathlib import Path

from zeropo11.ciphers.base import BaseCipher, CipherResult

PAYLOADS_DIR = Path.home() / ".0xPo11" / "resources" / "payloads"

HELP = """USAGE:
  key cp [FLAGS] [OPTIONS]
FLAGS:
  -g, --generate <method>   Payload generation method
  -p, --payload <name>      Payload name to copy
OPTIONS:
  -o, --output <path>       Output directory (default: current)
EXAMPLES:
  key cp -p duckyscript -o ~/Desktop
"""


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
        payload_name = getattr(args, "payload", None)
        output = getattr(args, "output", None) or "."
        if not payload_name:
            return CipherResult("Please provide -p <payload>", False)
        src = PAYLOADS_DIR / payload_name
        if not src.exists():
            return CipherResult(f"Payload '{payload_name}' not found", False)
        try:
            dest = Path(output) / payload_name
            if src.is_dir():
                shutil.copytree(src, dest)
            else:
                shutil.copy2(src, dest)
            return CipherResult(f"Payload copied to {dest}", True)
        except Exception as e:
            return CipherResult(f"Copy failed: {e}", False)
