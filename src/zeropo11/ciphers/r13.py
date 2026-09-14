"""ROT13 Encoding cipher (Caesar shift 13)."""
from __future__ import annotations

from zeropo11.ciphers.base import BaseCipher, CipherResult


class Cipher(BaseCipher):
    name = "ROT13 Encoding"
    command = "r13"
    help_menu = """USAGE:
  key r13 [FLAGS] [OPTIONS]
FLAGS:
  -e, --encode  ROT13 encode input text
  -d, --decode  ROT13 decode input text
OPTIONS:
  -t, --text <text>  Input text
EXAMPLES:
  key r13 -e -t "hello"
"""
    def encode(self, args):
        text = getattr(args, 'text', None)
        if not text:
            return CipherResult("Please provide -t <text>", False)
        result = []
        for c in text:
            if c.isalpha():
                base = ord('A') if c.isupper() else ord('a')
                result.append(chr((ord(c) - base + 13) % 26 + base))
            else:
                result.append(c)
        return CipherResult("".join(result), True)
    def decode(self, args):
        return self.encode(args)
