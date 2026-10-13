"""Tests for the XOR cipher (cycling key)."""
from zeropo11.ciphers.xor import Cipher as Xor


class _Args:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestXor:
    def setup_method(self):
        self.cipher = Xor()

    def test_single_char_key_cycles(self):
        r = self.cipher.encode(_Args(text="hello", key="A"))
        assert r.success is True
        assert r.output == ")$--."

    def test_equal_length_key(self):
        r = self.cipher.encode(_Args(text="a1b2", key="1a2b"))
        assert r.success is True
        assert r.output == "PPPP"

    def test_key_longer_than_text(self):
        r = self.cipher.encode(_Args(text="hi", key="abcdef"))
        assert r.success is True

    def test_roundtrip_single_char_key(self):
        encoded = self.cipher.encode(_Args(text="cmd.exe /c powershell", key="A"))
        assert encoded.success is True
        decoded = self.cipher.decode(_Args(text=encoded.output, key="A"))
        assert decoded.output == "cmd.exe /c powershell"

    def test_roundtrip_multi_char_key(self):
        encoded = self.cipher.encode(_Args(text="The quick brown fox", key="key"))
        decoded = self.cipher.decode(_Args(text=encoded.output, key="key"))
        assert decoded.output == "The quick brown fox"

    def test_no_key_fails(self):
        r = self.cipher.encode(_Args(text="hello", key=None))
        assert r.success is False

    def test_no_text_fails(self):
        r = self.cipher.encode(_Args(text=None, key="A"))
        assert r.success is False
