"""Twofish symmetric encryption cipher."""
from __future__ import annotations

from zeropo11.ciphers.base import BaseCipher, CipherResult


class Cipher(BaseCipher):
    """Twofish encryption/decryption cipher."""

    name = "Twofish Encryption"
    command = "twofish"
    help_menu = """USAGE:
  key twofish [FLAGS] [OPTIONS]
FLAGS:
  -e, --encode  Encrypt input text
  -d, --decode  Decrypt input text
OPTIONS:
  -t, --text <text>  Input text
  -k, --key <key>    Encryption key (1-32 chars)
  -o, --output <file> Output file (optional, for piping)
EXAMPLES:
  key twofish -e -t "hello" -k "secretkey"
"""

    def encode(self, args):
        text = getattr(args, "text", None)
        key = getattr(args, "key", None)
        output = getattr(args, "output", None)
        if not text or not key:
            return CipherResult("Please provide -t <text> and -k <key>", False)
        try:
            from twofish import Twofish

            key_bytes = key.encode().ljust(16, b"\0")[:16]
            tf = Twofish(key_bytes)
            text_bytes = text.encode()
            pad_len = 16 - (len(text_bytes) % 16)
            text_bytes += bytes([pad_len] * pad_len)
            encrypted = b""
            for i in range(0, len(text_bytes), 16):
                encrypted += tf.encrypt(text_bytes[i : i + 16])
            result = encrypted.hex()
            if output:
                return CipherResult(result, True)
            return CipherResult(f"Encrypted: {result}", True)
        except ImportError:
            return CipherResult("Install twofish: pip install twofish", False)
        except Exception as e:
            return CipherResult(f"Encryption failed: {e}", False)

    def decode(self, args):
        text = getattr(args, "text", None)
        key = getattr(args, "key", None)
        output = getattr(args, "output", None)
        if not text or not key:
            return CipherResult("Please provide -t <text> and -k <key>", False)
        try:
            from twofish import Twofish

            key_bytes = key.encode().ljust(16, b"\0")[:16]
            tf = Twofish(key_bytes)
            encrypted = bytes.fromhex(text)
            decrypted = b""
            for i in range(0, len(encrypted), 16):
                decrypted += tf.decrypt(encrypted[i : i + 16])
            pad_len = decrypted[-1]
            if 1 <= pad_len <= 16:
                decrypted = decrypted[:-pad_len]
            result = decrypted.decode()
            if output:
                return CipherResult(result, True)
            return CipherResult(f"Decrypted: {result}", True)
        except ImportError:
            return CipherResult("Install twofish: pip install twofish", False)
        except Exception as e:
            return CipherResult(f"Decryption failed: {e}", False)
