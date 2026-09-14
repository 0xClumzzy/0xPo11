"""Monoalphabetic substitution cipher."""
from __future__ import annotations

from zeropo11.ciphers.base import BaseCipher, CipherResult

PLAIN = "abcdefghijklmnopqrstuvwxyz"
CIPHER = "cdefghijklmnopqrstuvwxyzab"

class Cipher(BaseCipher):
    name = "Monoalphabetic Cipher"
    command = "mo"
    help_menu = """USAGE:
  key mo [FLAGS] [OPTIONS]
FLAGS:
  -e, --encode  Encode input text
  -d, --decode  Decode input text
OPTIONS:
  -t, --text <text>  Input text
EXAMPLES:
  key mo -e -t "hello"
"""
    def encode(self, args):
        text = getattr(args, 'text', None)
        if not text:
            return CipherResult("Please provide -t <text>", False)
        table = str.maketrans(PLAIN, CIPHER)
        return CipherResult(text.translate(table), True)
    def decode(self, args):
        text = getattr(args, 'text', None)
        if not text:
            return CipherResult("Please provide -t <text>", False)
        table = str.maketrans(CIPHER, PLAIN)
        return CipherResult(text.translate(table), True)
