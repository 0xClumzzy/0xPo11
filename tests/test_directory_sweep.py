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
