"""Tests for hash ciphers (MD5, SHA family)."""
import hashlib
from zeropo11.ciphers.md5 import Cipher as MD5
from zeropo11.ciphers.sha1 import Cipher as SHA1
from zeropo11.ciphers.sha224 import Cipher as SHA224
from zeropo11.ciphers.sha256 import Cipher as SHA256
from zeropo11.ciphers.sha384 import Cipher as SHA384
from zeropo11.ciphers.sha512 import Cipher as SHA512


class _Args:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestMD5:
    def setup_method(self):
        self.cipher = MD5()

    def test_encode(self):
        r = self.cipher.encode(_Args(text="hello"))
        expected = hashlib.md5(b"hello").hexdigest()
        assert r.output == expected
        assert r.success is True

    def test_encode_with_salt(self):
        r = self.cipher.encode(_Args(text="hello", salt="salt"))
        expected = hashlib.md5(b"salthello").hexdigest()
        assert r.output == expected

    def test_no_text(self):
        r = self.cipher.encode(_Args(text=None))
        assert r.success is False


class TestSHA1:
    def setup_method(self):
        self.cipher = SHA1()

    def test_encode(self):
        r = self.cipher.encode(_Args(text="hello"))
        expected = hashlib.sha1(b"hello").hexdigest()
        assert r.output == expected


class TestSHA224:
    def setup_method(self):
        self.cipher = SHA224()

    def test_encode(self):
        r = self.cipher.encode(_Args(text="hello"))
        expected = hashlib.sha224(b"hello").hexdigest()
        assert r.output == expected


class TestSHA256:
    def setup_method(self):
        self.cipher = SHA256()

    def test_encode(self):
        r = self.cipher.encode(_Args(text="hello"))
        expected = hashlib.sha256(b"hello").hexdigest()
        assert r.output == expected


class TestSHA384:
    def setup_method(self):
        self.cipher = SHA384()

    def test_encode(self):
        r = self.cipher.encode(_Args(text="hello"))
        expected = hashlib.sha384(b"hello").hexdigest()
        assert r.output == expected


class TestSHA512:
    def setup_method(self):
        self.cipher = SHA512()

    def test_encode(self):
        r = self.cipher.encode(_Args(text="hello"))
        expected = hashlib.sha512(b"hello").hexdigest()
        assert r.output == expected
