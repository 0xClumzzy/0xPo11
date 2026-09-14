"""L33T 5P34K Encoding cipher."""  # noqa: N999
from __future__ import annotations

from zeropo11.ciphers.base import BaseCipher, CipherResult

CHAR_TO_1337: dict[str, str] = {
    'a': '4', 'b': '8', 'c': '(', 'd': '|)', 'e': '3', 'f': '|=',
    'g': '6', 'h': '#', 'i': '1', 'j': '_|', 'k': '|<', 'l': '|_',
    'm': '|v|', 'n': '|\\|', 'o': '0', 'p': '|*', 'q': '(,)',
    'r': '|2', 's': '5', 't': '7', 'u': '|_|', 'v': '\\/',
    'w': '\\/\\/', 'x': '><', 'y': '`/', 'z': '2',
}
_1337_TO_CHAR: dict[str, str] = {v: k for k, v in CHAR_TO_1337.items()}

class Cipher(BaseCipher):
    name = "L33T 5P34K"
    command = "1337"
    help_menu = """USAGE:
  key 1337 [FLAGS] [OPTIONS]
FLAGS:
  -e, --encode  Encode to leet speak
  -d, --decode  Decode from leet speak
OPTIONS:
  -t, --text <text>  Input text
EXAMPLES:
  key 1337 -e -t "hello"
"""
    def encode(self, args):
        text = getattr(args, 'text', None)
        if not text:
            return CipherResult("Please provide -t <text>", False)
        result = "".join(CHAR_TO_1337.get(c.lower(), c) for c in text)
        return CipherResult(result, True)
    def decode(self, args):
        text = getattr(args, 'text', None)
        if not text:
            return CipherResult("Please provide -t <text>", False)
        result = []
        i = 0
        while i < len(text):
            matched = False
            for length in range(4, 0, -1):
                chunk = text[i:i + length]
                if chunk in _1337_TO_CHAR:
                    result.append(_1337_TO_CHAR[chunk])
                    i += length
                    matched = True
                    break
            if not matched:
                result.append(text[i])
                i += 1
        return CipherResult("".join(result).capitalize(), True)
