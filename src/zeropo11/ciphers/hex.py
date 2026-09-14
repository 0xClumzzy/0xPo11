"""Hex Encoding cipher."""
from __future__ import annotations

from zeropo11.ciphers.base import BaseCipher, CipherResult


class Cipher(BaseCipher):
    name = "Hex Encoding"
    command = "hex"
    help_menu = """USAGE:
  key hex [FLAGS] [OPTIONS]
FLAGS:
  -e, --encode  Encode input text
  -d, --decode  Decode input text
OPTIONS:
  -t, --text <text>  Input text
EXAMPLES:
  key hex -e -t "hello"
"""
    def encode(self, args):
        text = getattr(args, 'text', None)
        if not text:
            return CipherResult("Please provide -t <text>", False)
        return CipherResult(text.encode().hex(), True)
    def decode(self, args):
        text = getattr(args, 'text', None)
        if not text:
            return CipherResult("Please provide -t <text>", False)
        try:
            return CipherResult(bytes.fromhex(text).decode(), True)
        except Exception as e:
            return CipherResult(str(e), False)
