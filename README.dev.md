# 0xPo11 — Developer Guide

Architecture, conventions, and workflows for contributing to 0xPo11. User-facing docs: [README.md](./README.md).

## Quick Start

```bash
git clone https://github.com/0xClumzzy/0xPo11.git
cd 0xPo11
./run_tests.sh            # provisions .venv/ and runs the suite
```

```bash
./run_tests.sh --full     # also install optional cipher deps (Pillow, pyenchant, twofish, blowfish)
./run_tests.sh --cov      # coverage report (term-missing + htmlcov/)
./run_tests.sh -k xor     # forwards flags straight to pytest
./run_tests.sh --rebuild  # wipe .venv/ and reinstall
```

Smoke-test the CLI without installing (the `key` entry point is equivalent):

```bash
PYTHONPATH=src python3 -m zeropo11 --version
PYTHONPATH=src python3 -m zeropo11 xor -e -t "cmd.exe /c powershell" -k "A"
```

## Repository Layout

```
src/zeropo11/
├── __init__.py                # __version__ (package version source)
├── __main__.py                # enables `python -m zeropo11`
├── cli.py                     # the whole CLI: main(), keyconsole, dispatch, layered, -ad/-u/-rm
├── config.py                  # colors, banner, HELP_MENU (static text!), VERSION, paths
├── utils.py                   # handle_output, read_input_file, read_wordlist
└── ciphers/
    ├── base.py                # BaseCipher + CipherResult contract
    ├── registry.py            # auto-discovery, dispatch by command string
    ├── cc.py  b64.py  ...     # one module per cipher, class always named `Cipher`
    ├── hashid.py              # fingerprint-by-length RULES table
    ├── fe.py                  # password-based authenticated file encryption
    ├── cp.py                  # payload template copier (ships in the wheel)
    └── templates/payloads/    # bundled payload templates (setuptools package-data)
tests/                         # pytest suite (7 modules)
install.sh                     # venv-based installer: ~/.0xPo11/venv + ~/.local/bin/key shim
run_tests.sh                   # self-provisioning test runner
resources/update.sh            # git clone + install.sh (also what -u runs)
pyproject.toml                 # build system, deps, extras, `key` console script
version.txt                    # version advertised to GitHub clients (used by -u)
```

> **Legacy layout** — the repo-root `main.py`, `ciphers/`, and `mods/` are the original
> argparse implementation. They are superseded by `src/zeropo11/`, kept only for historical
> reference, and should not be extended. All active work happens under `src/`.

## Architecture

### Registry: zero-config discovery

`registry.py` walks `zeropo11.ciphers` with `pkgutil.iter_modules`, imports each module, and
registers any class that subclasses `BaseCipher` and sets a non-empty `command`. **Dropping a
new `.py` file into `ciphers/` is the entire registration step.**

```
get_cipher("cc")           → Cipher instance          (KeyError → "not found" message)
list_ciphers()             → sorted commands          (drives `list` and tab completion)
get_cipher_info()          → [(command, name), ...]   (drives keyconsole `list`)
```

Two consequences of the discovery mechanism:

- A module that raises `ImportError` is **silently skipped** — the cipher vanishes instead of
  erroring. Therefore optional third-party backends must be imported **lazily, inside the
  function** (see below), never at module top level.
- Discovery is lazy on first use and cached (`_loaded`), so no import cost at CLI startup.

### The cipher contract

```python
@dataclass
class CipherResult:
    output: str
    success: bool          # __iter__/__getitem__ keep legacy `out, ok = result` working

class BaseCipher:
    name: str = "Unknown"          # shown by `list`
    command: str = ""              # CLI token, e.g. "cc"
    help_menu: str = ""            # shown by `key <cmd> -h` / `help <cmd>`
    def encode/decode/brute(args) -> CipherResult: ...
```

Ciphers receive an **opaque args object** and read fields with `getattr(args, "field", None)` —
duck typing, so a cipher never imports the CLI. The namespace passed in is `_Args` from `cli.py`
built by `_build_args()`:

