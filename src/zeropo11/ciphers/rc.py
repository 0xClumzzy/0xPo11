"""Reverse Cipher."""
from __future__ import annotations

from zeropo11.ciphers.base import BaseCipher, CipherResult


class Cipher(BaseCipher):
    name = "Reverse Cipher"
    command = "rc"
    help_menu = """USAGE:
  key rc [FLAGS] [OPTIONS]
FLAGS:
  -e, --encode  Reverse input text
  -d, --decode  Reverse input text
OPTIONS:
  -t, --text <text>  Input text
EXAMPLES:
  key rc -e -t "hello"
"""
    def encode(self, args):
        text = getattr(args, 'text', None)
        if not text:
            return CipherResult("Please provide -t <text>", False)
        return CipherResult(text[::-1], True)
    def decode(self, args):
        return self.encode(args)
