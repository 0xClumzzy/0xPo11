"""Click-based CLI for 0xPo11."""

from __future__ import annotations

import sys

import click

from zeropo11 import __version__
from zeropo11.ciphers import get_cipher
from zeropo11.config import BANNER, CMD_PREFIX, END, FAIL, HELP_MENU, VERSION
from zeropo11.utils import handle_output, read_input_file, read_wordlist


@click.group(invoke_without_command=True)
@click.argument("cipher", required=False)
@click.option("-e", "--encode", "mode", flag_value="encode", help="Encrypt/encode input")
@click.option("-d", "--decode", "mode", flag_value="decode", help="Decrypt/decode input")
@click.option("-b", "--brute", "mode", flag_value="brute", help="Brute-force input")
@click.option("-t", "--text", help="Input text")
@click.option("-i", "--input-file", help="Input file path")
@click.option("-o", "--output", help="Output file path")
@click.option("-k", "--key", help="Encryption key")
@click.option("-s", "--salt", help="Hash salt")
@click.option("-r", "--range", "range_", help="Brute-force range (start,end)")
@click.option("-w", "--wordlist", help="Wordlist file for brute-force")
@click.option("-a", "--alphabet", help="Custom alphabet")
@click.option("-md", "--mode", help="Encryption mode (e.g. for blowfish)")
@click.option("-ex", "--exclude", help="Exclude characters")
@click.option("--iv", help="Initialization vector")
@click.option("-nc", "--nonce", type=int, help="Nonce value")
@click.option("-f", "--file", "file_path", help="File path for static encryption")
@click.option("--lingo", default="en_US", help="Language for word detection")
@click.option("--words", is_flag=True, help="Filter words from output")
@click.version_option(__version__, prog_name="0xPo11")
@click.pass_context
def main(
    ctx: click.Context,
    cipher: str | None,
    mode: str | None,
    text: str | None,
    input_file: str | None,
    output: str | None,
    key: str | None,
    salt: str | None,
    range_: str | None,
    wordlist: str | None,
    alphabet: str | None,
    mode_mode: str | None,
    exclude: str | None,
    iv: str | None,
    nonce: int | None,
    file_path: str | None,
    lingo: str,
    words: bool,
) -> None:
    """0xPo11 - A Cryptographic Suite by CosmodiumCS.

    Run without arguments to enter the interactive console.
    """
    if ctx.invoked_subcommand is not None:
        return

    # No cipher specified - show help or enter console
    if cipher is None:
        if len(sys.argv) == 1:
            _run_console()
        else:
            click.echo(HELP_MENU)
        return

    # Check for global flags
    if cipher in ("-h", "--help"):
        click.echo(HELP_MENU)
        return

    if cipher in ("-u", "--update"):
        _do_update()
        return

    if cipher in ("-rm", "--remove", "--uninstall"):
        _do_remove()
        return

    # Try to load the cipher module
    try:
        cipher_obj = get_cipher(cipher)
    except KeyError:
        click.echo(
            f"{FAIL}\n[✖] Cipher '{cipher}' not found.\n"
            f"Try 'key --help' to see all ciphers.{END}"
        )
        sys.exit(1)

    # Read input file if provided
    if input_file:
        text = read_input_file(input_file)

    # Read wordlist if provided
    wordlist_data = None
    if wordlist:
        wordlist_data = read_wordlist(wordlist)

    # Build args namespace for cipher compatibility
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
        file_path=file_path,
        lingo=lingo,
        words=words,
    )

    # Dispatch to cipher
    func = None
    if mode == "encode":
        func = cipher_obj.encode
    elif mode == "decode":
        func = cipher_obj.decode
    elif mode == "brute":
        func = cipher_obj.brute

    if func is None:
        click.echo(f"CYAN{cipher_obj.help_menu}{END}")
        return

    try:
        result = func(args)
        handle_output(result, output)
    except NotImplementedError as e:
        click.echo(f"{FAIL}[✖] {e}{END}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"{FAIL}[✖] Error: {e}{END}")
        sys.exit(1)


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
    )


def _run_console() -> None:
    """Run the interactive Keyconsole."""
    print(BANNER)
    print(f'{CMD_PREFIX}Type "help" for help menu :')

    while True:
        try:
            user_input = input("HEADER").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break

        if not user_input:
            continue

        if user_input == "help":
            print(HELP_MENU)
        elif user_input == "version":
            print(f"0xPo11 v{VERSION}")
        elif user_input in ("exit", "quit"):
            break
        elif user_input in ("update",):
            _do_update()
        elif user_input in ("uninstall", "remove"):
            _do_remove()
        else:
            # Parse the input as if it were CLI args
            parts = user_input.split()
            try:
                main(parts, standalone_mode=False)
            except SystemExit:
                pass
            except click.exceptions.UsageError as e:
                print(f"{FAIL}[✖] {e}{END}")


def _do_update() -> None:
    """Check for and apply updates."""
    import subprocess
    from pathlib import Path

    print("\n[*] Checking for updates...")

    try:
        result = subprocess.run(
            ["curl", "-s", "https://raw.githubusercontent.com/CosmodiumCS/SkeletonKey/main/version.txt"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        latest_text = result.stdout.strip()
        if not latest_text:
            print("[!] Could not fetch latest version")
            return

        latest_version = float(latest_text)
        current_version = float(VERSION)

        if latest_version > current_version:
            print("\n[+] Update found")
            click.echo(f"{CMD_PREFIX}Update 0xPo11? [y/n]")
            option = input("HEADER").strip()
            if option == "y":
                # Use subprocess instead of os.system
                subprocess.run(["bash", str(Path.home() / ".0xPo11/resources/update.sh")])
        else:
            print("\n[+] 0xPo11 already up to date")
    except (ValueError, subprocess.TimeoutExpired) as e:
        print(f"[!] Update check failed: {e}")


def _do_remove() -> None:
    """Uninstall 0xPo11."""
    import shutil
    from pathlib import Path

    click.echo(f"\n{CMD_PREFIX}Are you sure you want to remove 0xPo11? [y/n]")
    option = input("HEADER").strip()
    if option == "y":
        target = Path.home() / ".0xPo11"
        if target.exists():
            shutil.rmtree(target)
            print("[+] 0xPo11 removed successfully")
        else:
            print("[!] 0xPo11 installation not found")


if __name__ == "__main__":
    main()
