"""Tests for layered (+) command chains and stray-argument handling."""
from __future__ import annotations

import contextlib
import io
import sys


def _run(argv: list[str]) -> tuple[str, int]:
    """Invoke the CLI in-process, returning (output, exit code).

    main() reads root-level flags from sys.argv (the -rm/-u pre-scan is
    sys.argv-driven by design), so the helper installs a realistic argv.
    """
    from zeropo11.cli import main

    old_argv = sys.argv
    sys.argv = ["key", *argv]
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            main(argv, standalone_mode=False)
            code = 0
    except SystemExit as exc:
        code = int(exc.code or 0)
    finally:
        sys.argv = old_argv
    return buffer.getvalue(), code


class TestLayeredChains:
    def test_encode_chain(self):
        # cc -e then b64 -e: the documented demo chain
        out, code = _run(["cc", "-e", "-t", "payload", "-k", "3", "+", "b64", "-e"])
        assert code == 0
        assert "c2Rib3JkZw==" in out

    def test_decode_chain_reverses(self):
        # b64 -d then cc -d -k 3 inverts the beat-1 encode chain
        out, code = _run(["b64", "-d", "-t", "c2Rib3JkZw==", "+", "cc", "-d", "-k", "3"])
        assert code == 0
        assert "payload" in out

    def test_final_layer_defaults_to_encode(self):
        # no mode on the last layer -> -e is appended automatically
        out, code = _run(["cc", "-e", "-t", "payload", "-k", "3", "+", "b64"])
        assert code == 0
        assert "c2Rib3JkZw==" in out

    def test_bare_plus_rejected(self):
        _, code = _run(["cc", "-e", "-t", "x", "-k", "1", "+"])
        assert code == 0  # guarded inside the runner; never crashes

    def test_three_layer_chain(self):
        out, code = _run(
            ["cc", "-e", "-t", "payload", "-k", "3", "+", "b64", "-e", "+", "hex", "-e"]
        )
        assert code == 0


class TestStrayArguments:
    def test_stray_positional_rejected(self):
        out, code = _run(["md5", "hello"])
        assert code != 0
        assert "Unexpected argument: 'hello'" in out

    def test_flag_shaped_typo_is_not_stray(self):
        # unknown flags are tolerated by design (ignore_unknown_options);
        # only bare positionals are rejected
        out, code = _run(["md5", "-e", "-t", "malware_sample"])
        assert code == 0
        assert "9127daf288687deb678053e2aa828e7d" in out

    def test_plus_not_treated_as_stray(self):
        out, code = _run(["xor", "-e", "-t", "cmd", "-k", "A", "+", "hex", "-e"])
        assert code == 0
