"""Click-based CLI for 0xPo11."""

from __future__ import annotations

import os
import re
import shlex
import sys

import click
from colorama import Fore

from zeropo11 import __version__
from zeropo11.ciphers import get_cipher, get_cipher_info, list_ciphers
from zeropo11.ciphers.base import CipherResult
from zeropo11.config import (
    BANNER,
    CMD_PREFIX,
    END,
    FAIL,
    HEADER,
    HELP_MENU,
    SUCCESS,
    VERSION,
)
from zeropo11.utils import handle_output, read_input_file, read_wordlist

# Module-level state shared by the console and layered runners.
_last_result: CipherResult | None = None
_quiet = False

# Maps hashid candidate labels to brute-able cipher commands.
_AUTO_DECODE_MAP = {
    "MD5": "md5",
    "NTLM": "md5",
    "SHA1": "sha1",
    "SHA224": "sha224",
    "SHA256": "sha256",
    "SHA384": "sha384",
    "SHA512": "sha512",
}


class _Args:
    """Namespace to pass arguments to cipher functions."""

    def __init__(self, **kwargs: object) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


def _build_args(
    text: str | None = None,
    key: str | None = None,
    salt: str | None = None,
    range_: str | None = None,
    wordlist: list[str] | None = None,
    alphabet: str | None = None,
    encryption_mode: str | None = None,
    exclude: str | None = None,
    iv: str | None = None,
    nonce: int | None = None,
    file_path: str | None = None,
    lingo: str = "en_US",
    words: bool = False,
    channel: int | None = None,
    input_image: str | None = None,
    payload: str | None = None,
    generate: str | None = None,
    output: str | None = None,
    iterations: int | None = None,
    host: str | None = None,
    port: int | None = None,
    timeout: int | None = None,
    local_in: bool = False,
    local_out: bool = False,
    template: str | None = None,
    deadline: str | None = None,
    drop_note: str | None = None,
    note_out: str | None = None,
    remove_source: bool = False,
) -> _Args:
    """Build an args namespace for cipher functions."""
    return _Args(
        text=text,
        key=key,
        salt=salt,
        range=range_,
        wordlist=wordlist,
        alphabet=alphabet,
        mode=encryption_mode,
        exclude=exclude,
        iv=iv,
        nonce=nonce,
        file=file_path,
        lingo=lingo,
        words=words,
        channel=channel,
        inputImage=input_image,
        payload=payload if payload is not None else generate,
        generate=generate,
        output=output,
        iterations=iterations,
        host=host,
        port=port,
        timeout=timeout,
        local_in=local_in,
        local_out=local_out,
        template=template,
        deadline=deadline,
        drop_note=drop_note,
        note_out=note_out,
        remove_source=remove_source,
    )


def _dispatch(
    cipher_obj: object,
    args: _Args,
    mode: str | None,
    payload: str | None,
    generate: str | None,
) -> CipherResult | None:
    """Dispatch to the cipher's payload/encode/decode/brute handler."""
    payload_or_generate = payload or generate
    if payload_or_generate:
        payload_fn = getattr(cipher_obj, "payload", None)
        if payload_fn is None:
            return CipherResult(
                f"{cipher_obj.name} does not support payload generation", False
            )
        try:
            return payload_fn(args)
        except NotImplementedError as e:
            return CipherResult(str(e), False)
        except Exception as e:
            return CipherResult(f"Error: {e}", False)

    func = None
    if mode == "encode":
        func = cipher_obj.encode
    elif mode == "decode":
        func = cipher_obj.decode
    elif mode == "brute":
        func = cipher_obj.brute

    if func is None:
        click.echo(f"{Fore.CYAN}{cipher_obj.help_menu}{END}")
        return None

    try:
        return func(args)
    except NotImplementedError as e:
        return CipherResult(str(e), False)
    except Exception as e:
        return CipherResult(f"Error: {e}", False)


def _parse_version(version_text: str) -> tuple[int, int, int, int]:
    """Parse a version string into a padded 4-segment integer tuple."""
    segments = re.findall(r"\d+", version_text)[:4]
    segments += ["0"] * (4 - len(segments))
    return tuple(int(segment) for segment in segments)


