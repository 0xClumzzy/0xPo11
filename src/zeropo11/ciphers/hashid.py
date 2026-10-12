"""Hash Identifier - identify common hash types by length and charset."""
from __future__ import annotations

import re

from zeropo11.ciphers.base import BaseCipher, CipherResult

HELP_MENU = """USAGE:
  key hashid [FLAGS] [OPTIONS]
FLAGS:
  -e, --encode  Identify hash type
  -d, --decode  Not supported (identification only)
OPTIONS:
  -t, --text <hash>  Hash to identify
EXAMPLES:
  key hashid -t 9127daf288687deb678053e2aa828e7d
  key hashid -t 5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8
"""

# (length, hex_charset, prefix, name)
RULES = [
    (128, True, None, "SHA512"),
    (96, True, None, "SHA384"),
    (64, True, None, "SHA256"),
    (56, True, None, "SHA224"),
    (40, True, None, "SHA1"),
    (32, True, None, "MD5"),
    (32, False, None, "NTLM"),
    (32, False, None, "MySQL 4.1"),
    (60, False, "$2a$", "bcrypt ($2a$)"),
    (60, False, "$2b$", "bcrypt ($2b$)"),
    (60, False, "$2y$", "bcrypt ($2y$)"),
    (64, False, None, "SHA256 (hex) / Whirlpool"),
]

HEX_RE = re.compile(r"^[0-9a-f]+$")


class Cipher(BaseCipher):
    name = "Hash Identifier"
    command = "hashid"
    help_menu = HELP_MENU

    def encode(self, args) -> CipherResult:
        text = (args.text or "").strip().lower()
        if not text:
            return CipherResult("Please provide a hash with -t <hash>", False)

        # Strip common prefixes and column-format ("user:hash")
        stripped = text.split(":")[-1].strip()
        prefixes = ("$hash$", "$md5$", "$1$", "{md5}", "{sha1}", "{sha256}")
        for prefix in prefixes:
            if stripped.startswith(prefix):
                stripped = stripped.replace(prefix, "", 1)
                break

        hex_only = bool(HEX_RE.match(stripped))
        length = len(stripped)

        matches: list[str] = []
        for size, is_hex, prefix, name in RULES:
            if size != length:
                continue
            if prefix and not stripped.startswith(prefix):
                continue
            if not prefix and is_hex and not hex_only:
                continue

            # NTLM vs MD5: identical 32-hex, so highlight the ambiguity
            candidate = name
            if size == 32 and is_hex:
                candidate = "MD5 (or NTLM - same length/charset, test both)"
            if candidate not in matches:
                matches.append(candidate)

        if not matches:
            return CipherResult(f"No match for {length} chars", False)

        output = f"Hash | {stripped}\nLength | {length}\n\nPossible type(s):"
        for match in matches:
            output += f"\n  - {match}"
        output += "\n\nNext step: crack with 'key md5 -b -t <hash> -w <wordlist>' (if MD5/NTLM)"
        return CipherResult(output, True)

    def decode(self, args) -> CipherResult:
        return CipherResult(
            "Hash identification does not support decode (use -e to identify)", False
        )

    def brute(self, args) -> CipherResult:
        return CipherResult("Hash identification does not support brute-force", False)