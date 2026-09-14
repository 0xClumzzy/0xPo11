"""Blowfish symmetric encryption cipher with multiple modes."""
from __future__ import annotations

from zeropo11.ciphers.base import BaseCipher, CipherResult

HELP = """USAGE:
  key blowfish [FLAGS] [OPTIONS]
FLAGS:
  -e, --encode  Encrypt input text
  -d, --decode  Decrypt input text
OPTIONS:
  -t, --text <text>  Input text
  -k, --key <key>    Encryption key
  -md, --mode <mode>  Mode: block, ecb, cbc, cfb, ofb, ctr (default: cbc)
  -iv <iv>           Initialization vector (8 bytes for cbc/cfb/ofb)
  -nc, --nonce <n>   Nonce for CTR mode (auto-generated if omitted)
EXAMPLES:
  key blowfish -e -t "hello" -k "secret" -md cbc
"""


def _pad(data: bytes) -> bytes:
    pad_len = 8 - (len(data) % 8)
    return data + bytes([pad_len] * pad_len)


def _unpad(data: bytes) -> bytes:
    pad_len = data[-1]
    if 1 <= pad_len <= 8:
        return data[:-pad_len]
    return data


def _xor_bytes(a: bytes, b: bytes) -> bytes:
    return bytes(x ^ y for x, y in zip(a, b, strict=True))


class Cipher(BaseCipher):
    """Blowfish encryption/decryption cipher."""

    name = "Blowfish Encryption"
    command = "blowfish"
    help_menu = HELP

    def encode(self, args: object) -> CipherResult:
        text = getattr(args, "text", None)
        key = getattr(args, "key", None)
        mode = getattr(args, "mode", None) or "cbc"
        iv = getattr(args, "iv", None)
        nonce = getattr(args, "nonce", None)
        if not text or not key:
            return CipherResult("Please provide -t <text> and -k <key>", False)
        try:
            import blowfish

            cipher = blowfish.Cipher(key.encode())
            data = _pad(text.encode())
            iv_bytes = iv.encode()[:8] if iv else b"\x00" * 8
            if mode == "ecb":
                result = b"".join(
                    cipher.encrypt_block(data[i : i + 8]) for i in range(0, len(data), 8)
                )
            elif mode == "cbc":
                result = b""
                prev = iv_bytes
                for i in range(0, len(data), 8):
                    block = _xor_bytes(data[i : i + 8], prev)
                    encrypted = cipher.encrypt_block(block)
                    result += encrypted
                    prev = encrypted
            elif mode == "cfb":
                result = b""
                prev = iv_bytes
                for i in range(0, len(data), 8):
                    encrypted = cipher.encrypt_block(prev)
                    block = _xor_bytes(data[i : i + 8], encrypted)
                    result += block
                    prev = block
            elif mode == "ofb":
                result = b""
                prev = iv_bytes
                for i in range(0, len(data), 8):
                    encrypted = cipher.encrypt_block(prev)
                    block = _xor_bytes(data[i : i + 8], encrypted)
                    result += block
                    prev = encrypted
            elif mode == "ctr":
                import os

                ctr = nonce if nonce else int.from_bytes(os.urandom(8), "big")
                result = b""
                for i in range(0, len(data), 8):
                    counter = (ctr + i // 8).to_bytes(8, "big")
                    encrypted = cipher.encrypt_block(counter)
                    block = _xor_bytes(data[i : i + 8], encrypted)
                    result += block
            else:
                return CipherResult(f"Unsupported mode: {mode}", False)
            return CipherResult(result.hex(), True)
        except ImportError:
            return CipherResult("Install blowfish: pip install blowfish", False)
        except Exception as e:
            return CipherResult(f"Encryption failed: {e}", False)

    def decode(self, args: object) -> CipherResult:
        text = getattr(args, "text", None)
        key = getattr(args, "key", None)
        mode = getattr(args, "mode", None) or "cbc"
        iv = getattr(args, "iv", None)
        nonce = getattr(args, "nonce", None)
        if not text or not key:
            return CipherResult("Please provide -t <text> and -k <key>", False)
        try:
            import blowfish

            cipher = blowfish.Cipher(key.encode())
            data = bytes.fromhex(text)
            iv_bytes = iv.encode()[:8] if iv else b"\x00" * 8
            if mode == "ecb":
                result = b"".join(
                    cipher.decrypt_block(data[i : i + 8]) for i in range(0, len(data), 8)
                )
            elif mode == "cbc":
                result = b""
                prev = iv_bytes
                for i in range(0, len(data), 8):
                    block = cipher.decrypt_block(data[i : i + 8])
                    result += _xor_bytes(block, prev)
                    prev = data[i : i + 8]
            elif mode == "cfb":
                result = b""
                prev = iv_bytes
                for i in range(0, len(data), 8):
                    encrypted = cipher.encrypt_block(prev)
                    result += _xor_bytes(data[i : i + 8], encrypted)
                    prev = data[i : i + 8]
            elif mode == "ofb":
                result = b""
                prev = iv_bytes
                for i in range(0, len(data), 8):
                    encrypted = cipher.encrypt_block(prev)
                    result += _xor_bytes(data[i : i + 8], encrypted)
                    prev = encrypted
            elif mode == "ctr":
                ctr = nonce if nonce else 0
                result = b""
                for i in range(0, len(data), 8):
                    counter = (ctr + i // 8).to_bytes(8, "big")
                    encrypted = cipher.encrypt_block(counter)
                    result += _xor_bytes(data[i : i + 8], encrypted)
            else:
                return CipherResult(f"Unsupported mode: {mode}", False)
            return CipherResult(_unpad(result).decode(), True)
        except ImportError:
            return CipherResult("Install blowfish: pip install blowfish", False)
        except Exception as e:
            return CipherResult(f"Decryption failed: {e}", False)