def _do_update() -> None:
    """Check for and apply updates."""
    import subprocess
    from pathlib import Path

    print("\n[*] Checking for updates...")

    current = VERSION
    version_file = Path.home() / ".0xPo11" / "version.txt"
    if version_file.exists():
        try:
            current = version_file.read_text().strip()
        except OSError:
            current = VERSION

    try:
        result = subprocess.run(
            [
                "curl",
                "-s",
                "https://raw.githubusercontent.com/0xClumzzy/0xPo11/main/version.txt",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except subprocess.TimeoutExpired as exc:
        print(f"[✖] Update check failed: {exc}")
        return
    except FileNotFoundError:
        print("[✖] Update check failed: curl not found")
        return

    latest_text = result.stdout.strip()
    if not latest_text:
        print("[✖] Could not fetch latest version")
        return

    if _parse_version(latest_text) <= _parse_version(current):
        print(f"{SUCCESS}[+] 0xPo11 already up to date{END}")
        return

    print("\n[+] Update found")
    click.echo(f"{CMD_PREFIX}Update 0xPo11? [y/n]")
    try:
        option = input(HEADER).strip()
    except (EOFError, KeyboardInterrupt):
        print("\nExiting...")
        return

    if option == "y":
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            clone = subprocess.run(
                ["git", "clone", "--quiet", "https://github.com/0xClumzzy/0xPo11", tmp],
                capture_output=True,
                text=True,
            )
            if clone.returncode != 0:
                print("[✖] Update failed: could not clone latest 0xPo11")
                return
            install = subprocess.run([sys.executable, "-m", "pip", "install", tmp])
            if install.returncode != 0:
                print("[✖] Update failed: pip install error")
                return
            print(f"{SUCCESS}[+] 0xPo11 updated to the latest version{END}")


def _do_remove() -> None:
    """Uninstall 0xPo11."""
    import shutil
    import subprocess
    from pathlib import Path

    click.echo(f"\n{CMD_PREFIX}Are you sure you want to remove 0xPo11? [y/n]")
    try:
        option = input(HEADER).strip()
    except (EOFError, KeyboardInterrupt):
        print("\nExiting...")
        return
    if option != "y":
        return

    result = subprocess.run(
        [sys.executable, "-m", "pip", "uninstall", "-y", "zeropo11"]
    )
    if result.returncode != 0:
        print("[✖] Failed to uninstall package")
        return

    target = Path.home() / ".0xPo11"
    if target.exists():
        shutil.rmtree(target)

    # Remove the `key` shim install.sh symlinks into ~/.local/bin (only if it
    # is a symlink we created - never touch a user's own file there)
    shim = Path.home() / ".local" / "bin" / "key"
    try:
        if shim.is_symlink():
            shim.unlink()
            print(f"{SUCCESS}[+] Removed '{shim}' symlink{END}")
    except OSError:
        pass

    # Strip the PATH export block install.sh added to shell rc files
    marker = "# 0xPo11 (added by install.sh)"
    path_line = 'export PATH="$HOME/.local/bin:$PATH"'
    for name in (".bashrc", ".zshrc"):
        rc = Path.home() / name
        try:
            if not rc.is_file():
                continue
            lines = rc.read_text(encoding="utf-8", errors="ignore").splitlines(keepends=True)
            if not any(line.strip() == marker for line in lines):
                continue
            rc.write_text(
                "".join(
                    line
                    for line in lines
                    if line.strip() not in (marker, path_line)
                ),
                encoding="utf-8",
            )
            print(f"{SUCCESS}[+] Cleaned PATH changes from {rc}{END}")
        except OSError:
            pass

    print(f"{SUCCESS}[+] 0xPo11 removed successfully{END}")


def _identify_hash_types(text: str) -> list[str]:
    """Use the hashid cipher to identify brute-able hash types."""
    identification = get_cipher("hashid").encode(_Args(text=text))
    if not identification.success:
        return []

    found: list[str] = []
    for line in identification.output.splitlines():
        label = line.strip().removeprefix("- ")
        cmd = _AUTO_DECODE_MAP.get(label)
        if cmd is None:
            for key, mapped in _AUTO_DECODE_MAP.items():
                if key in line:
                    cmd = mapped
                    break
        if cmd is not None and cmd not in found:
            found.append(cmd)
    return found


def _run_auto_decode(
    text: str | None,
    input_file: str | None,
    wordlist: str | None,
    salt: str | None,
) -> None:
    """Auto-detect hash type and brute-force it against a wordlist."""
    if not text and input_file:
        try:
            text = read_input_file(input_file)
        except OSError as exc:
            click.echo(f"{FAIL}[✖] {exc}{END}")
            return
    if not text:
        click.echo(f"{FAIL}[✖] Auto-decode requires -t <hash>{END}")
        return
    if not wordlist:
        click.echo(f"{FAIL}[✖] Auto-decode requires -w <wordlist>{END}")
        return
    try:
        wordlist_data = read_wordlist(wordlist)
    except OSError as exc:
        click.echo(f"{FAIL}[✖] {exc}{END}")
        return
    if not wordlist_data:
        click.echo(f"{FAIL}[✖] Wordlist is empty{END}")
        return

    identified = _identify_hash_types(text or "")
    if not identified:
        click.echo(f"{FAIL}[✖] No brute-able hash type identified{END}")
        return

    for cmd in identified:
        cipher_obj = get_cipher(cmd)
        result = cipher_obj.brute(
            _Args(text=text, wordlist=wordlist_data, salt=salt or "", range=None)
        )
        if result.success:
            handle_output(result)
            return

    click.echo(
        f"{FAIL}[✖] No match found in wordlist for any identified hash type{END}"
    )


def _run_single(parts: list[str], quiet: bool = False) -> CipherResult | None:
    """Run the CLI once, returning the last cipher result."""
    global _last_result, _quiet
    _last_result = None
    _quiet = quiet
    try:
        main(parts, standalone_mode=False)
    except SystemExit:
        pass
    except click.exceptions.UsageError as exc:
        if not quiet:
            click.echo(f"{FAIL}[✖] {exc}{END}")
    finally:
        _quiet = False
    return _last_result


def setup_completion() -> None:
    """Enable tab-completion for the keyconsole (readline)."""
    try:
        import readline
    except ImportError:
        return

    words = list_ciphers() + [
        "help",
        "list",
        "clear",
        "version",
        "update",
        "remove",
        "uninstall",
        "exit",
        "quit",
    ]

    def _completer(text: str, state: int) -> str | None:
        matches = [word for word in words if word.startswith(text)]
        return matches[state] if state < len(matches) else None

    readline.set_completer(_completer)
    readline.parse_and_bind("tab: complete")


def _run_layered(cmd_str: str) -> CipherResult | None:
    """Run a layered command chain, e.g. 'cc -e -t hi -k 3 + b64 -e'."""
    stripped = cmd_str.strip()
    if not re.search(r"[^\s+]", stripped):
        click.echo(f"{FAIL}[✖] Bare '+' is not a valid layered command{END}")
        return None

    layers = re.split(r"\s+\+\s*|\s*\+\s+", stripped)
    previous: str | None = None
    result: CipherResult | None = None

    for n, layer in enumerate(layers, start=1):
        if not layer.strip():
            click.echo(f"{FAIL}[✖] Bare '+' is not a valid layered command{END}")
            return None

        parts = shlex.split(layer)
        if previous is not None:
            parts[1:1] = ["-t", previous]
        if n == len(layers) and not re.search(r"(^|\s)-[edb](\s|$)", layer):
            parts.append("-e")

        click.echo(f"\n[{Fore.CYAN}*] Layer {n}: {layer}{END}")
        result = _run_single(parts, quiet=(n < len(layers)))
        if result is None or not result[1]:
            return None
        previous = result[0]

    return result


def _run_console() -> None:
    """Run the interactive Keyconsole."""
    print(BANNER)
    print(f'{CMD_PREFIX}Type "help" for help menu :')
    setup_completion()

    while True:
        try:
            user_input = input(HEADER).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break

        if not user_input:
            continue

        if user_input == "help":
            print(HELP_MENU)
        elif user_input.startswith("help "):
            cmd = user_input[len("help "):].strip()
            try:
                print(f"{Fore.CYAN}{get_cipher(cmd).help_menu}{END}")
            except KeyError:
                print(f"{FAIL}[✖] Cipher '{cmd}' not found.{END}")
        elif user_input == "list":
            for command, name in get_cipher_info():
                print(f"    {command:<12} {name}")
        elif user_input == "clear":
            os.system("clear")
        elif user_input == "version":
            print(f"0xPo11 v{__version__}")
        elif user_input in ("update",):
            _do_update()
        elif user_input in ("uninstall", "remove"):
            _do_remove()
        elif user_input in ("exit", "quit"):
            break
        elif "+" in user_input:
            _run_layered(user_input)
        else:
            _run_single(shlex.split(user_input))


@click.command(
    name="main",
    add_help_option=False,
    context_settings={
        "ignore_unknown_options": True,
        "allow_extra_args": True,
    },
)
@click.argument("cipher", required=False)
@click.option("-e", "--encode", "mode", flag_value="encode", help="Encrypt/encode input")
@click.option("-d", "--decode", "mode", flag_value="decode", help="Decrypt/decode input")
@click.option("-b", "--brute", "mode", flag_value="brute", help="Brute-force input")
@click.option("-t", "--text", help="Input text")
@click.option("-i", "--input-file", "input_file", help="Input file path")
@click.option("-o", "--output", help="Output file path")
@click.option("-k", "--key", help="Encryption key")
@click.option("-s", "--salt", help="Hash salt")
@click.option("-r", "--range", "range_", help="Brute-force range (start,end)")
@click.option("-w", "--wordlist", help="Wordlist file for brute-forcing")
@click.option("-a", "--alphabet", help="Alphabet for brute-force")
@click.option("-ex", "--exclude", help="Chars to exclude from brute-force")
@click.option("-md", "--mode", "mode_mode", help="Alternate mode selector (legacy)")
@click.option("--iv", "iv", help="Initialization vector")
@click.option("-nc", "--nonce", "nonce", type=int, help="Nonce value")
@click.option("-lingo", "--lingo", "lingo", default="en_US", help="Language for diceware")
@click.option("-words", "--words", "words", is_flag=True, help="Show words in diceware output")
@click.option("-c", "--channel", "channel", help="Pixel channel (0/1/2)")
@click.option("-g", "--generate", help="Generate a payload template")
@click.option("-p", "--payload", help="Use a payload template")
@click.option("-u", "--update", "--upgrade", "do_update", is_flag=True, help="Check for updates")
@click.option("--remove", "--uninstall", "do_remove", is_flag=True, help="Uninstall 0xPo11")
@click.option("-ad", "--auto-decode", "auto_decode", is_flag=True, help="Auto-detect and brute hash")
@click.option(
    "-it", "--iterations", "iterations", type=int, help="PBKDF2 iterations (file encryption)"
)
@click.option("--host", "host", help="Remote host for file encryption (user@server)")
@click.option("--port", "port", type=int, help="SSH port (default: 22)")
@click.option("--timeout", "timeout", type=int, help="SSH timeout in seconds (default: 120)")
@click.option("--local-in", "local_in", is_flag=True, help="Input path is local even with --host")
@click.option(
    "--local-out", "local_out", is_flag=True, help="Output path is local even with --host"
)
@click.option("--drop-note", "drop_note", help="After encrypting, drop ransom note (template: generic/polite/press)")
@click.option("--note-out", "note_out", help="Where to write the dropped ransom note (default: source parent / NOTE.txt)")
@click.option("--remove-source", "remove_source", is_flag=True, help="After a successful encryption, delete the original file (encrypt only)")
@click.option("-tm", "--template", "template", help="Ransom note voice (rn)")
@click.option("-dl", "--deadline", "deadline", help="Ransom note deadline in hours (rn)")
@click.option("-ii", "--inputImage", "input_image", help="Input image path")
@click.version_option(
    __version__,
    "-v",
    "--version",
    prog_name="0xPo11",
    expose_value=False,
)
@click.pass_context
def main(
    ctx: click.Context,
    cipher: str | None,
    mode: str | None,
    mode_mode: str | None,
    text: str | None,
    input_file: str | None,
    output: str | None,
    key: str | None,
    salt: str | None,
    range_: str | None,
    wordlist: str | None,
    alphabet: str | None,
    exclude: str | None,
    iv: str | None,
    nonce: int | None,
    lingo: str,
    words: bool,
    channel: int | None,
    generate: str | None,
    payload: str | None,
    input_image: str | None,
    do_update: bool,
    do_remove: bool,
    auto_decode: bool,
    iterations: int | None,
    host: str | None,
    port: int | None,
    timeout: int | None,
    local_in: bool,
    local_out: bool,
    template: str | None,
    deadline: str | None,
    drop_note: str | None,
    note_out: str | None,
    remove_source: bool,
) -> None:
    """0xPo11 - Multi-format encryption toolkit."""
    global _last_result

    argv = sys.argv[1:]
    # `-rm` is not a declared flag (click parses it as `-r m`); pre-scan only.
    if any(arg == "-rm" for arg in argv):
        do_remove = True

    # String fallbacks for flags that may surface as extra/positional args.
    if any(arg in ("-u", "--update", "--upgrade") for arg in argv):
        do_update = True
    if any(arg in ("--remove", "--uninstall", "-rm") for arg in argv):
        do_remove = True

    if cipher in ("-h", "--help"):
        click.echo(HELP_MENU)
        return

    if do_remove:
        _do_remove()
        return

    if do_update:
        _do_update()
        return

    if auto_decode:
        _run_auto_decode(text=text, input_file=input_file, wordlist=wordlist, salt=salt)
        return

    if cipher is None:
        if len(sys.argv) <= 1:
            _run_console()
        else:
            click.echo(HELP_MENU)
        return

    try:
        cipher_obj = get_cipher(cipher)
    except KeyError:
        click.echo(
            f"{FAIL}\n[✖] Cipher '{cipher}' not found.\n"
            f"Try 'key --help' to see all ciphers.{END}"
        )
        sys.exit(1)

    # binary ciphers (e.g. file encryption) read the file themselves
    is_binary = getattr(cipher_obj, "binary", False)

    if "-h" in ctx.args or "--help" in ctx.args:
        click.echo(f"{Fore.CYAN}{cipher_obj.help_menu}{END}")
        return

    # Layered chains (`cipher -e ... + cipher -e ...`) are re-quoted from the
    # original argv and handed to the layered runner, same as the keyconsole.
    if "+" in (ctx.args or []):
        _run_layered(" ".join(shlex.quote(arg) for arg in sys.argv[1:]))
        return

    # a bare path after a flag means a typo (e.g. `--local-out <path>` where
    # `-o <path>` was meant); click would otherwise swallow it silently.
    # `+` and cipher names are legitimate extras: they are the layers of a
    # `cipher -e ... + cipher -e ...` chain.
    from zeropo11.ciphers import list_ciphers

    allowed = {"+"} | set(list_ciphers())
    stray = [a for a in (ctx.args or []) if not a.startswith("-") and a not in allowed]
    if stray:
        click.echo(
            f"{FAIL}[✖] Unexpected argument: '{stray[0]}'{END}\n"
            f"{CMD_PREFIX}Paths belong in flags, e.g. -o <path>. "
            f"Run 'key {cipher} -h' for usage.{END}"
        )
        sys.exit(1)

    if input_file and not is_binary:
        try:
            text = read_input_file(input_file)
        except OSError as exc:
            click.echo(f"{FAIL}[✖] Could not read input file: {exc}{END}")
            sys.exit(1)

    wordlist_data = None
    if wordlist:
        try:
            wordlist_data = read_wordlist(wordlist)
        except OSError as exc:
            click.echo(f"{FAIL}[✖] Could not read wordlist: {exc}{END}")
            sys.exit(1)

    args = _build_args(
        text=text,
        key=key,
        salt=salt,
        range_=range_,
        wordlist=wordlist_data,
        alphabet=alphabet,
        encryption_mode=mode_mode,
        exclude=exclude,
        iv=iv,
        nonce=nonce,
        file_path=input_file,
        lingo=lingo,
        words=words,
        channel=channel,
        input_image=input_image,
        payload=payload,
        generate=generate,
        output=output,
        iterations=iterations,
        host=host,
        port=port,
        timeout=timeout,
        local_in=local_in,
        local_out=local_out,
        template=template,
        deadline=deadline,
        drop_note=drop_note,
        note_out=note_out,
        remove_source=remove_source,
    )

    _last_result = _dispatch(cipher_obj, args, mode or mode_mode, payload, generate)
    if _last_result is not None and not _quiet:
        if payload or generate:
            # For payload copies, -o is the destination *directory*; the cipher
            # already wrote the file(s), so only display the result message.
            handle_output(_last_result)
        elif is_binary:
            # Binary ciphers (file encryption) own their output files.
            handle_output(_last_result)
        else:
            handle_output(_last_result, output)


if __name__ == "__main__":
    main()
