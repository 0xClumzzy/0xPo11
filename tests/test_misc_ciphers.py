"""Tests for ROT13, ROT47, Reverse, Morse, Phonetic, Leetspeak, Monoalphabetic ciphers."""
import importlib
from zeropo11.ciphers.r13 import Cipher as ROT13
from zeropo11.ciphers.r47 import Cipher as ROT47
from zeropo11.ciphers.rc import Cipher as RC
from zeropo11.ciphers.mor import Cipher as MOR
from zeropo11.ciphers.pho import Cipher as PHO
from zeropo11.ciphers.mo import Cipher as MO

_l337_mod = importlib.import_module("zeropo11.ciphers.1337")
L337 = _l337_mod.Cipher
from zeropo11.ciphers.mo import Cipher as MO


class _Args:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestROT13:
    def setup_method(self):
        self.cipher = ROT13()

    def test_encode(self):
        r = self.cipher.encode(_Args(text="hello"))
        assert r.output == "uryyb"

    def test_decode(self):
        r = self.cipher.decode(_Args(text="uryyb"))
        assert r.output == "hello"

    def test_roundtrip(self):
        encoded = self.cipher.encode(_Args(text="Hello World"))
        decoded = self.cipher.decode(_Args(text=encoded.output))
        assert decoded.output == "Hello World"


class TestROT47:
    def setup_method(self):
        self.cipher = ROT47()

    def test_encode(self):
        r = self.cipher.encode(_Args(text="Hello World!"))
        assert r.success is True

    def test_roundtrip(self):
        original = "Hello World!"
        encoded = self.cipher.encode(_Args(text=original))
        decoded = self.cipher.decode(_Args(text=encoded.output))
        assert decoded.output == original


class TestReverse:
    def setup_method(self):
        self.cipher = RC()

    def test_encode(self):
        r = self.cipher.encode(_Args(text="hello"))
        assert r.output == "olleh"

    def test_decode(self):
        r = self.cipher.decode(_Args(text="olleh"))
        assert r.output == "hello"


class TestMorse:
    def setup_method(self):
        self.cipher = MOR()

    def test_encode(self):
        r = self.cipher.encode(_Args(text="SOS"))
        assert r.output == "... --- ..."

    def test_decode(self):
        r = self.cipher.decode(_Args(text="... --- ..."))
        assert r.output == "SOS"

    def test_roundtrip(self):
        encoded = self.cipher.encode(_Args(text="HELLO"))
        decoded = self.cipher.decode(_Args(text=encoded.output))
        assert decoded.output == "HELLO"


class TestPhonetic:
    def setup_method(self):
        self.cipher = PHO()

    def test_encode(self):
        r = self.cipher.encode(_Args(text="AB"))
        assert r.output == "Alfa Bravo"

    def test_decode(self):
        r = self.cipher.decode(_Args(text="Alfa Bravo"))
        assert r.output == "AB"


class TestLeetspeak:
    def setup_method(self):
        self.cipher = L337()

    def test_encode(self):
        r = self.cipher.encode(_Args(text="hello"))
        assert r.success is True
        assert "3" in r.output

    def test_no_text(self):
        r = self.cipher.encode(_Args(text=None))
        assert r.success is False


class TestMonoalphabetic:
    def setup_method(self):
        self.cipher = MO()

    def test_encode(self):
        r = self.cipher.encode(_Args(text="abc"))
        assert r.output == "cde"

    def test_decode(self):
        r = self.cipher.decode(_Args(text="cde"))
        assert r.output == "abc"

    def test_roundtrip(self):
        encoded = self.cipher.encode(_Args(text="Hello World"))
        decoded = self.cipher.decode(_Args(text=encoded.output))
        assert decoded.output == "Hello World"
