"""Phonetic Alphabet cipher."""
from __future__ import annotations

from zeropo11.ciphers.base import BaseCipher, CipherResult

CHAR_TO_PHONETIC: dict[str, str] = {
    'A': 'Alfa', 'B': 'Bravo', 'C': 'Charlie', 'D': 'Delta', 'E': 'Echo',
    'F': 'Foxtrot', 'G': 'Golf', 'H': 'Hotel', 'I': 'India', 'J': 'Juliett',
    'K': 'Kilo', 'L': 'Lima', 'M': 'Mike', 'N': 'November', 'O': 'Oscar',
    'P': 'Papa', 'Q': 'Quebec', 'R': 'Romeo', 'S': 'Sierra', 'T': 'Tango',
    'U': 'Uniform', 'V': 'Victor', 'W': 'Whiskey', 'X': 'X-ray', 'Y': 'Yankee',
    'Z': 'Zulu',
}
PHONETIC_TO_CHAR: dict[str, str] = {v.upper(): k for k, v in CHAR_TO_PHONETIC.items()}

class Cipher(BaseCipher):
    name = "Phonetic Alphabet"
    command = "pho"
    help_menu = """USAGE:
  key pho [FLAGS] [OPTIONS]
FLAGS:
  -e, --encode  Encode to phonetic alphabet
  -d, --decode  Decode from phonetic alphabet
OPTIONS:
  -t, --text <text>  Input text
EXAMPLES:
  key pho -e -t "hello"
"""
    def encode(self, args):
        text = getattr(args, 'text', None)
        if not text:
            return CipherResult("Please provide -t <text>", False)
        result = " ".join(CHAR_TO_PHONETIC.get(c.upper(), c) for c in text)
        return CipherResult(result, True)
    def decode(self, args):
        text = getattr(args, 'text', None)
        if not text:
            return CipherResult("Please provide -t <text>", False)
        words = text.upper().split(" ")
        result = "".join(PHONETIC_TO_CHAR.get(w, w) for w in words)
        return CipherResult(result, True)