| Attribute | Source | Notes |
|-----------|--------|-------|
| `text` | `-t`, or pre-loaded from `-i` | already file contents if `-i` given |
| `key`, `salt`, `iv` | `-k`, `-s`, `--iv` | |
| `range`, `wordlist` | `-r`, `-w` | **`wordlist` is already `list[str]`** (read by the CLI) |
| `alphabet`, `lingo`, `words` | `-a`, `-lingo`, `-words` | |
| `mode` | `-md` | legacy mode selector for blowfish/twofish |
| `exclude` | `-ex` | chars to skip in brute force |
| `nonce` | `-nc` | int |
| `channel`, `inputImage` | `-c`, `-ii` | pixel cipher |
| `iterations` | `-it` | PBKDF2 round count for `fe` |
| `file` | `-i` | path (raw, alongside pre-loaded `text`) |
| `payload`, `generate`, `output` | `-p`, `-g`, `-o` | `payload` also mirrors `generate` |

### Binary ciphers

Ciphers that handle arbitrary bytes (file encryption) set `binary = True` on the class. Two
consequences in `main()`: the CLI **skips** pre-reading the input file as text (which would
`UnicodeDecodeError` on binary input), and the result is **printed only** — the cipher owns its
output files end to end instead of routing through `handle_output`. See `fe.py` for the
reference implementation.
| `range_` → exposed as `range` | | see `_build_args` |

### CLI dispatch flow

**One-shot** (`key cc -e -t hi -k 3`):

```
main() [flat click command, ignore_unknown_options]
  ├─ pre-scan sys.argv for exact tokens "-rm" / "-u" / "--remove" / "--uninstall"
  │     (click would otherwise eat "-rm" as "-r m"; -rm is deliberately NOT a declared flag)
  ├─ remove / update → _do_remove() / _do_update()  (early return)
  ├─ -ad → _run_auto_decode()                        (early return)
  ├─ cipher in ("-h","--help") → HELP_MENU
  ├─ no cipher + argv → HELP_MENU | no args → _run_console()
  └─ get_cipher(cipher) → _build_args(_Args) → _dispatch() → handle_output()
```

`_dispatch()` resolves, in order: `payload/generate` → `cipher.payload()`, else
`mode` (`-e/-d/-b`) → `encode/decode/brute`. If no mode is given it prints the cipher's
`help_menu`. Exceptions (including `NotImplementedError`) become `CipherResult(..., False)` —
a cipher method may raise, it degrades to a red error line instead of a traceback.

**Keyconsole** (`key` with no args): `_run_console()` is a readline loop with tab completion
(cipher names + `help`, `list`, `clear`, `version`, `update`, `remove`, `uninstall`, `exit`).
Console commands run **in-process**: `_run_single(shlex.split(input))` re-invokes `main()` with
`standalone_mode=False` and captures the last result — no subprocess per command.

**Layered chains** (`cc -e -t x -k 3 + b64 -e`): `_run_layered()` splits on `+`, feeds each
intermediate output into the next layer via `-t`, and appends `-e` to the final layer unless a
mode flag is present. Bare `+` is rejected with a usage error.

**`-ad` auto-decode**: `_identify_hash_types()` runs `hashid`, maps candidate labels through
`_AUTO_DECODE_MAP` to concrete ciphers (`md5`, `sha1`, `sha224`, `sha256`, `sha384`, `sha512`),
then brute-forces each until a match — first hit wins, so ambiguity (MD5 vs NTLM) is tried, not
guessed.

**Self-management**:

- `-u/--update` — fetches `version.txt` from GitHub, compares 4-segment versions, and on a
  newer tag clones into a temp dir and `pip install`s with `sys.executable`. Because
  `sys.executable` is the **venv** interpreter when run from the shim, updates stay inside
  `~/.0xPo11/venv`.
- `-rm/--remove` — `pip uninstall zeropo11`, then removes `~/.0xPo11/`, the
  `~/.local/bin/key` symlink, and the PATH line the installer appended to rc files.

### Output rules

`handle_output(result, output_path)` in `utils.py`:

| Condition | Behavior |
|-----------|----------|
| `success=False` | print `[✖] Failed:` + message |
| `-o` path ends in `.png` | **print only** (the cipher wrote the image itself) |
| `-o` any other path | write text to that file, print `[✓] File Output Successful` |
| `-o` with `cp -p/-g` | path is a **destination directory**, cipher already copied |

## Adding a Cipher

### 1. Create the module

One file, one class named `Cipher`. A complete minimal example (`src/zeropo11/ciphers/atbash.py`):

