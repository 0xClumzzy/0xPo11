"""Base64 Encoding cipher."""
from __future__ import annotations

import base64

from zeropo11.ciphers.base import BaseCipher, CipherResult


class Cipher(BaseCipher):
    name = "Base64 Encoding"
    command = "b64"
    help_menu = """USAGE:
  key b64 [FLAGS] [OPTIONS]
FLAGS:
  -e, --encode  Encode input text
  -d, --decode  Decode input text
OPTIONS:
  -t, --text <text>  Input text
  -i, --inputFile <file>  Input file
  -o, --output <file>  Output file
EXAMPLES:
  key b64 -e -t "hello world"
"""
    def encode(self, args):
        text = getattr(args, 'text', None)
        if not text:
            return CipherResult("Please provide -t <text>", False)
        return CipherResult(base64.b64encode(text.encode()).decode(), True)
    def decode(self, args):
        text = getattr(args, 'text', None)
        if not text:
            return CipherResult("Please provide -t <text>", False)
        try:
            return CipherResult(base64.b64decode(text.encode()).decode(), True)
        except Exception as e:
            return CipherResult(str(e), False)
