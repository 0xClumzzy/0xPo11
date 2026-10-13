"""File Encryption - password-based, authenticated file encryption.

Streaming format built from stdlib primitives only:

    PBKDF2-HMAC-SHA256 (password, salt)  -> enc_key + mac_key
    keystream block i = SHA256(enc_key || nonce || counter_be8)   (CTR mode)
    HMAC-SHA256(mac_key, header || ciphertext)                    (integrity)

File layout (all ints big-endian):

    magic "0xFE" (4) | version (1) | kdf_id (1) | iterations (4)
    | salt (16) | nonce (16) | ciphertext (N) | mac (32)
"""
from __future__ import annotations

import hashlib
import hmac
import os
import struct
from pathlib import Path

from zeropo11.ciphers.base import BaseCipher, CipherResult

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
EXAMPLES:
  key fe -e -i payload.bin -k "hunter2" -o payload.bin.enc
  key fe -d -i payload.bin.enc -k "hunter2" -o payload.bin
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


class Cipher(BaseCipher):
    """Authenticated file encryption cipher."""

    name = "File Encryption"
    command = "fe"
    help_menu = HELP
    binary = True

    # ------------------------------------------------------------------ encode

    def encode(self, args: object) -> CipherResult:
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

        if file_path:
            src = Path(file_path)
            if not src.is_file():
                return CipherResult(f"Input file not found: {file_path}", False)
            output = getattr(args, "output", None) or f"{file_path}.enc"
            try:
                with src.open("rb") as fin, Path(output).open("wb") as fout:
                    fout.write(header)
                    next_block = 0
                    while chunk := fin.read(CHUNK_SIZE):
                        encrypted, next_block = _crypt_chunk(
                            chunk, enc_key, nonce, next_block
                        )
                        mac.update(encrypted)
                        fout.write(encrypted)
                    fout.write(mac.digest())
            except OSError as exc:
                return CipherResult(f"Encryption failed: {exc}", False)
            return CipherResult(f"File encrypted to {output}", True)

        # inline -t data: encrypt and emit as hex for pipe-friendly use
        data = text.encode("utf-8")
        encrypted, _ = _crypt_chunk(data, enc_key, nonce, 0)
        mac.update(encrypted)
        blob = header + encrypted + mac.digest()
        return CipherResult(blob.hex(), True)

    # ------------------------------------------------------------------ decode

    def decode(self, args: object) -> CipherResult:
        password = getattr(args, "key", None)
        if not password:
            return CipherResult("Please provide a password with -k <password>", False)

        iterations_opt = getattr(args, "iterations", None)
        file_path = getattr(args, "file", None)
        text = getattr(args, "text", None)

        if file_path:
            try:
                blob = Path(file_path).read_bytes()
            except OSError as exc:
                return CipherResult(f"Could not read input file: {exc}", False)
        elif text is not None:
            try:
                blob = bytes.fromhex("".join(text.split()))
            except ValueError:
                return CipherResult("Inline ciphertext must be hex (-t <hex>)", False)
        else:
            return CipherResult("Provide a file with -i <path> or hex with -t <hex>", False)

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

        if file_path:
            output = getattr(args, "output", None)
            if not output:
                output = file_path[:-4] if file_path.endswith(".enc") else f"{file_path}.dec"
            try:
                Path(output).write_bytes(plaintext)
            except OSError as exc:
                return CipherResult(f"Decryption failed: {exc}", False)
            return CipherResult(f"File decrypted to {output}", True)

        try:
            return CipherResult(plaintext.decode("utf-8"), True)
        except UnicodeDecodeError:
            return CipherResult(plaintext.hex(), True)

    # ------------------------------------------------------------------- brute

    def brute(self, args: object) -> CipherResult:
        return CipherResult("File encryption requires a password (no brute force)", False)
