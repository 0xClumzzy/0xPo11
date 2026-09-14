"""URL Encoding cipher."""
from __future__ import annotations

from urllib.parse import quote, unquote

from zeropo11.ciphers.base import BaseCipher, CipherResult


class Cipher(BaseCipher):
    name = "URL Encoding"
    command = "url"
    help_menu = """USAGE:
  key url [FLAGS] [OPTIONS]
FLAGS:
  -e, --encode  Encode input text
  -d, --decode  Decode input text
OPTIONS:
  -t, --text <text>  Input text
EXAMPLES:
  key url -e -t "hello world"
"""
    def encode(self, args):
        text = getattr(args, 'text', None)
        if not text:
            return CipherResult("Please provide -t <text>", False)
        return CipherResult(quote(text), True)
    def decode(self, args):
        text = getattr(args, 'text', None)
        if not text:
            return CipherResult("Please provide -t <text>", False)
        return CipherResult(unquote(text), True)
