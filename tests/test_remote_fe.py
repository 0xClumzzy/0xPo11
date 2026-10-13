"""Tests for the remote (ssh streaming) file encryption transport."""
from __future__ import annotations

import io
import shlex
import subprocess

from zeropo11.ciphers.fe import Cipher as Fe

PASSWORD = "correct horse battery staple"
ITERATIONS = 1000
HOST = "deploy@10.0.0.5"


class _Args:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class _FakeStdin:
    def __init__(self, on_write=None):
        self._on_write = on_write
        self.closed = False

    def write(self, data: bytes) -> None:
        if self._on_write is not None:
            self._on_write(data)

    def close(self) -> None:
        self.closed = True


class _FakeStdout:
    def __init__(self, data: bytes):
        self._buf = io.BytesIO(data)
        self.closed = False

    def read(self, size: int = -1) -> bytes:
        return self._buf.read(size)

    def close(self) -> None:
        self.closed = True


class _FakeProc:
    def __init__(self, cmd, *, stdout=b"", returncode=0, stderr="", on_write=None, wait_exc=None):
        self.args = cmd
        self.returncode = returncode
        self._stderr = stderr
        self._wait_exc = wait_exc
        self.stdin = _FakeStdin(on_write)
        self.stdout = _FakeStdout(stdout)
        self.killed = False
        self.waited = False

    def wait(self, timeout=None):
        first_call = not self.waited
        self.waited = True
        if first_call and self._wait_exc is not None:
            raise self._wait_exc
        return self.returncode

    def kill(self):
        self.killed = True


def install_fake_ssh(monkeypatch, remote_files, *, returncode=0, stderr="", wait_exc=None):
    """Replace _spawn_ssh with an in-memory fake; returns the write log."""
    written: dict[str, bytearray] = {}
    spawned: list[_FakeProc] = []

    def fake_spawn(cmd, timeout):
        remote_cmd = cmd[-1]
        if remote_cmd.startswith("cat >"):
            path = shlex.split(remote_cmd[len("cat >") :].strip())[0]
            buf = bytearray()
            written[path] = buf
            proc = _FakeProc(
                cmd,
                returncode=returncode,
                stderr=stderr,
                on_write=buf.extend,
                wait_exc=wait_exc,
            )
        else:
            path = shlex.split(remote_cmd)[1]
            proc = _FakeProc(
                cmd,
                stdout=remote_files.get(path, b""),
                returncode=returncode,
                stderr=stderr,
                wait_exc=wait_exc,
            )
        spawned.append(proc)
        return proc, lambda: stderr

    monkeypatch.setattr("zeropo11.ciphers.fe._spawn_ssh", fake_spawn)
    return written, spawned


