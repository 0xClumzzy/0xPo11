"""Tests for the ransom note generator (rn)."""
from __future__ import annotations

from zeropo11.ciphers.fe import MAGIC
from zeropo11.ciphers.rn import (
    Cipher as Rn,
)
from zeropo11.ciphers.rn import (
    _fingerprint,
    _grouped,
    _random_victim_id,
    _victim_id_from_salt,
)

PASSWORD = "hunter2"


class _Args:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestRansomNote:
    def setup_method(self):
        self.cipher = Rn()

    # ------------------------------------------------------------------ basics

    def test_default_note_generated(self):
        r = self.cipher.encode(_Args())
        assert r.success is True
        assert "ENCRYPTED" in r.output
        assert "Victim ID" in r.output
        assert "PLACEHOLDER" in r.output
        assert "educational simulation" in r.output  # footer always present

    def test_victim_id_groups(self):
        assert _grouped("0123456789abcdef") == "0123-4567-89ab-cdef"
        assert len(_grouped("0123456789ABCDEF")) == 19

    def test_victim_ids_random_by_default(self):
        assert _random_victim_id() != _random_victim_id()

    # --------------------------------------------------------------- templates

    def test_template_selection(self):
        for template, marker in (
            ("generic", "YOUR FILES ARE ENCRYPTED"),
            ("polite", "Dear Administrator"),
            ("press", "PRESS RELEASE"),
        ):
            r = self.cipher.encode(_Args(template=template))
            assert r.success is True
            assert marker in r.output

    def test_unknown_template_rejected(self):
        r = self.cipher.encode(_Args(template="ransom-note-9000"))
        assert r.success is False
        assert "generic" in r.output and "polite" in r.output and "press" in r.output

    # ------------------------------------------------------------------- input

    def test_explicit_victim_id_honored(self):
        r = self.cipher.encode(_Args(text="AAAA-BBBB-CCCC-DDDD"))
        assert "AAAA-BBBB-CCCC-DDDD" in r.output
        r2 = self.cipher.encode(_Args(text="AAAA-BBBB-CCCC-DDDD"))
        assert "AAAA-BBBB-CCCC-DDDD" in r2.output  # stable when given

    def test_victim_id_from_encrypted_file(self, tmp_path):
        salt = bytes(range(16))
        blob = MAGIC + bytes([1, 1]) + (200_000).to_bytes(4, "big") + salt + b"\x00" * 48
        enc = tmp_path / "victims.db.enc"
        enc.write_bytes(blob)

        r = self.cipher.encode(_Args(file=str(enc)))
        assert r.success is True
        assert _victim_id_from_salt(salt) in r.output

    def test_garbage_file_falls_back_to_random_id(self, tmp_path):
        junk = tmp_path / "not-encrypted.bin"
        junk.write_bytes(b"definitely not an 0xPo11 file")
        r = self.cipher.encode(_Args(file=str(junk)))
        assert r.success is True  # generator still produces a note

    def test_missing_file_falls_back(self):
        r = self.cipher.encode(_Args(file="/nonexistent/file.enc"))
        assert r.success is True

    def test_key_fingerprint_shown(self):
        r = self.cipher.encode(_Args(key=PASSWORD))
        assert _fingerprint(PASSWORD) in r.output

    # ----------------------------------------------------------------- deadline

    def test_deadline_hours(self):
        r = self.cipher.encode(_Args(deadline="6"))
        assert r.success is True
        assert "6 hours" in r.output

    def test_deadline_invalid_rejected(self):
        assert self.cipher.encode(_Args(deadline="tomorrow")).success is False
        assert self.cipher.encode(_Args(deadline="0")).success is False
        assert self.cipher.encode(_Args(deadline="-5")).success is False

    # ------------------------------------------------------------------ output

    def test_output_file_written(self, tmp_path):
        out = tmp_path / "NOTE.txt"
        r = self.cipher.encode(_Args(output=str(out)))
        assert r.success is True
        assert "written to" in r.output
        text = out.read_text()
        assert "Victim ID" in text
        assert text.endswith("=" * 62)

    # ------------------------------------------------------------------ guards

    def test_brute_not_supported(self):
        r = self.cipher.brute(_Args())
        assert r.success is False
        assert "brute" in r.output

    def test_registered_command(self):
        from zeropo11.ciphers import get_cipher

        assert get_cipher("rn").name == "Ransom Note"
