"""ROT47 Encoding cipher."""
from __future__ import annotations

from zeropo11.ciphers.base import BaseCipher, CipherResult


class Cipher(BaseCipher):
    name = "ROT47 Encoding"
    command = "r47"
    help_menu = """USAGE:
  key r47 [FLAGS] [OPTIONS]
FLAGS:
  -e, --encode  ROT47 encode input text
  -d, --decode  ROT47 decode input text
OPTIONS:
  -t, --text <text>  Input text
EXAMPLES:
  key r47 -e -t "Hello World!"
"""
    def encode(self, args):
        text = getattr(args, 'text', None)
        if not text:
            return CipherResult("Please provide -t <text>", False)
        result = []
        for c in text:
            code = ord(c)
            if 33 <= code <= 126:
                result.append(chr(33 + (code - 33 + 47) % 94))
            else:
                result.append(c)
        return CipherResult("".join(result), True)
    def decode(self, args):
        return self.encode(args)
