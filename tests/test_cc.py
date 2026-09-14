"""Tests for Caesar Cipher."""
from zeropo11.ciphers.cc import Cipher


cipher = Cipher()


class _Args:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def test_encode_basic():
    result = cipher.encode(_Args(text="hello", key="3"))
    assert result.output == "khoor"
    assert result.success is True


def test_decode_basic():
    result = cipher.decode(_Args(text="khoor", key="3"))
    assert result.output == "hello"
    assert result.success is True


def test_encode_uppercase():
    result = cipher.encode(_Args(text="HELLO", key="3"))
    assert result.output == "KHOOR"


def test_encode_decode_roundtrip():
    original = "The Quick Brown Fox!"
    encoded = cipher.encode(_Args(text=original, key="7"))
    decoded = cipher.decode(_Args(text=encoded.output, key="7"))
    assert decoded.output == original


def test_encode_no_text():
    result = cipher.encode(_Args(text=None, key="3"))
    assert result.success is False


def test_encode_no_key():
    result = cipher.encode(_Args(text="hello", key=None))
    assert result.success is False


def test_brute():
    result = cipher.brute(_Args(text="khoor", range="1,26"))
    assert "hello" in result.output
    assert result.success is True


def test_brute_no_text():
    result = cipher.brute(_Args(text=None, range="1,26"))
    assert result.success is False
