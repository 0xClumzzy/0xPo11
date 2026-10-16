from __future__ import annotations

import os
import shutil
from pathlib import Path

from zeropo11.ciphers.fe import Cipher as Fe

PASSWORD = "hunter2"


class _Args:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def test_local_dir_sweep(tmp_path):
    d = tmp_path / "sw"
    d.mkdir()
    (d / "a.txt").write_bytes(b"alpha")
    (d / "b.txt").write_bytes(b"bravo")
    sub = d / "nested"
    sub.mkdir()
    (sub / "c.txt").write_bytes(b"charlie")

    args = _Args(file=str(d), key=PASSWORD, local_in=True, local_out=True)
    r = Fe().encode(args)
    assert r.success
    assert "3 files" in r.output and "3 encrypted" in r.output
    assert (d / "a.txt.enc").is_file()
    assert (d / "nested" / "c.txt.enc").is_file()


def test_local_dir_sweep_empty(tmp_path):
    d = tmp_path / "empty"
    d.mkdir()
    args = _Args(file=str(d), key=PASSWORD, local_in=True, local_out=True)
    r = Fe().encode(args)
    assert not r.success
    assert "No files found" in r.output


def test_local_dir_requires_password(tmp_path):
    d = tmp_path / "sw"
    d.mkdir()
    (d / "a.txt").write_bytes(b"alpha")
    args = _Args(file=str(d), local_in=True, local_out=True)
    r = Fe().encode(args)
    assert not r.success
    assert "password with -k" in r.output


def test_local_dir_sweep_remove_source(tmp_path):
    d = tmp_path / "sw"
    d.mkdir()
    (d / "a.txt").write_bytes(b"alpha")
    sub = d / "nested"
    sub.mkdir()
    (sub / "c.txt").write_bytes(b"charlie")

    args = _Args(file=str(d), key=PASSWORD, local_in=True, local_out=True, remove_source=True)
    r = Fe().encode(args)
    assert r.success
    assert "2 encrypted" in r.output
    assert "source removed" in r.output
    assert not (d / "a.txt").exists()
    assert not (sub / "c.txt").exists()
    assert (d / "a.txt.enc").is_file()
    assert (sub / "c.txt.enc").is_file()

    # the ciphertext still recovers the original bytes
    dest = tmp_path / "a.txt"
    r2 = Fe().decode(_Args(key=PASSWORD, file=str(d / "a.txt.enc"), output=str(dest)))
    assert r2.success
    assert dest.read_bytes() == b"alpha"


def test_local_dir_sweep_keeps_sources_by_default(tmp_path):
    d = tmp_path / "sw"
    d.mkdir()
    (d / "a.txt").write_bytes(b"alpha")

    args = _Args(file=str(d), key=PASSWORD, local_in=True, local_out=True)
    r = Fe().encode(args)
    assert r.success
    assert (d / "a.txt").is_file()  # no --remove-source => originals are kept