```python
"""Atbash cipher - maps a<->z, b<->y, ..."""
from __future__ import annotations

from zeropo11.ciphers.base import BaseCipher, CipherResult

HELP = """USAGE:
  key atbash [FLAGS] [OPTIONS]
FLAGS:
  -e, --encode  Encode input text
  -d, --decode  Decode input text
OPTIONS:
  -t, --text <text>  Input text
EXAMPLES:
  key atbash -e -t "hello"
  key atbash -d -t "svool"
"""


class Cipher(BaseCipher):
    name = "Atbash Cipher"
    command = "atbash"
    help_menu = HELP

    def _map(self, text: str) -> str:
        return "".join(
            chr(ord(c) + 25 - 2 * (ord(c.lower()) - ord("a"))) if c.isalpha() else c
            for c in text
        )

    def encode(self, args: object) -> CipherResult:
        text = getattr(args, "text", None)
        if not text:
            return CipherResult("Please provide -t <text>", False)
        return CipherResult(self._map(text), True)

    def decode(self, args: object) -> CipherResult:
        return self.encode(args)   # Atbash is symmetric
```

That is the whole registration step — the registry finds it by module import.

Follow these conventions:

- **Validate cheaply, fail softly.** Return `CipherResult("Please provide -t <text>", False)`
  rather than raising; `False` results print as a red `[✖]` line.
- **Read every input through `getattr` with a default.** No required kwargs.
- **Symmetric operations** can alias `decode = encode` (see `xor.py`).
- **Hash ciphers** should copy the `md5.py` shape: a module-level `_hash_func(data: bytes)`,
  `encode` prepending the optional salt, and `brute` accepting either `-w` (list) or `-r`
  (`start,end`) candidates. Also add the type to `hashid.RULES` and, if brute-able, to
  `_AUTO_DECODE_MAP` in `cli.py`.
- **Never print.** Return results; `handle_output` owns all console output.

### 2. Optional third-party backends

Import lazily inside the method so the module always imports (otherwise the registry silently
drops your cipher). Copy the `blowfish.py` pattern exactly:

```python
try:
    import blowfish
    ...
except ImportError:
    return CipherResult("Install blowfish: pip install blowfish", False)
except Exception as e:
    return CipherResult(f"Encryption failed: {e}", False)
```

Add the package to the `full` (and `crypto`, if applicable) extra in `pyproject.toml` — never to
the hard `dependencies` list.

### 3. Wire into docs (manual)

The discovery is automatic; the docs are not:

1. `README.md` → **Available Ciphers** table.
2. `config.py` → `HELP_MENU` cipher list + argument list (it is a hardcoded string; `key -h`
   output only matches reality if you edit it).
3. Optional: `hashid.RULES` / `_AUTO_DECODE_MAP` for hash ciphers.

### 4. Tests

Mirror `tests/test_encodings.py`: a local `_Args` helper, one test class per cipher,
`setup_method` instantiating it, and round-trip coverage.

```python
class _Args:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

class TestAtbash:
    def setup_method(self):
        self.cipher = Atbash()

    def test_encode(self):
        r = self.cipher.encode(_Args(text="hello"))
        assert r.output == "svool"
        assert r.success is True

    def test_roundtrip(self):
        encoded = self.cipher.encode(_Args(text="Hello World!"))
        assert self.cipher.decode(_Args(text=encoded.output)).output == "Hello World!"

    def test_no_text_fails(self):
        assert self.cipher.encode(_Args(text=None)).success is False
```

Run with `./run_tests.sh -k atbash`. New optional-dep ciphers must also pass under `--full`
(that installs the backend), and their missing-backend path should be asserted with
`success is False`.

## Testing

Everything goes through `./run_tests.sh` — it provisions `.venv/` from the `dev` extra on first
run, so no global pytest install is needed. `PYTHONPATH=src` is set for the pytest process, so
**source edits take effect without reinstalling the package**.

- `addopts = "-v --tb=short"` (in `pyproject.toml`) applies to every run.
- Test modules import ciphers as `from zeropo11.ciphers.xor import Cipher as Xor`.
- Optional-backend ciphers are exercised only under `--full`.

