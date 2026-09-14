"""Vigenere Cipher with frequency analysis brute-force."""
from __future__ import annotations

from collections import Counter

from zeropo11.ciphers.base import BaseCipher, CipherResult

ENGLISH_FREQ = [
    0.082, 0.015, 0.028, 0.043, 0.127, 0.022, 0.020, 0.061, 0.070,
    0.002, 0.008, 0.040, 0.024, 0.067, 0.075, 0.019, 0.001, 0.060,
    0.063, 0.091, 0.028, 0.010, 0.023, 0.002, 0.020, 0.001,
]


def _index_of_coincidence(text: str) -> float:
    n = len(text)
    if n <= 1:
        return 0.0
    counts = Counter(text)
    return sum(c * (c - 1) for c in counts.values()) / (n * (n - 1))


def _shift_text(text: str, shift: int) -> str:
    result = []
    for c in text:
        if c.isalpha():
            base = ord("A") if c.isupper() else ord("a")
            result.append(chr((ord(c) - base - shift) % 26 + base))
        else:
            result.append(c)
    return "".join(result)


def _find_key_length(text: str, max_len: int = 20) -> int:
    text_upper = text.upper()
    best_len = 1
    best_score = 0.0
    for kl in range(1, min(max_len + 1, len(text_upper))):
        groups = [text_upper[i::kl] for i in range(kl)]
        avg_ic = sum(_index_of_coincidence(g) for g in groups if len(g) > 1) / kl
        score = abs(avg_ic - 0.065)
        if best_score == 0 or score < best_score:
            best_score = score
            best_len = kl
    return best_len


def _find_shift(text: str) -> int:
    text_upper = "".join(c for c in text if c.isalpha()).upper()
    if not text_upper:
        return 0
    best_shift = 0
    best_score = float("inf")
    for shift in range(26):
        shifted = _shift_text(text_upper, shift)
        counts = Counter(shifted)
        n = len(shifted)
        freq = [counts.get(chr(i + ord("A")), 0) / n for i in range(26)]
        score = sum((f - ef) ** 2 for f, ef in zip(freq, ENGLISH_FREQ, strict=True))
        if score < best_score:
            best_score = score
            best_shift = shift
    return best_shift


class _Args:
    def __init__(self, **kwargs: object) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


class Cipher(BaseCipher):
    name = "Vigenere Cipher"
    command = "vc"
    help_menu = """USAGE:
  key vc [FLAGS] [OPTIONS]
FLAGS:
  -e, --encode  Encode input text
  -d, --decode  Decode input text
  -b, --brute  Brute-force using frequency analysis
OPTIONS:
  -t, --text <text>  Input text
  -k, --key <key>    Encryption key (text)
EXAMPLES:
  key vc -e -t "hello" -k "secret"
  key vc -b -t "encrypted text"
"""

    def encode(self, args: object) -> CipherResult:
        text = getattr(args, "text", None)
        key = getattr(args, "key", None)
        if not text or not key:
            return CipherResult("Please provide -t <text> and -k <key>", False)
        key = key.upper()
        result = []
        ki = 0
        for c in text:
            if c.isalpha():
                base = ord("A") if c.isupper() else ord("a")
                shift = ord(key[ki % len(key)]) - ord("A")
                result.append(chr((ord(c) - base + shift) % 26 + base))
                ki += 1
            else:
                result.append(c)
        return CipherResult("".join(result), True)

    def decode(self, args: object) -> CipherResult:
        text = getattr(args, "text", None)
        key = getattr(args, "key", None)
        if not text or not key:
            return CipherResult("Please provide -t <text> and -k <key>", False)
        key = key.upper()
        result = []
        ki = 0
        for c in text:
            if c.isalpha():
                base = ord("A") if c.isupper() else ord("a")
                shift = ord(key[ki % len(key)]) - ord("A")
                result.append(chr((ord(c) - base - shift) % 26 + base))
                ki += 1
            else:
                result.append(c)
        return CipherResult("".join(result), True)

    def brute(self, args: object) -> CipherResult:
        text = getattr(args, "text", None)
        if not text:
            return CipherResult("Please provide -t <text>", False)
        try:
            key_length = _find_key_length(text)
            text_upper = "".join(c for c in text if c.isalpha()).upper()
            shifts = []
            for i in range(key_length):
                group = text_upper[i::key_length]
                shifts.append(_find_shift(group))
            key = "".join(chr(s + ord("A")) for s in shifts)
            decoded = self.decode(_Args(text=text, key=key))
            output = f"Detected key: {key}\n{decoded.output}"
            return CipherResult(output, True)
        except (ZeroDivisionError, ValueError):
            return CipherResult("Text too short for frequency analysis", False)
