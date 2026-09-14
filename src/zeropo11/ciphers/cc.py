"""Caesar Cipher."""
from __future__ import annotations

from zeropo11.ciphers.base import BaseCipher, CipherResult


class Cipher(BaseCipher):
    name = "Caesar Cipher"
    command = "cc"
    DEFAULT_EXCLUDE = "\\n\\t .?!,/\\\\<>|[]{}@#$%^&*()-_=+`~:;\\\"'0123456789"
    help_menu = """USAGE:
  key cc [FLAGS] [OPTIONS]
FLAGS:
  -b, --brute   Brute force the caesar cipher
  -d, --decode  Decrypt input text or file
  -e, --encode  Encrypt input text or file
OPTIONS:
  -ex, --exclude <exclude list>  Custom exclude list for brute forcing
  -i, --inputFile <input file>   Input file to encrypt or decrypt
  -k, --key <key>                Key for encoding or decoding
  -o, --output <output file>     Output file for encrypted or decrypted text
  -r, --range <range>            Range for brute forcing (start,finish)
  -t, --text <text>              Input text to encrypt or decrypt
EXAMPLES:
  key cc -e -k 5 -t hello -ex "asd[]"
"""

    def encode(self, args: object) -> CipherResult:
        text = getattr(args, "text", None)
        key = getattr(args, "key", None)
        exclude = getattr(args, "exclude", None) or self.DEFAULT_EXCLUDE
        if not text or not key:
            return CipherResult("Please provide -t <text> and -k <key>", False)
        result = []
        for c in text:
            if c in exclude:
                result.append(c)
            elif c.isupper():
                result.append(chr((ord(c) + int(key) - 65) % 26 + 65))
            else:
                result.append(chr((ord(c) + int(key) - 97) % 26 + 97))
        return CipherResult("".join(result), True)

    def decode(self, args: object) -> CipherResult:
        text = getattr(args, "text", None)
        key = getattr(args, "key", None)
        exclude = getattr(args, "exclude", None) or self.DEFAULT_EXCLUDE
        if not text or not key:
            return CipherResult("Please provide -t <text> and -k <key>", False)
        result = []
        for c in text:
            if c in exclude:
                result.append(c)
            elif c.isupper():
                result.append(chr((ord(c) - int(key) - 65) % 26 + 65))
            else:
                result.append(chr((ord(c) - int(key) - 97) % 26 + 97))
        return CipherResult("".join(result), True)

    def brute(self, args: object) -> CipherResult:
        text = getattr(args, "text", None)
        exclude = getattr(args, "exclude", None) or self.DEFAULT_EXCLUDE
        range_str = getattr(args, "range", None)
        if not text:
            return CipherResult("Please provide -t <text>", False)
        range_parts = range_str.split(",") if range_str else ["0", "27"]
        start, end = int(range_parts[0]), int(range_parts[1])
        results = []
        for shift in range(start, end):
            inner = []
            for c in text:
                if c in exclude:
                    inner.append(c)
                elif c.isupper():
                    inner.append(chr((ord(c) - shift - 65) % 26 + 65))
                else:
                    inner.append(chr((ord(c) - shift - 97) % 26 + 97))
            decoded = "".join(inner)
            if decoded != text:
                results.append(f"Key [{shift}] | {decoded}")
        return CipherResult("\\n".join(results), True)
