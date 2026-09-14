"""Multiplicative Cipher."""
from __future__ import annotations

from zeropo11.ciphers.base import BaseCipher, CipherResult

MOD_INVERSE: dict[int, int] = {}
for i in range(1, 26):
    for j in range(1, 26):
        if (i * j) % 26 == 1:
            MOD_INVERSE[i] = j


class Cipher(BaseCipher):
    name = "Multiplicative Cipher"
    command = "mc"
    help_menu = """USAGE:
  key mc [FLAGS] [OPTIONS]
FLAGS:
  -e, --encode  Encode input text
  -d, --decode  Decode input text
OPTIONS:
  -t, --text <text>  Input text
  -k, --key <key>    Encryption key (integer)
EXAMPLES:
  key mc -e -t "hello" -k 3
"""

    def encode(self, args: object) -> CipherResult:
        text = getattr(args, "text", None)
        key = getattr(args, "key", None)
        if not text or not key:
            return CipherResult("Please provide -t <text> and -k <key>", False)
        key = int(key)
        result = []
        for c in text:
            if c.isalpha():
                base = ord("A") if c.isupper() else ord("a")
                result.append(chr((ord(c) - base) * key % 26 + base))
            else:
                result.append(c)
        return CipherResult("".join(result), True)

    def decode(self, args: object) -> CipherResult:
        text = getattr(args, "text", None)
        key = getattr(args, "key", None)
        if not text or not key:
            return CipherResult("Please provide -t <text> and -k <key>", False)
        key = int(key)
        if key not in MOD_INVERSE:
            return CipherResult(f"Key {key} has no multiplicative inverse mod 26", False)
        inv = MOD_INVERSE[key]
        result = []
        for c in text:
            if c.isalpha():
                base = ord("A") if c.isupper() else ord("a")
                result.append(chr((ord(c) - base) * inv % 26 + base))
            else:
                result.append(c)
        return CipherResult("".join(result), True)
