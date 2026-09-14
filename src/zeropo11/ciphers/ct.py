"""Code Transcript Brute-force cipher."""
from __future__ import annotations

from zeropo11.ciphers.base import BaseCipher, CipherResult

HELP = """USAGE:
  key ct [FLAGS] [OPTIONS]
FLAGS:
  -b, --brute   Brute-force code transcripts
OPTIONS:
  -t, --text <text>         Input text to match against
  -a, --alphabet <alpha>    Custom alphabet (must include 'A')
  -words, --words           Filter output to dictionary words only
  -lingo, --lingo <lang>    Language for word detection (default: en_US)
EXAMPLES:
  key ct -b -t "encoded message"
"""

# Build transcript set from ASCII ranges
_TRANSCRIPTS = {}
for code in range(65, 91):  # A-Z
    _TRANSCRIPTS[chr(code)] = chr(code + 32)
for code in range(97, 123):  # a-z
    _TRANSCRIPTS[chr(code)] = chr(code - 32)
for code in range(48, 58):  # 0-9
    _TRANSCRIPTS[chr(code)] = chr(code)


class Cipher(BaseCipher):
    """Code Transcript brute-force cipher."""

    name = "Code Transcript"
    command = "ct"
    help_menu = HELP

    def encode(self, args):
        return CipherResult("Code Transcript does not support encoding", False)

    def decode(self, args):
        return CipherResult("Code Transcript does not support decoding", False)

    def brute(self, args):
        text = getattr(args, "text", None)
        use_words = getattr(args, "words", False)
        if not text:
            return CipherResult("Please provide -t <text>", False)
        results = []
        for char in text:
            if char in _TRANSCRIPTS:
                results.append(_TRANSCRIPTS[char])
            else:
                results.append(char)
        output = "".join(results)
        if use_words:
            try:
                import enchant

                d = enchant.Dict("en_US")
                words = output.split()
                output = " ".join(w for w in words if d.check(w))
            except ImportError:
                pass
        return CipherResult(output, True)
