"""Tests for registry and CLI."""
from zeropo11.ciphers import list_ciphers, get_cipher, get_cipher_info
from zeropo11.ciphers.base import CipherResult


class TestCipherResult:
    def test_unpack(self):
        r = CipherResult("hello", True)
        data, success = r
        assert data == "hello"
        assert success is True

    def test_index(self):
        r = CipherResult("hello", True)
        assert r[0] == "hello"
        assert r[1] is True

    def test_iter(self):
        r = CipherResult("hello", True)
        assert list(r) == ["hello", True]


class TestRegistry:
    def test_list_ciphers(self):
        ciphers = list_ciphers()
        assert "cc" in ciphers
        assert "b64" in ciphers
        assert "md5" in ciphers

    def test_get_cipher(self):
        cipher = get_cipher("cc")
        assert cipher.command == "cc"
        assert cipher.name == "Caesar Cipher"

    def test_get_cipher_invalid(self):
        try:
            get_cipher("nonexistent")
            assert False, "Should have raised KeyError"
        except KeyError:
            pass

    def test_get_cipher_info(self):
        info = get_cipher_info()
        assert len(info) > 0
        assert all(isinstance(i, tuple) and len(i) == 2 for i in info)
