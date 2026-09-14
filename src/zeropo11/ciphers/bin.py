"""Binary Encoding cipher."""
from __future__ import annotations

from zeropo11.ciphers.base import BaseCipher, CipherResult


class Cipher(BaseCipher):
    name = "Binary Encoding"
    command = "bin"
    help_menu = """USAGE:
  key bin [FLAGS] [OPTIONS]
FLAGS:
  -e, --encode  Encode input text
  -d, --decode  Decode input text
OPTIONS:
  -t, --text <text>  Input text
EXAMPLES:
  key bin -e -t "hello"
"""
    def encode(self, args):
        text = getattr(args, 'text', None)
        if not text:
            return CipherResult("Please provide -t <text>", False)
        return CipherResult(" ".join(format(ord(c), "08b") for c in text), True)
    def decode(self, args):
        text = getattr(args, 'text', None)
        if not text:
            return CipherResult("Please provide -t <text>", False)
        try:
            binary_values = text.split()
            decoded = "".join(chr(int(b, 2)) for b in binary_values)
            return CipherResult(decoded, True)
        except Exception as e:
            return CipherResult(str(e), False)
