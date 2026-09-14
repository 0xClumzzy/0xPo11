"""Configuration: colors, paths, banners, version."""

from __future__ import annotations

import getpass
from pathlib import Path

from colorama import Fore

# Version
VERSION = "2.0.0"

# User
USERNAME = getpass.getuser()

# Paths
LOCAL_PATH = Path(f"/home/{USERNAME}/.0xPo11" if USERNAME != "root" else "/root/.0xPo11")

# Colors
SUCCESS = "\033[92m"
FAIL = "\033[91m"
END = "\033[0m"
CMD_PREFIX = f"{Fore.CYAN}[~] {Fore.RESET}"

# Header for interactive console
HEADER = f"{Fore.RED}{USERNAME}{Fore.WHITE}@{Fore.RED}0xPo11 $ {Fore.RESET}"

# Banner
# Banner - loaded from original to avoid quote escaping issues
def _load_banner() -> str:
    """Load the ASCII art banner."""
    fallback = r"""
                     _,=;::::::;=,,_
                 _,;,ss*"":::::'""sss;;,_
               ,;,sSSSss::::::::*"sSSss;;,
             ,;,sSSSKKk*:::::::::*kkKKKKk;,
            ,;kKKKKEEee::::::::::,eEEELEEe;,
           ,;;;eEEEEEEe*:::::::::,lL",LLLl;;;
           ;ll;;LLLLLLl::::::::_Ll *LLLLl;ll;
           ;*ll,lLLLEee:::::::*:::EeEEEE;*eE;
           ;;*EeeEEEEee::::::::::*eEEEEE;eE;;
           ;;;e'eeEEeEe,_::::::_,eeEEEET;Tt;;
            ;;t;""  '"=:::::::="'   '";;Tt'
             Ttt         ";::;*         t;T;
             t;Tt.,,_ _,_::::;;     __,tT;T
            =t;;*TTt=-=-=T:' ';T=_=_=tTT;,Tt=
            tTTT;"ttT TT;t"   :tt tTo00;OO'0
              0Oo*oOOOo'0"    ':O OO0o0oOo0'

            0xPo11 Version : """ + VERSION
    return fallback

BANNER = Fore.RED + _load_banner() + Fore.RESET

HELP_MENU = Fore.CYAN + """
┌─────────────────────────────────────────────────────────────┐
│ [■] EXAMPLE: key cc -e -t "Encrypt Me" -k 5                 │
│                                                             │
│ [■] ARG 1. Cipher                                           │
│       [cc] ───────── Caesar Cipher                          │
│       [vc] ───────── Vigenere Cipher                        │
│       [rc] ───────── Reverse Cipher                         │
│       [mc] ───────── Multiplicative Cipher                  │
│       [ct] ───────── Code Transcript                        │
│       [mo] ───────── Monoalphabetic Cipher                  │
│       [url] ──────── URL Encoding                           │
│       [xor] ──────── XOR Cipher                             │
│       [r13] ──────── ROT 13 Encoding                        │
│       [r47] ──────── ROT 47 Encoding                        │
│       [b64] ──────── Base64 Encoding                        │
│       [bin] ──────── Binary Encoding                        │
│       [pix] ──────── Image Pixel                            │
│       [hex] ──────── Hex Encoding                           │
│       [oct] ──────── Octal Encoding                         │
│       [mor] ──────── Morse Code Cipher                      │
│       [pho] ──────── Phonetic Alphabet Cipher               │
│       [md5] ──────── MD5 Hash                               │
│       [1337] ─────── L33T 5P34K Encoding                    │
│       [sha1] ─────── SHA1 Hash                              │
│       [sha224] ───── SHA224 Hash                            │
│       [sha384] ───── SHA384 Hash                            │
│       [sha512] ───── SHA512 Hash                            │
│       [twofish] ──── Twofish Encryption                     │
│       [blowfish] ─── Blowfish Encryption                    │
│       [translate] ── Google Translate API                   │
├─────────────────────────────────────────────────────────────┤
│ [■] ARG 2. Ciphering Method                                 │
│       [-e] ────────── Encrypt/Encode                        │
│       [-d] ────────── Decrypt/Decode                        │
│       [-b] ────────── Break/Brute Force                     │
├─────────────────────────────────────────────────────────────┤
│ [■] Additional Arguments                                    │
│       [-t] ────────── Input Text                            │
│       [-i] ────────── Input File                            │
│       [-o] ────────── Output File                           │
│       [-k] ────────── Encryption Key                        │
│       [-s] ────────── Hash Salt                             │
│       [-r] ────────── Range                                 │
│       [-w] ────────── Wordlist                              │
│       [-a] ────────── Custom Alphabet                       │
│       [-md] ───────── Encryption Mode                       │
│       [-src] ──────── Source Language                       │
│       [-dest] ─────── Destination Language                  │
│       [-lingo] ────── Set Language ["en_US" Default]        │
│       [-words] ────── Pull Words From Output                │
├─────────────────────────────────────────────────────────────┤
│ [■] 0xPo11 Arguments                                         │
│       [--help] ────── help                                  │
│       [--version] ─── version                               │
│       [--update] ──── update                                │
└─────────────────────────────────────────────────────────────┘
""" + Fore.RESET
