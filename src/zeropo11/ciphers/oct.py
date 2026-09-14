"""Octal Encoding cipher."""
from __future__ import annotations

from zeropo11.ciphers.base import BaseCipher, CipherResult


class Cipher(BaseCipher):
    name = "Octal Encoding"
    command = "oct"
    help_menu = """USAGE:
  key oct [FLAGS] [OPTIONS]
FLAGS:
  -e, --encode  Encode input text
  -d, --decode  Decode input text
OPTIONS:
  -t, --text <text>  Input text
EXAMPLES:
  key oct -e -t "hello"
"""
    def encode(self, args):
        text = getattr(args, 'text', None)
        if not text:
            return CipherResult("Please provide -t <text>", False)
        return CipherResult(" ".join(format(ord(c), "03o") for c in text), True)
    def decode(self, args):
        text = getattr(args, 'text', None)
        if not text:
            return CipherResult("Please provide -t <text>", False)
        try:
            return CipherResult(" ".join(chr(int(o, 8)) for o in text.split()), True)
        except Exception as e:
            return CipherResult(str(e), False)
