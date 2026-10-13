```
  ___        ┌──────────────┐
 / _ \__  __/│ ◆ ENCRYPT    │
| | | \ \/ / │ ◆ DECRYPT    │
| |_| |>  <  │ ◆ CRACK      │
 \___//_/\_\ └──────────────┘
  0    x     [ REDACTED ]
```
## Overview

0xPo11 is a cryptographic suite built for malware analysis and offensive tooling development. It implements 30 ciphers from scratch - no external crypto libraries. Every operation works at the byte level using Python's `ord()` and `chr()` functions.

Built by [0xSESSIONS](https://github.com/0xClumzzy). Developer guide: [README.dev.md](./README.dev.md).

## Why This Project

Understanding cryptographic primitives is fundamental to both malware analysis and offensive tooling. This project demonstrates:

- How XOR, Base64, and encoding chains work in payload obfuscation
- How hash functions generate signatures for sample identification
- How layered encryption creates multi-stage droppers
- How brute force and wordlist attacks crack credentials

## Roadmap

| Phase  | Status | Feature | Purpose |
|------- |--------|---------|---------|
| 1 | [x] | 30 ciphers, XOR, hashing | Core crypto primitives |
| 2 | [x] | Keyconsole (interactive shell) | Rapid analysis workflow |
| 3 | [x] | Brute force / wordlist + `hashid` | Credential cracking & hash ID |
| 4 | [x] | File encryption module | payload encryption |
| 5 | [ ] | Key exchange simulation | Understanding key management |
| 6 | [x] | Ransom note generator | Full attack chain simulation |
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
- [x] File encryption module (`fe`): PBKDF2 password derivation + SHA-256 CTR keystream + HMAC-SHA256 integrity, streaming 1 MiB chunks, versioned `0xFE` file format
- [x] Remote file encryption (`fe --host`): streams files over system ssh, no agent, explicit `--local-in`/`--local-out` locality
- [x] Ransom note generator (`rn`): three extortion-note templates (generic/polite/press), victim ID derived from the encrypted file's salt, deadline + key-fingerprint quoting
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

## Testing

```bash
./run_tests.sh
```

The runner manages its own virtualenv at `.venv/` (gitignored, separate from the install venv) and installs the test dependencies on first run.

| Command | Effect |
|---------|--------|
| `./run_tests.sh` | Run the full suite |
| `./run_tests.sh -k xor` | Forward any flags straight to pytest |
| `./run_tests.sh --cov` | Coverage report (`term-missing` + `htmlcov/`) |
| `./run_tests.sh --full` | Also install optional cipher deps (Pillow, pyenchant, ...) |
| `./run_tests.sh --rebuild` | Wipe `.venv/` and reinstall from scratch |

`TEST_VENV=/path/to/venv` overrides the test venv location; `PYTHON=/path/to/python` picks the base interpreter (3.10+ required).

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

### File Encryption - Password-Protected Payloads

```bash
fe -e -i payload.bin -k "hunter2" -o payload.bin.enc
fe -d -i payload.bin.enc -k "hunter2" -o payload.bin
# encrypt without -o writes payload.bin.enc; decrypt strips .enc back to payload.bin
```

Password-based file encryption built from stdlib primitives: **PBKDF2-HMAC-SHA256** derives an encryption key plus a separate MAC key (200,000 iterations, tunable with `-it`), a **SHA-256 counter-mode keystream** scrambles the file in 1 MiB chunks (streaming — the whole file is never held in memory), and an **HMAC-SHA256** covers the header and ciphertext. Decryption verifies the HMAC *before* writing anything, so a wrong password or a flipped byte fails cleanly instead of producing garbage.

Inline data works too — `fe -e -t "secret" -k "pass"` prints the ciphertext as hex, and `fe -d -t <hex> -k "pass"` prints it back.

> Educational implementation, not an audited crypto tool. Use [age](https://github.com/FiloSottile/age) or GPG to protect real secrets.

### Remote Hosts - Encrypt Files on Another Machine

```bash
fe -e --host deploy@10.0.0.5 -i /data/db.dump -k "hunter2" --local-out db.enc
fe -d --host deploy@10.0.0.5 --local-in -i db.enc -o /data/db.dump -k "hunter2"
```

`--host` streams the file over the system `ssh` binary — no remote agent, no remote install, nothing added to the far machine. Plaintext passes through the pipe and process memory only: it is never written to the remote disk and never lands in a local temp file. Files use the same `0xFE` format, so anything encrypted remotely decrypts locally and vice versa.

With `--host`, paths default to the **remote** side. `--local-in` / `--local-out` move one side back to this machine, so you always state explicitly which endpoint each path refers to. Failures (bad path, dead host, refused auth) come back as the server's own error, and a stalled transfer is killed at `--timeout` seconds.

### Ransom Note - Simulating the Extortion Artifact

```bash
rn -e -i victims.db.enc -k "hunter2" -tm press -o NOTE.txt
rn -e -tm polite -dl 24
```

`rn` generates the note that accompanies encrypted files, in three operator voices: `generic` (threat-and-authority), `polite` (customer-support framing), and `press` (fake press release threatening publication). Given an `fe`-encrypted file it derives the **victim ID from that file's salt**, so the same file always yields the same note — the coupling a real chain relies on. `-dl` sets the deadline, and the password's key fingerprint is quoted when `-k` is supplied.

Every note carries a simulation footer and obviously-fake payment placeholders, so output can never be mistaken for an operational demand. The point is pattern analysis: deadline pressure, the "free test decryption" trust trick, and the anti-forensic warnings ("don't use third-party tools") that appear in nearly every real sample.

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

## Hash Identification

`hashid` fingerprints an unknown hash by **length, charset, and prefix** — it is a heuristic, not a full parser like hashcat's mode detection. `-ad` then chains it straight into the brute-force ciphers.

### Identified and auto-crackable (`-ad`)

| Type | Detected by | Cracked via |
|------|-------------|-------------|
| MD5 / NTLM | 32 hex chars | `md5 -b` |
| SHA1 | 40 hex chars | `sha1 -b` |
| SHA224 | 56 hex chars | `sha224 -b` |
| SHA256 | 64 hex chars | `sha256 -b` |
| SHA384 | 96 hex chars | `sha384 -b` |
| SHA512 | 128 hex chars | `sha512 -b` |

Input mangling is handled first: `user:hash` column dumps and prefixes such as `$md5$`, `$1$`, `{md5}`, `{sha1}`, `{sha256}`, `$hash$`.

### Identified but not crackable

| Type | Detected by | Limitation |
|------|-------------|------------|
| bcrypt (`$2a$`, `$2b$`, `$2y$`) | 60 chars + `$2_$` prefix | no bcrypt brute implementation |
| MySQL 4.1 | 32 non-hex chars | no cipher |
| Whirlpool | 64 chars | no cipher |

### Not identified

Returns `No match for N chars` for anything outside the above, including other `crypt()` variants (`$5$`, `$6$`, `$y$`, `$P$B` WordPress/phpass, Django `pbkdf2_sha256$`), KDFs (scrypt, argon2), LM/LanMan, MD5-crypt, Cisco type 5/7/8/9, CRC32, and MySQL 323.

**Salted hashes** are only crackable manually — `-ad` cannot supply a salt:

```bash
md5 -b -t "<hash>" -s "<salt>" -w rockyou.txt
```

### Known ambiguities

Same length/charset means some types are indistinguishable — the tool flags them instead of guessing:

- **MD5 vs NTLM vs MySQL 4.1** — all 32 chars (reported as "MD5 (or NTLM - same length/charset, test both)")
- **SHA256 vs Whirlpool** — both 64 chars

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
| File Encryption | `fe` | Password-based authenticated file encryption |
| Ransom Note | `rn` | Extortion-note simulation (SE pattern analysis) |

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
| `-it` | PBKDF2 iterations for `fe` (default: 200000) |
| `--host` | Remote host for `fe` (`user@server`), streamed over ssh |
| `--port` | SSH port for `--host` (default: 22) |
| `--timeout` | SSH timeout for `--host` (default: 120 seconds) |
| `--local-in` | `-i` is a local path even with `--host` |
| `--local-out` | `-o` is a local path even with `--host` |
| `-tm` | Note template for `rn`: `generic` / `polite` / `press` |
| `-dl` | Payment deadline in hours for `rn` (default: 72) |
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
