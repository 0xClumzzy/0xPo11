"""XOR Cipher."""
from __future__ import annotations

from zeropo11.ciphers.base import BaseCipher, CipherResult


class Cipher(BaseCipher):
    name = "XOR Cipher"
    command = "xor"
    help_menu = """USAGE:
  key xor [FLAGS] [OPTIONS]
FLAGS:
  -e, --encode  Encode input text
  -d, --decode  Decode input text
OPTIONS:
  -t, --text <text>  Input text
  -k, --key <key>    Encryption key
EXAMPLES:
  key xor -e -t "hello" -k "key"
"""

    def _xor(self, text: str, key: str) -> str:
        return "".join(chr(ord(t) ^ ord(k)) for t, k in zip(text, key, strict=True))

    def encode(self, args: object) -> CipherResult:
        text = getattr(args, "text", None)
        key = getattr(args, "key", None)
        if not text or not key:
            return CipherResult("Please provide -t <text> and -k <key>", False)
        if len(text) != len(key):
            return CipherResult("Text and key must be the same length for XOR", False)
        return CipherResult(self._xor(text, key), True)

    def decode(self, args: object) -> CipherResult:
        return self.encode(args)