**Known gap:** the suite covers the cipher and registry layers (~36% of total statements) but
not `cli.py` — the click surface, `-ad`, `-u`/`-rm`, and the keyconsole loop have no automated
tests. The highest-value contribution is a `tests/test_cli.py` using pytest + click's
`CliRunner` (or subprocess against `python -m zeropo11`) covering: root help, per-cipher
`-h`, cipher-not-found, layered chains, and `-ad` against a temp wordlist.

## Build & Release

### Versioning (three places + one remote)

| Location | Value |
|----------|-------|
| `src/zeropo11/__init__.py` | `__version__` |
| `src/zeropo11/config.py` | `VERSION` (banner + console `version`) |
| `pyproject.toml` | `version` |
| `version.txt` (repo root) | served to GitHub clients; `-u` compares against this |

> ⚠️ These are currently **out of sync**: the package is `2.0.0` while `version.txt` says `3.0`.
> Any release must bump all four together, or `key --update` will report a phantom update and
> reinstall the same version.

### Wheel

```bash
python3 -m pip wheel . --no-deps -w dist/
# verify payload templates made it in:
python3 -c "import zipfile; print([n for n in zipfile.ZipFile('dist/zeropo11-*.whl').namelist() if 'payloads' in n])"
```

Payload templates ride along via `[tool.setuptools.package-data] zeropo11 = ["ciphers/templates/payloads/*"]`
— without it the wheel installs a broken `cp`.

### Install / update flow

```
install.sh → python3 -m venv ~/.0xPo11/venv
           → pip install .            (deps incl. click resolved by pip)
           → ln -sf .../venv/bin/key → ~/.local/bin/key
           → strip legacy `alias key=...` lines from .bashrc/.zshrc
           → append `export PATH="$HOME/.local/bin:$PATH"` if missing

resources/update.sh → git clone → bash install.sh (reuses the existing venv)

key --update → curl version.txt → git clone to temp → pip install with sys.executable
key --remove → pip uninstall → rm -rf ~/.0xPo11 → remove shim + rc PATH lines
```

User payloads live in `~/.0xPo11/resources/payloads` (seeded from the wheel by `cp` on first
use); the installer preserves them and user files in that dir take precedence over bundled
templates.

## Conventions & Gotchas

- **Args are duck-typed.** `getattr(args, "x", None)` everywhere; never construct `_Args` in a
  cipher, and never add required fields.
- **`-w` arrives as `list[str]`.** The CLI reads the wordlist file. Ciphers must guard
  `wordlist is not None` — an empty file yields `[]`, which is falsy but not `None` (this
  distinction caused a real crash; see the `if wordlist is not None:` guards in the hash
  ciphers).
- **`-o` means different things.** Output *file* for most ciphers, *directory* for
  `cp -p/-g`, a no-op path suffix `.png` telling `handle_output` the cipher already wrote the
  file, and a fully cipher-owned path for every `binary = True` cipher (`fe`).
- **Binary input never flows through the text pipeline.** `BaseCipher.binary = True` skips the
  CLI's `read_text()` pre-load; without it, encrypting a binary payload dies on
  `UnicodeDecodeError` before the cipher is even reached.
- **`-rm` is pre-scanned, not a click flag.** With `ignore_unknown_options` on, click parses
  `-rm` as `-r m`. `main()` inspects `sys.argv` for the exact token `"-rm"` before click runs.
  Any new root-level bare-dash flags need the same treatment.
- **`zip(..., strict=True)`** is the house style — it makes length mismatches loud instead of
  silently truncating (the original XOR bug). Note `xor.py` now cycles the key instead of
  zipping, so equal-length inputs and any-key-length inputs both work.
- **Help menus are static strings.** Nothing derives them from the option list; keep examples
  in `help_menu` runnable against the current code (several demos were caught wrong and fixed).
- **HELP_MENU is hand-maintained** in `config.py` — adding a cipher means editing it or
  `key -h` output will be stale.
- **`hashid` is a heuristic.** Length+charset+prefix only; MD5/NTLM/MySQL 4.1 share 32 chars
  and SHA256/Whirlpool share 64. `-ad` resolves ambiguity by trying, not guessing.
- **Legacy root code** (`main.py`, `ciphers/`, `mods/`) must import nothing new; it exists only
  so old docs/aliases don't 404.
- Python floor is **3.10** (`from __future__ import annotations` everywhere; no 3.12-only
  syntax), and the code targets the ruff rule set in `pyproject.toml` (`E F W I N UP B SIM`).
