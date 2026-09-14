#!/usr/bin/python
# Hash Identifier
# created by : 0xSESSIONS

import re

# help menu for cipheringing process
help_menu = """
Usage:
  key hashid [FLAGS] [OPTIONS]

FLAGS:
  -e, --encode   Identify hash type

OPTIONS:
  -t, --text <hash>    Hash to identify

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

HEX_RE = re.compile(r'^[0-9a-f]+$')


def encode(args):
    text = (args.text or "").strip().lower()

    if not text:
        return ['Please provide a hash with -t <hash>', False]

    # strip common prefixes and column-format ("user:hash")
    stripped = text.split(':')[-1].strip()
    prefixes = ('$hash$', '$md5$', '$1$', '{md5}', '{sha1}', '{sha256}')
    for p in prefixes:
        if stripped.startswith(p):
            stripped = stripped.replace(p, '', 1)
            break

    hex_only = bool(HEX_RE.match(stripped))
    length = len(stripped)

    matches = []
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
        return [f"[✖] No match for {length}-char input. Not a common MD5/SHA hash format.", False]

    output = f"Hash | {stripped}\nLength | {length}\n\nPossible type(s):"
    for m in matches:
        output += f"\n  - {m}"
    output += "\n\nNext step: crack with 'key md5 -b -t <hash> -w <wordlist>' (if MD5/NTLM)"

    return [output, True]