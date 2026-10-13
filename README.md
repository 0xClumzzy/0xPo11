```
  ___        ┌──────────────┐
 / _ \__  __/│ ◆ ENCRYPT    │
| | | \ \/ / │ ◆ DECRYPT    │
| |_| |>  <  │ ◆ CRACK      │
 \___//_/\_\ └──────────────┘
  0    x     [ REDACTED ]
```
## Overview

0xPo11 is a cryptographic suite built for malware analysis and offensive tooling development. It implements 28 ciphers from scratch - no external crypto libraries. Every operation works at the byte level using Python's `ord()` and `chr()` functions.

Built by [0xSESSIONS](https://github.com/0xClumzzy).

## Why This Project

Understanding cryptographic primitives is fundamental to both malware analysis and offensive tooling. This project demonstrates:

- How XOR, Base64, and encoding chains work in payload obfuscation
- How hash functions generate signatures for sample identification
- How layered encryption creates multi-stage droppers
- How brute force and wordlist attacks crack credentials

## Roadmap

| Phase  | Status | Feature | Purpose |
|------- |--------|---------|---------|
| 1 | [x] | 28 ciphers, XOR, hashing | Core crypto primitives |
| 2 | [x] | Keyconsole (interactive shell) | Rapid analysis workflow |
| 3 | [x] | Brute force / wordlist + `hashid` | Credential cracking & hash ID |
| 4 | [ ] | File encryption module | payload encryption |
| 5 | [ ] | Key exchange simulation | Understanding key management |
| 6 | [ ] | Ransom note generator | Full attack chain simulation |
| 7 | [ ] | C2 communication layer | Post-exploitation tooling |
| 8 | [ ] | Lateral movement module | Network propagation |
| 9 | [ ] | Rust migration | Full rewrite in Rust for speed/safety |

**Goal:** Complete ransomware simulation framework for understanding offensive techniques at every stage. **Long-term:** reimplement the suite in Rust (RustCrypto-style primitives, native binaries, single-static-binary distribution).

## Task List

Current, working and upcoming items. Checked items are done and verified.

- [x] CLI flags added: `--version` / `-v`, `-h`, `-u/--update`, `-rm/--remove`
- [x] Keyconsole tab completion for ciphers and commands
- [x] Keyconsole `list` command shows all ciphers with names
- [x] Keyconsole `clear`, `exit`, `quit` commands
- [x] Console cipher dispatch runs in-process (no per-command subprocess)
- [x] Layered encryption (`+`) and bare `+` usage guard
- [x] XOR cipher: fixed single-char-key bug (`zip()` truncated to shortest) and space-separator decode issue, key now cycles, round-trip verified
- [x] hashid cipher added (fingerprint hash type by length/charset)
- [x] Layered decryption (`hex -d + b64 -d + cc -d -k n` reverse-order chains) — round-trip verified
- [x] Decode-model: console `+` chains, no-mode layers default to `-e`, XOR `-d` space-separator fix
- [x] Decode-model: audit all 28 ciphers for a working `-d` path (some only `-e`/hash)
- [x] Decode-model: add a unified "auto-detect then decode" flag (`-ad` → hashid → brute in one command)
- [x] Decode-model: per-cipher decode examples for the phonebook (`key <cipher> -h`)
- [x] Decide: pure-Python rework vs. documented optional deps for the 4 ciphers below
- [ ] Fix `blowfish` cipher — missing `blowfish` package
- [ ] Fix `twofish` cipher — missing `twofish` package
- [ ] Fix `ct` cipher — missing `pyenchant` package
- [ ] Fix `pix` cipher — missing `Pillow` package
- [ ] `pix` channel arg required (crashes with `-e -t` alone) — make `-c` optional/default
- [x] Fix empty-wordlist brute force crash (e.g. `cc -b` with no matching wordlist)
- [x] Payload generator (`cp`) — ship default payload templates
- [x] Add `help <cipher>` to keyconsole for per-cipher usage
- [x] Add per-cipher `-h`/usage flag consistency
- [x] Remove ghost `translate` entry — no module exists; decide: implement or drop the reference

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| CLI | Click |
| Color output | colorama |
| Package manager | pip / setuptools |
| Installer | Bash |

### How It Works

Every cipher is built from first principles:

- **Character shifting** (Caesar, ROT13): `(ord(char) + key) % 26`
- **XOR operations**: `ord(char) ^ ord(key)`
- **Block ciphers**: Twofish/Blowfish via lightweight Python implementations
- **Hashing**: MD5, SHA family built on byte-level manipulation

No external crypto libraries. Everything operates on raw ASCII values and byte arrays.

### Optional Dependencies

Only needed for ciphers that currently fail without them. Each is imported lazily, so the rest of the suite works fine without them — running an affected cipher prints a clean `Install X: pip install X` hint:

| Package | Purpose | Needed by |
|---------|---------|-----------|
| Pillow | Image cipher support | `pix` |
| pyenchant | Wordlist filtering | `ct` |
| twofish | Block cipher | `twofish` |
| blowfish | Block cipher | `blowfish` |

## Installation

```bash
git clone https://github.com/0xClumzzy/0xPo11.git
cd 0xPo11
chmod +x install.sh
./install.sh
```

The installer creates a dedicated virtual environment at `~/.0xPo11/venv` and symlinks the `key` command into `~/.local/bin` — your system Python is never touched (no PEP 668 issues). `~/.local/bin` is added to your PATH if it is missing.

Restart your terminal after installation.

### Running 0xPo11

**Keyconsole (recommended)** — launch `key` once, then type cipher commands directly, with no `key` prefix:

```bash
key
[~] user@0xPo11 $ xor -e -t "cmd.exe /c powershell" -k "A"
```

**One-shot** — from a shell or a script, prefix the same command with `key`:

```bash
key xor -e -t "cmd.exe /c powershell" -k "A"
```

## Demos

The demo commands below run inside the keyconsole — no `key` prefix needed. From a plain shell, prefix the same line with `key` (e.g. `key xor -e -t "cmd.exe /c powershell" -k "A"`).

### XOR - String Encryption (Common in Malware)

```bash
xor -e -t "cmd.exe /c powershell" -k "A"
```

XOR is the most common string encryption technique in malware. Each character is XORed with the key character (the key repeats if it is shorter than the text), producing an encrypted string that can be decoded with the same key.

### Base64 Decode - Dropper Commands

```bash
b64 -d -t "Y21kLmV4ZSAvYyBwb3dlcnNoZWxs"
# Output: cmd.exe /c powershell
```

Most droppers use Base64 to hide commands in configuration files or network traffic. Quick decode reveals the actual payload.

### MD5 Hash - Sample Identification

```bash
md5 -e -t "malware_sample"
# Output: 9127daf288687deb678053e2aa828e7d
```

Generate hashes for tracking samples, creating YARA rules, or matching against known malware databases.

### Hash Identification - From Unknown Hash to Plaintext

```bash
hashid -e -t "1fb9c14e934b825a62d15230cc0c2bd1"
# Output: MD5 (or NTLM - same length/charset, test both)

md5 -b -t "1fb9c14e934b825a62d15230cc0c2bd1" -w rockyou.txt
# Output: Found: p@ssw0rd123
```

Fingerprint an unknown hash by length and charset, then crack it with a wordlist.

### Layered Encryption - Payload Obfuscation

```bash
cc -e -t "payload" -k 3 + b64 -e
# Output: c2Rib3JkZw==
```

Chain multiple ciphers to simulate how packers and obfuscators layer transformations to evade detection.

### Auto-Decode - Unknown Hash to Plaintext in One Command

```bash
-ad -t "1fb9c14e934b825a62d15230cc0c2bd1" -w rockyou.txt
# Output: Found: p@ssw0rd123
```

`-ad` fingerprints the hash with `hashid`, then brutes it against the wordlist — no need to know the hash type first.

### Payload Generator

```bash
cp -p duckyscript.txt            # copy a bundled template into the current dir
cp -g python.py -o ~/payloads    # -g is an alias for -p; -o picks the output dir
# seeded templates: duckyscript.txt  powershell.ps1  bash.sh  python.py
```

`cp` ships default payload templates in the wheel, seeds them into `~/.0xPo11/resources/payloads/` on first use, and user payloads dropped in that dir take precedence.

### Per-Cipher Help

```bash
help cc          # usage menu with working encode/decode examples
```

Every cipher exposes a consistent `help <cipher>` menu — no need to memorize flags. From a plain shell, `key cc -h` / `key cc --help` prints the same menu.

### Keyconsole - Interactive Analysis Shell

```bash
key
[~] user@0xPo11 $ xor -e -t "cmd.exe /c powershell" -k "K"
[~] user@0xPo11 $ b64 -d -t "Y21kLmV4ZSAvYyBwb3dlcnNoZWxs"
[~] user@0xPo11 $ md5 -e -t "sample.exe"
[~] user@0xPo11 $ help cc          # per-cipher usage, same menus as key cc -h
[~] user@0xPo11 $ list             # every cipher, with names
[~] user@0xPo11 $ version          # show the installed version
[~] user@0xPo11 $ clear            # clear the screen
[~] user@0xPo11 $ exit
```

Metasploit-style interactive shell for rapid cipher analysis and testing. Tab completion works for cipher names and console commands (`help`, `list`, `clear`, `version`, `update`, `remove`, `exit`).

## Available Ciphers

### Classical

| Cipher | Code | Description |
|--------|------|-------------|
| Caesar | `cc` | Shift cipher |
| Vigenère | `vc` | Polyalphabetic substitution |
| Reverse | `rc` | Reverse text |
| Multiplicative | `mc` | Multiplicative cipher |
| Monoalphabetic | `mo` | Monoalphabetic substitution |

### Encoding

| Cipher | Code | Description |
|--------|------|-------------|
| ROT13 | `r13` | ROT13 encoding |
| ROT47 | `r47` | ROT47 encoding |
| Base64 | `b64` | Base64 encoding |
| Binary | `bin` | Binary encoding |
| Hex | `hex` | Hexadecimal encoding |
| Octal | `oct` | Octal encoding |
| URL | `url` | URL encoding |
| L33T | `1337` | Leet speak |

### Hashing

| Cipher | Code | Description |
|--------|------|-------------|
| MD5 | `md5` | MD5 hash |
| SHA1 | `sha1` | SHA1 hash |
| SHA224 | `sha224` | SHA224 hash |
| SHA256 | `sha256` | SHA256 hash |
| SHA384 | `sha384` | SHA384 hash |
| SHA512 | `sha512` | SHA512 hash |

### Modern Encryption

| Cipher | Code | Description |
|--------|------|-------------|
| Twofish | `twofish` | Twofish encryption |
| Blowfish | `blowfish` | Blowfish encryption |
| XOR | `xor` | XOR cipher |

### Other

| Cipher | Code | Description |
|--------|------|-------------|
| Morse | `mor` | Morse code |
| Phonetic | `pho` | NATO phonetic alphabet |
| Pixel | `pix` | Image pixel cipher |
| Code Transcript | `ct` | Code transcript |
| Payloads | `cp` | Payload generation (`-p`, `-g`) |
| Hash Identifier | `hashid` | Fingerprint hash type by length/charset |

## Arguments

| Flag | Description |
|------|-------------|
| `-e` | Encrypt/Encode |
| `-d` | Decrypt/Decode |
| `-b` | Break/Brute force |
| `-ad` | Auto-detect hash type, then brute (hashid → crack in one command) |
| `-t` | Input text |
| `-k` | Encryption key |
| `-i` | Input file |
| `-o` | Output file |
| `-w` | Wordlist for brute force |
| `-r` | Range for brute force |
| `-s` | Hash salt |
| `-a` | Alphabet for brute force |
| `-ex` | Chars to exclude from brute force |
| `-md` | Encryption mode (e.g. `cbc` for blowfish) |
| `--iv` | Initialization vector |
| `-nc` | Nonce value |
| `-c` | Pixel channel (0/1/2, for `pix`) |
| `-ii` | Input image path (for `pix`) |
| `-g` | Generate a payload template (`cp`) |
| `-p` | Use a payload template (`cp`) |
| `-v` / `--version` | Show version |
| `-u` / `--update` | Check for updates |
| `-rm` / `--remove` / `--uninstall` | Uninstall 0xPo11 |
| `-h` / `--help` | Root help, or per-cipher help after a cipher name |

## Uninstalling

```bash
key --remove
```

Or from the Keyconsole:

```bash
key
[~] user@0xPo11 $ remove
```