class TestRemoteEncrypt:
    def setup_method(self):
        self.cipher = Fe()

    def test_read_command_quoted(self, monkeypatch):
        _, spawned = install_fake_ssh(monkeypatch, {})
        self.cipher.encode(
            _Args(key=PASSWORD, host=HOST, file="/data/db dump;.dump", iterations=ITERATIONS)
        )
        assert spawned[0].args[-1] == f"cat {shlex.quote('/data/db dump;.dump')}"

    def test_read_command_uses_port(self, monkeypatch):
        _, spawned = install_fake_ssh(monkeypatch, {})
        self.cipher.encode(
            _Args(
                key=PASSWORD, host=HOST, port=2222, file="/etc/shadow", iterations=ITERATIONS
            )
        )
        assert spawned[0].args == ["ssh", "-p", "2222", HOST, "cat /etc/shadow"]

    def test_write_command_quoted(self, monkeypatch):
        written, _ = install_fake_ssh(monkeypatch, {})
        self.cipher.encode(
            _Args(
                key=PASSWORD, host=HOST, file="/data/x.bin", output="/remote/out put.enc",
                iterations=ITERATIONS,
            )
        )
        # the sink path was quoted, and the ciphertext landed in the fake sink
        assert list(written) == ["/remote/out put.enc"]
        assert bytes(written["/remote/out put.enc"]).startswith(b"0xFE")

    def test_remote_encrypt_roundtrip_local(self, monkeypatch, tmp_path):
        data = b"remote plaintext payload" * 10
        install_fake_ssh(monkeypatch, {"/data/secret.bin": data})
        out = tmp_path / "secret.bin.enc"
        r = self.cipher.encode(
            _Args(
                key=PASSWORD, host=HOST, file="/data/secret.bin",
                output=str(out), local_out=True, iterations=ITERATIONS,
            )
        )
        assert r.success is True
        blob = out.read_bytes()
        assert blob.startswith(b"0xFE")
        # and the local copy decrypts back to the original remote bytes
        d = self.cipher.decode(
            _Args(key=PASSWORD, file=str(out), output=str(tmp_path / "restored"))
        )
        assert d.success is True
        assert (tmp_path / "restored").read_bytes() == data

    def test_remote_pipe_mode(self, monkeypatch):
        # remote -> remote: nothing touches the local disk
        data = bytes(range(256)) * 4  # spans multiple keystream blocks
        written_enc, _ = install_fake_ssh(monkeypatch, {"/data/blob.bin": data})
        r = self.cipher.encode(
            _Args(key=PASSWORD, host=HOST, file="/data/blob.bin", iterations=ITERATIONS)
        )
        assert r.success is True
        # default naming stays on the remote side
        assert "/data/blob.bin.enc" in written_enc
        blob = bytes(written_enc["/data/blob.bin.enc"])

        # feed that blob back over ssh as a remote source, restore remotely
        written_dec, _ = install_fake_ssh(monkeypatch, {"/data/blob.bin.enc": blob})
        d = self.cipher.decode(
            _Args(key=PASSWORD, host=HOST, file="/data/blob.bin.enc", iterations=ITERATIONS)
        )
        assert d.success is True
        # default restore naming strips .enc, still remote
        assert bytes(written_dec["/data/blob.bin"]) == data

    def test_ssh_failure_surfaced(self, monkeypatch):
        install_fake_ssh(
            monkeypatch, {}, returncode=1, stderr="cat: /nope.bin: No such file or directory"
        )
        r = self.cipher.encode(
            _Args(key=PASSWORD, host=HOST, file="/nope.bin", iterations=ITERATIONS)
        )
        assert r.success is False
        assert "SSH operation failed" in r.output
        assert "No such file or directory" in r.output

    def test_ssh_timeout_killed(self, monkeypatch):
        install_fake_ssh(
            monkeypatch,
            {},
            wait_exc=subprocess.TimeoutExpired(cmd="ssh", timeout=1),
        )
        r = self.cipher.encode(
            _Args(key=PASSWORD, host=HOST, file="/x", iterations=ITERATIONS)
        )
        assert r.success is False
        assert "timed out" in r.output

    def test_host_rejects_inline_text(self):
        r = self.cipher.encode(
            _Args(key=PASSWORD, host=HOST, text="secret", iterations=ITERATIONS)
        )
        assert r.success is False
        assert "--host" in r.output

    def test_all_local_with_host_refused(self, tmp_path):
        src = tmp_path / "x.bin"
        src.write_bytes(b"data")
        r = self.cipher.encode(
            _Args(
                key=PASSWORD, host=HOST, file=str(src), output=str(tmp_path / "y.enc"),
                local_in=True, local_out=True, iterations=ITERATIONS,
            )
        )
        assert r.success is False
        assert "drop --host" in r.output


class TestRemoteDecrypt:
    def setup_method(self):
        self.cipher = Fe()

    def test_remote_write_of_plaintext(self, monkeypatch):
        # encrypt locally, then "push" the plaintext to a remote sink
        encoded = self.cipher.encode(_Args(key=PASSWORD, text="push me", iterations=ITERATIONS))
        written, _ = install_fake_ssh(monkeypatch, {})
        r = self.cipher.decode(
            _Args(key=PASSWORD, host=HOST, text=encoded.output, output="/remote/pushed.txt",
                  local_in=True)
        )
        assert r.success is True
        assert bytes(written["/remote/pushed.txt"]) == b"push me"

    def test_write_failure_surfaced(self, monkeypatch):
        encoded = self.cipher.encode(_Args(key=PASSWORD, text="x", iterations=ITERATIONS))
        install_fake_ssh(monkeypatch, {}, returncode=1, stderr="cat: permission denied")
        r = self.cipher.decode(
            _Args(key=PASSWORD, host=HOST, text=encoded.output, output="/root/x",
                  local_in=True)
        )
        assert r.success is False
        assert "permission denied" in r.output


def os_urandom_like() -> bytes:
    return bytes(range(256)) * 4

