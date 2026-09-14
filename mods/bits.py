# import getpasscd
import getpass
import os

from colorama import Fore

# Variables
username = getpass.getuser() # Get username
header = Fore.RED + f'{username}' + Fore.WHITE + '@' + Fore.RED + '0xPo11 $ ' + Fore.RESET # header for user input

# Resolve paths: prefer installed location, fall back to project directory
_installed_path = f'/home/{username}/.0xPo11' if username != 'root' else '/root/.0xPo11'
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
local_path = _installed_path if os.path.isdir(_installed_path) else _project_root
cipher = f'{local_path}/ciphers/' # local path to ciphers

# Colors
SUCCESS = '\033[92m'
FAIL = '\033[91m'
END = '\033[0m'

version = open(f'{local_path}/version.txt').read().strip()
banner = Fore.RED + f'''
  ╔═══════════════════════════════════════════════════════╗
  ║  ╔═╗╔═╗╔╦╗╔═╗  ╔═╗╦ ╦╔═╗╔═╗╔╦╗                     ║
  ║  ╚═╗╠═╣║║║║╣   ╠═╣║║║╠═╣║   ║                      ║
  ║  ╚═╝╩ ╩╩ ╩╚═╝  ╩ ╩╚╩╝╩ ╩╚═╝ ╩                      ║
  ║─────────────────────────────────────────────────────║
  ║  🔑 ENCRYPT  🔓 DECRYPT  ⚡ CRACK  🛡️ ANALYZE      ║
  ║─────────────────────────────────────────────────────║
  ║              ◆ Version {version} ◆                        ║
  ╚═══════════════════════════════════════════════════════╝
''' + Fore.RESET

help_menu = Fore.CYAN + """
┌─────────────────────────────────────────────────────────────┐
│  EXAMPLE: key cc -e -t "Encrypt Me" -k 5                   │
├─────────────────────────────────────────────────────────────┤
│  CIPHERS                                                    │
│                                                             │
│  Classical Ciphers                                          │
│    cc ──── Caesar Cipher           mc ──── Multiplicative   │
│    vc ──── Vigenère Cipher         mo ──── Monoalphabetic   │
│    rc ──── Reverse Cipher          ct ──── Code Transcript  │
│                                                             │
│  Encoding                                                   │
│    r13 ─── ROT13                   r47 ─── ROT47            │
│    b64 ─── Base64                  hex ─── Hexadecimal      │
│    bin ─── Binary                  oct ─── Octal            │
│    url ─── URL Encoding            1337 ── L33T 5P34K       │
│                                                             │
│  Hashing                                                    │
│    md5 ─── MD5                     sha1 ── SHA1             │
│    sha224 ─ SHA224                 sha384 ─ SHA384          │
│    sha512 ─ SHA512                                     │
│                                                             │
│  Modern Encryption                                          │
│    twofish ─ Twofish               blowfish ─ Blowfish      │
│    xor ──── XOR Cipher                                │
│                                                             │
│  Other                                                      │
│    mor ──── Morse Code             pho ──── Phonetic        │
│    pix ──── Image Pixel            translate ─ Google API   │
├─────────────────────────────────────────────────────────────┤
│  METHODS                                                    │
│    -e ──── Encrypt/Encode                                   │
│    -d ──── Decrypt/Decode                                   │
│    -b ──── Break/Brute Force                                │
├─────────────────────────────────────────────────────────────┤
│  ARGUMENTS                                                  │
│    -t ──── Input Text           -k ──── Key                 │
│    -i ──── Input File           -o ──── Output File         │
│    -s ──── Hash Salt            -w ──── Wordlist            │
│    -r ──── Range                -a ──── Custom Alphabet     │
│    -md ─── Mode                 -src ── Source Language      │
│    -dest ─ Dest Language        -lingo ─ Language           │
│    -words ─ Pull Words                                   │
├─────────────────────────────────────────────────────────────┤
│  0xPo11                                                     │
│    --help ──── Show help            --version ── Version    │
│    --update ── Update               --remove ── Uninstall   │
└─────────────────────────────────────────────────────────────┘
""" + Fore.RESET
