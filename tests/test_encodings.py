"""Tests for Base64, Binary, Hex, Octal, URL ciphers."""
from zeropo11.ciphers.b64 import Cipher as B64
from zeropo11.ciphers.bin import Cipher as Bin
from zeropo11.ciphers.hex import Cipher as Hex
from zeropo11.ciphers.oct import Cipher as Oct
from zeropo11.ciphers.url import Cipher as Url


class _Args:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestBase64:
    def setup_method(self):
        self.cipher = B64()

    def test_encode(self):
        r = self.cipher.encode(_Args(text="hello"))
        assert r.output == "aGVsbG8="
        assert r.success is True

    def test_decode(self):
        r = self.cipher.decode(_Args(text="aGVsbG8="))
        assert r.output == "hello"
        assert r.success is True

    def test_roundtrip(self):
        encoded = self.cipher.encode(_Args(text="Hello World!"))
        decoded = self.cipher.decode(_Args(text=encoded.output))
        assert decoded.output == "Hello World!"

    def test_no_text(self):
        r = self.cipher.encode(_Args(text=None))
        assert r.success is False


class TestBinary:
    def setup_method(self):
        self.cipher = Bin()

    def test_encode(self):
        r = self.cipher.encode(_Args(text="A"))
        assert r.output == "01000001"
        assert r.success is True

    def test_decode(self):
        r = self.cipher.decode(_Args(text="01000001"))
        assert r.output == "A"

    def test_roundtrip(self):
        encoded = self.cipher.encode(_Args(text="Hi"))
        decoded = self.cipher.decode(_Args(text=encoded.output))
        assert decoded.output == "Hi"


class TestHex:
    def setup_method(self):
        self.cipher = Hex()

    def test_encode(self):
        r = self.cipher.encode(_Args(text="hello"))
        assert r.output == "68656c6c6f"
        assert r.success is True

    def test_decode(self):
        r = self.cipher.decode(_Args(text="68656c6c6f"))
        assert r.output == "hello"

    def test_roundtrip(self):
        encoded = self.cipher.encode(_Args(text="Test 123"))
        decoded = self.cipher.decode(_Args(text=encoded.output))
        assert decoded.output == "Test 123"


class TestOctal:
    def setup_method(self):
        self.cipher = Oct()

    def test_encode(self):
        r = self.cipher.encode(_Args(text="A"))
        assert r.output == "101"
        assert r.success is True

    def test_decode(self):
        r = self.cipher.decode(_Args(text="101"))
        assert r.output == "A"


class TestURL:
    def setup_method(self):
        self.cipher = Url()

    def test_encode(self):
        r = self.cipher.encode(_Args(text="hello world"))
        assert r.output == "hello%20world"

    def test_decode(self):
        r = self.cipher.decode(_Args(text="hello%20world"))
        assert r.output == "hello world"

    def test_roundtrip(self):
        encoded = self.cipher.encode(_Args(text="a=b&c=d"))
        decoded = self.cipher.decode(_Args(text=encoded.output))
        assert decoded.output == "a=b&c=d"
