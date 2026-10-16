"""Tests for the file encryption cipher (fe)."""
from __future__ import annotations

import os
import struct

from zeropo11.ciphers.fe import (
    BLOCK_SIZE,
    CHUNK_SIZE,
    DEFAULT_ITERATIONS,
    MAGIC,
    NONCE_SIZE,
    SALT_SIZE,
    _crypt_chunk,
    _keystream_block,
)
from zeropo11.ciphers.fe import (
    Cipher as Fe,
)

PASSWORD = "correct horse battery staple"
ITERATIONS = 1000  # keep tests fast


class _Args:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestFileEncryption:
    def setup_method(self):
        self.cipher = Fe()

    # ------------------------------------------------------------------ helpers

    def _encrypt(self, tmp_path, name, data, **kwargs):
        src = tmp_path / name
        src.write_bytes(data)
        out = tmp_path / f"{name}.enc"
        r = self.cipher.encode(
            _Args(key=PASSWORD, file=str(src), output=str(out), iterations=ITERATIONS, **kwargs)
        )
        assert r.success is True
        return src, out

    # ------------------------------------------------------------------ basics

    def test_encrypt_produces_header_and_mac(self, tmp_path):
        _, out = self._encrypt(tmp_path, "payload.bin", b"secret payload")
        blob = out.read_bytes()
        assert blob.startswith(MAGIC)
        assert struct.unpack(">I", blob[6:10])[0] == ITERATIONS
        # header + ciphertext (same length) + 32-byte mac
        assert len(blob) == 42 + len(b"secret payload") + 32
        # salt and nonce are non-zero
        salt = blob[10 : 10 + SALT_SIZE]
        nonce = blob[10 + SALT_SIZE : 10 + SALT_SIZE + NONCE_SIZE]
        assert salt.strip(b"\x00")
        assert nonce.strip(b"\x00")

    def test_roundtrip_small_file(self, tmp_path):
        data = b"attack at dawn"
        src, out = self._encrypt(tmp_path, "note.txt", data)
        dest = tmp_path / "note.txt.dec"
        r = self.cipher.decode(
            _Args(key=PASSWORD, file=str(out), output=str(dest), iterations=ITERATIONS)
        )
        assert r.success is True
        assert dest.read_bytes() == data

    def test_roundtrip_binary(self, tmp_path):
        data = os.urandom(4096)
        src, out = self._encrypt(tmp_path, "blob.bin", data)
        dest = tmp_path / "blob.bin.dec"
        r = self.cipher.decode(
            _Args(key=PASSWORD, file=str(out), output=str(dest), iterations=ITERATIONS)
        )
        assert r.success is True
        assert dest.read_bytes() == data

    def test_roundtrip_empty_file(self, tmp_path):
        src, out = self._encrypt(tmp_path, "empty.bin", b"")
        dest = tmp_path / "empty.out"
        r = self.cipher.decode(
            _Args(key=PASSWORD, file=str(out), output=str(dest), iterations=ITERATIONS)
        )
        assert r.success is True
        assert dest.read_bytes() == b""

    def test_roundtrip_multichunk(self, tmp_path):
        # spans several keystream blocks and more than one read chunk
        data = os.urandom(CHUNK_SIZE + BLOCK_SIZE * 5 + 17)
        src, out = self._encrypt(tmp_path, "big.bin", data)
        dest = tmp_path / "big.out"
        r = self.cipher.decode(
            _Args(key=PASSWORD, file=str(out), output=str(dest), iterations=ITERATIONS)
        )
        assert r.success is True
        assert dest.read_bytes() == data

    def test_default_output_names(self, tmp_path):
        src, out = self._encrypt(tmp_path, "payload.bin", b"hello")
        assert out.name == "payload.bin.enc"
        r = self.cipher.decode(_Args(key=PASSWORD, file=str(out), iterations=ITERATIONS))
        assert r.success is True
        # strips .enc on decrypt
        assert (tmp_path / "payload.bin").read_bytes() == b"hello"

    def test_remove_source_deletes_original(self, tmp_path):
        src, out = self._encrypt(tmp_path, "locked.bin", b"lock me", remove_source=True)
        assert out.is_file()
        assert src.exists() is False
        # the ciphertext still recovers the original bytes
        dest = tmp_path / "locked.dec"
        r = self.cipher.decode(
            _Args(key=PASSWORD, file=str(out), output=str(dest), iterations=ITERATIONS)
        )
        assert r.success is True
        assert dest.read_bytes() == b"lock me"

    # ------------------------------------------------------------------- crypto

    def test_ciphertext_differs_from_plaintext(self, tmp_path):
        data = b"A" * 64
        _, out = self._encrypt(tmp_path, "repeat.bin", data)
        blob = out.read_bytes()
        ciphertext = blob[42:-32]
        assert ciphertext != data
        # same plaintext never repeats in the keystream (no ECB-ish pattern)
        assert len(set(ciphertext[i : i + 32] for i in range(0, 64, 32))) == 2

    def test_nonce_randomised(self, tmp_path):
        _, out1 = self._encrypt(tmp_path, "a.bin", b"same plaintext")
        _, out2 = self._encrypt(tmp_path, "b.bin", b"same plaintext")
        assert out1.read_bytes() != out2.read_bytes()

    def test_wrong_password_fails(self, tmp_path):
        _, out = self._encrypt(tmp_path, "secret.bin", b"top secret")
        r = self.cipher.decode(
            _Args(key="wrong password", file=str(out), iterations=ITERATIONS)
        )
        assert r.success is False
        assert "wrong password or file has been tampered" in r.output

    def test_tampered_ciphertext_fails(self, tmp_path):
        _, out = self._encrypt(tmp_path, "tamper.bin", b"integrity matters")
        blob = bytearray(out.read_bytes())
        blob[50] ^= 0xFF  # flip one ciphertext byte
        tampered = tmp_path / "tampered.bin"
        tampered.write_bytes(bytes(blob))
        r = self.cipher.decode(
            _Args(key=PASSWORD, file=str(tampered), iterations=ITERATIONS)
        )
        assert r.success is False
        assert "tampered" in r.output

    def test_tampered_mac_fails(self, tmp_path):
        _, out = self._encrypt(tmp_path, "mac.bin", b"integrity matters")
        blob = bytearray(out.read_bytes())
        blob[-1] ^= 0xFF  # corrupt the mac itself
        tampered = tmp_path / "tampered_mac.bin"
        tampered.write_bytes(bytes(blob))
        r = self.cipher.decode(
            _Args(key=PASSWORD, file=str(tampered), iterations=ITERATIONS)
        )
        assert r.success is False

    def test_bad_magic_fails(self, tmp_path):
        junk = tmp_path / "junk.bin"
        junk.write_bytes(b"not an 0xPo11 file at all, really")
        r = self.cipher.decode(_Args(key=PASSWORD, file=str(junk), iterations=ITERATIONS))
        assert r.success is False
        assert "magic" in r.output

    def test_truncated_file_fails(self, tmp_path):
        _, out = self._encrypt(tmp_path, "trunc.bin", b"some data")
        short = tmp_path / "truncated.bin"
        short.write_bytes(out.read_bytes()[:20])
        r = self.cipher.decode(
            _Args(key=PASSWORD, file=str(short), iterations=ITERATIONS)
        )
        assert r.success is False

    def test_embedded_iterations_used(self, tmp_path):
        # encrypt with a custom count, decrypt WITHOUT passing -it
        _, out = self._encrypt(tmp_path, "iter.bin", b"round trip", )
        r = self.cipher.decode(_Args(key=PASSWORD, file=str(out)))
        assert r.success is True
        # .enc is stripped, restoring the original filename
        assert (tmp_path / "iter.bin").read_bytes() == b"round trip"

    # ------------------------------------------------------------------ inline

    def test_inline_roundtrip(self):
        encoded = self.cipher.encode(
            _Args(key=PASSWORD, text="inline secret", iterations=ITERATIONS)
        )
        assert encoded.success is True
        decoded = self.cipher.decode(_Args(key=PASSWORD, text=encoded.output))
        assert decoded.success is True
        assert decoded.output == "inline secret"

    def test_inline_bad_hex_fails(self):
        r = self.cipher.decode(_Args(key=PASSWORD, text="not hex!!!"))
        assert r.success is False

    # ------------------------------------------------------------------ guards

    def test_missing_password(self, tmp_path):
        src, _ = self._encrypt(tmp_path, "p.bin", b"x")
        r = self.cipher.decode(_Args(key=None, file=str(src)))
        assert r.success is False
        assert "password" in r.output

    def test_missing_input(self):
        r = self.cipher.encode(_Args(key=PASSWORD))
        assert r.success is False
        assert "-i" in r.output or "-t" in r.output

    def test_missing_file(self, tmp_path):
        r = self.cipher.encode(
            _Args(key=PASSWORD, file=str(tmp_path / "nope.bin"), iterations=ITERATIONS)
        )
        assert r.success is False
        assert "not found" in r.output

    def test_brute_not_supported(self):
        r = self.cipher.brute(_Args(text="x"))
        assert r.success is False

    def test_default_iterations_reasonable(self):
        assert DEFAULT_ITERATIONS >= 100_000
        r = self.cipher.encode(_Args(key=PASSWORD, text="x", iterations=0))
        assert r.success is True  # 0 falls back to the default, not a crash

    # ------------------------------------------------------------------- keystream

    def test_keystream_deterministic_and_counter_bound(self):
        key, nonce = os.urandom(32), os.urandom(16)
        assert _keystream_block(key, nonce, 0) == _keystream_block(key, nonce, 0)
        assert _keystream_block(key, nonce, 0) != _keystream_block(key, nonce, 1)
        assert _keystream_block(key, nonce, 0) != _keystream_block(key, nonce, 0xFFFFFFFFFFFFFFFF)

    def test_chunk_boundary_alignment(self):
        # chunk sizes that are not multiples of the block size must still chain
        key, nonce = os.urandom(32), os.urandom(16)
        data = os.urandom(CHUNK_SIZE + 100)
        part1, block = _crypt_chunk(data[:CHUNK_SIZE], key, nonce, 0)
        part2, _ = _crypt_chunk(data[CHUNK_SIZE:], key, nonce, block)
        whole, _ = _crypt_chunk(data, key, nonce, 0)
        assert part1 + part2 == whole
