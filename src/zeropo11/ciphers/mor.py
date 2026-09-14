"""Morse Code cipher."""
from __future__ import annotations

from zeropo11.ciphers.base import BaseCipher, CipherResult

CHAR_TO_MORSE: dict[str, str] = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..',
    '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
    '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.',
    ' ': '/', '.': '.-.-.-', ',': '--..--', '?': '..--..', "'": '.----.',
    '!': '-.-.--', '/': '-..-.', '(': '-.--.', ')': '-.--.-', '&': '.-...',
    ':': '---...', ';': '-.-.-.', '=': '-...-', '+': '.-.-.', '-': '-....-',
    '_': '..--.-', '"': '.-..-.', '$': '...-..-', '@': '.--.-.',
}
MORSE_TO_CHAR: dict[str, str] = {v: k for k, v in CHAR_TO_MORSE.items()}

class Cipher(BaseCipher):
    name = "Morse Code"
    command = "mor"
    help_menu = """USAGE:
  key mor [FLAGS] [OPTIONS]
FLAGS:
  -e, --encode  Encode to Morse code
  -d, --decode  Decode from Morse code
OPTIONS:
  -t, --text <text>  Input text
EXAMPLES:
  key mor -e -t "hello world"
"""
    def encode(self, args):
        text = getattr(args, 'text', None)
        if not text:
            return CipherResult("Please provide -t <text>", False)
        result = " ".join(CHAR_TO_MORSE.get(c.upper(), c) for c in text)
        return CipherResult(result, True)
    def decode(self, args):
        text = getattr(args, 'text', None)
        if not text:
            return CipherResult("Please provide -t <text>", False)
        try:
            result = "".join(MORSE_TO_CHAR.get(c, c) for c in text.split(" "))
            return CipherResult(result, True)
        except Exception as e:
            return CipherResult(str(e), False)
