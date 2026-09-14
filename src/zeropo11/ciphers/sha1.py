"""SHA-1 Hash cipher."""
from __future__ import annotations

import hashlib

from zeropo11.ciphers.base import BaseCipher, CipherResult

HELP_TEMPLATE = """USAGE:
  key {cmd} [FLAGS] [OPTIONS]
FLAGS:
  -e, --encode  Hash input text
  -b, --brute   Brute-force hash using wordlist or range
OPTIONS:
  -t, --text <text>       Input text to hash
  -s, --salt <salt>       Salt to prepend before hashing
  -w, --wordlist <file>   Wordlist file for brute-forcing
  -r, --range <range>     Dynamic range for brute-forcing (start,end)
EXAMPLES:
  key {cmd} -e -t "hello"
  key {cmd} -b -w wordlist.txt -s mysalt
"""


def _hash_func(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


class Cipher(BaseCipher):
    name = "SHA-1 Hash"
    command = "sha1"
    help_menu = HELP_TEMPLATE.format(cmd="sha1")

    def encode(self, args):
        text = getattr(args, 'text', None)
        salt = getattr(args, 'salt', None) or ""
        if not text:
            return CipherResult("Please provide -t <text>", False)
        return CipherResult(_hash_func((salt + text).encode()), True)

    def brute(self, args):
        wordlist = getattr(args, 'wordlist', None)
        salt = getattr(args, 'salt', None) or ""
        text = getattr(args, 'text', None)
        range_str = getattr(args, 'range', None)
        if not text:
            return CipherResult("Please provide -t <hash to crack>", False)
        candidates = []
        if wordlist:
            candidates = wordlist
        elif range_str:
            parts = range_str.split(",")
            candidates = [str(i) for i in range(int(parts[0]), int(parts[1]))]
        else:
            return CipherResult("Provide -w <wordlist> or -r <range>", False)
        for candidate in candidates:
            if _hash_func((salt + candidate).encode()) == text:
                return CipherResult(f"Found: {candidate}", True)
        return CipherResult("No match found", False)
