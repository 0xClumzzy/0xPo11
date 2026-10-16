---
marp: true
theme: default
paginate: true
size: 16:9
style: |
  section { font-size: 25px; }
  h1 { color: #008b8b; }
  h2 { color: #008b8b; }
  a { color: #008b8b; }
  code { background: #101418; color: #7fe3d4; padding: 0 5px; border-radius: 3px; }
  pre { background: #101418; }
  pre code { color: #d6f5ef; }
  table { font-size: 21px; }
  blockquote { border-left: 4px solid #008b8b; color: #444; font-style: italic; }
  section.lead h1 { font-size: 46px; }
  section.lead { text-align: center; }
---

<!-- _class: lead -->

```
  ___        ┌──────────────┐
 / _ \__  __/│ ◆ ENCRYPT    │
| | | \ \/ / │ ◆ DECRYPT    │
| |_| |>  <  │ ◆ CRACK      │
 \___//_/\_\ └──────────────┘
  0    x     [ REDACTED ]
```

# 0xPo11

### Ransomware Simulation Framework

The cryptographic core of a ransomware chain, built from first principles

**0xSESSIONS** · github.com/0xClumzzy/0xPo11

---

# Why this project?

- Defenders see the **artifacts** of attacks — rarely the **construction**
- You can't detect what you don't understand: XOR strings, layered obfuscation, PBKDF2 keystreams, MACs
- Learn primitives by rebuilding them: byte-level Python, no libraries, no magic
- Fundamentals for **malware analysis** and **offensive tooling development**

> "0xPo11 implements the cryptographic *core* of a ransomware chain from first
> principles — obfuscation, credential access, file encryption, and the extortion
> artifact. It is a simulation — and the point is understanding it well enough to
> detect it."

<!-- Speaker note: say this framing out loud — it sets the tone for the whole talk. -->

---

# What it is

- **30 ciphers** built from scratch — no external crypto libraries
- **Keyconsole** — Metasploit-style interactive shell for rapid analysis
- **`fe`** — password-based, authenticated file encryption (the "impact" stage)
- **Remote encryption** — streams files over system `ssh`, zero footprint
- **`rn`** — ransom-note generator (three operator voices)
- **Control panel** — localhost dashboard that drives the whole chain
- Layered transforms — chain ciphers with `+` like real obfuscators do

---

# What it is *not*

- ❌ No propagation &nbsp;&nbsp; ❌ No C2 channel
- ❌ No key exfiltration &nbsp;&nbsp; ❌ No persistence &nbsp;&nbsp; ❌ No loader
- ✅ Every artifact carries a **simulation marker**
- ✅ Destructive behavior is **opt-in and lab-scoped**
- ✅ What's *missing* is deliberate — the roadmap tracks it

> The boundary between "crypto demo" and "ransomware kit" is the project's scope.

<!-- Speaker note: this slide preempts the first Q&A question. Missing stages = by design. -->

---

# The toolbox: 30 ciphers, first principles

| Family | Examples | What it teaches |
|---|---|---|
| Classical | Caesar (`cc`), Vigenère (`vc`) | Shift/substitution math |
| Encoding | Base64 (`b64`), hex, URL, `1337` | Obfuscation chains |
| Hashing | MD5, SHA-1, SHA-256/512 | IOCs, sample fingerprints |
| Modern | XOR, Twofish, Blowfish | String encryption in the wild |
| Tooling | `fe` `rn` `hashid` `cp` | The ransomware chain itself |

**Layered obfuscation — two ciphers, one command:**

```bash
key cc -e -t "payload" -k 3 + b64 -e      # -> c2Rib3JkZw==
key b64 -d -t "c2Rib3JkZw==" + cc -d -k 3 # -> payload  (reverse order)
```

---

# The chain we simulate

| # | Phase | Command |
|---|---|---|
| 1 | **Obfuscate** — hide intent | `key cc -e -t "..." -k 3 + b64 -e` |
| 2 | **Identify** — create IOCs | `key md5 -e -t "payload.exe"` |
| 3 | **Impact** — encrypt files | `key fe -e -i ./target -k "hunter2"` |
| 4 | **Cross machines** — zero footprint | `key fe -e --host user@host -i /data/db.dump ...` |
| 5 | **Extort** — operator psychology | `key fe ... --drop-note press` |
| 6 | **Recover** — fail clean | `key fe -d -i victims.db.enc -k "hunter2"` |

Each phase is a detection opportunity — that's the narrative.

---

# Deep dive: `fe` — file encryption

- **PBKDF2-HMAC-SHA256** — 200,000 iterations → encryption key + *separate* MAC key
- **SHA-256 in counter mode** — the keystream; 1 MiB streaming chunks (whole file never in memory)
- **HMAC-SHA256** covers header + ciphertext — verified **before** anything is written
- Wrong password / flipped byte → **clean refusal**, never garbage output
- Random salt + nonce per file → the same password never yields the same ciphertext twice

```text
file.enc = magic (0xFE) | version | kdf | iterations | salt | nonce | ciphertext | HMAC
```

- Standard-library only: `hashlib`, `hmac`, `os.urandom`

<!-- Speaker note: the "fail clean" property is the audience's favorite part — demo it live. -->

---

# Deep dive: remote encryption over `ssh`

- `--host user@server` streams the file through the **system `ssh` binary**
- **No agent, no install, nothing added** to the far machine
- Plaintext never touches the remote disk — pipe and process memory only
- `--local-in` / `--local-out` — every path's endpoint is stated explicitly
- Same `0xFE` format everywhere → remote ciphertext decrypts locally and vice versa
- `--timeout` kills stalled transfers

```bash
key fe -e --host deploy@server -i /data/db.dump -k hunter2 --local-out -o db.enc
key fe -d --host deploy@server -i db.enc -k hunter2 --local-in -o /data/db.dump
```

---

# Impact automation: sweep → note → (opt-in) delete

- **Directory sweep** — recursive; encrypts every file to `<name>.enc` **beside** the source
- **`--drop-note`** — the moment encryption succeeds, the ransom note is dropped
  *and auto-printed to the operator's terminal* (the "hood drop")
- **Default: non-destructive** — originals are kept; the tool stays an analysis aid
- **`--remove-source` (opt-in)** — full simulation: original deleted after its ciphertext
  is written; note drops *first*, then files disappear one by one
- Real ransomware doesn't leave originals — that switch is what makes the demo honest

---

# The extortion artifact: `rn`

- Three operator voices: **generic** (threat), **polite** (support), **press** (publication threat)
- **Victim ID derived from the encrypted file's salt** → note and ciphertext are coupled,
  exactly as a real chain couples them

```bash
key rn -e -i victims.db.enc -k "hunter2" -tm press -o NOTE.txt   # same ID every run
```

- Built from the mechanics real samples share:
  - deadline pressure (`-dl` hours)
  - the "free test decryption" trust trick
  - anti-forensic warnings ("don't use third-party tools")
- Simulation footer + placeholder payment details — **can never be mistaken for a real demand**
- The artifact exists to study the **social engineering**, not to send

---

# Control panel — the whole chain, one dashboard

- Localhost-only Flask app — no auth surface, no network exposure
- **Encrypt / decrypt / remote-run** forms; every field maps to a CLI flag
- **Command preview** — watch the exact `key ...` line being built
- **Simulation mode** — preview the command without executing
- Remote options default to the **local SSH lab** (`127.0.0.1:2222`)
- `--drop-note` + remote host → the note is `cat`-ed back after encryption

> Good for demos and teaching: the audience sees the command *and* the effect.

---

# Guardrails & the lab

- Encrypt-only file operations; nothing points at real user data
- Disposable lab (`setup_demo_env.sh`) — one command rebuilds it from scratch
- **`golden/`** pristine copies → recovery is *provable*: `diff golden/victims.db output/victims.db`
- Local SSH lab on `127.0.0.1:2222` — real-host hardening checklist documented in the README
- 125-test suite + headless `demo.sh` (PASS/FAIL per beat)
- Installer: dedicated venv at `~/.0xPo11/venv` — system Python never touched

<!-- Speaker note: mention the rebuild command — it makes live failures recoverable mid-demo. -->

---

# Under the hood

| Component | Choice |
|---|---|
| Language | Python 3.10+ (stdlib crypto only) |
| CLI | Click + colorama |
| Architecture | Cipher **registry** — every cipher self-registers; CLI ⇄ keyconsole ⇄ panel share one dispatch |
| Testing | `pytest` suite (125 tests), `run_tests.sh` with its own venv |
| Demo | `demo.sh` — headless, non-interactive, PASS/FAIL per beat |
| Packaging | pip / setuptools, bash installer |

- Optional cipher deps (Pillow, pyenchant, twofish…) import **lazily** —
  a missing package prints a clean `pip install X` hint instead of crashing the suite

---

# Live demo — what you'll see next

```bash
# 1. sweep the lab: encrypt every file, drop the note, remove originals
key fe -e --host 127.0.0.1 -i /tmp/0xpo11-lab/target -k hunter2 \
    --local-in --drop-note press --note-out /tmp/0xpo11-lab/NOTE.txt --remove-source

# 2. the target dir now holds only .enc files — and the note is printed

# 3. recover one file from its ciphertext
key fe -d --host 127.0.0.1 -i /tmp/0xpo11-lab/target/victims.db.enc \
    -o /tmp/0xpo11-lab/output/victims.db -k hunter2 --local-out

# 4. prove the recovery against the pristine copy
diff /tmp/0xpo11-lab/golden/victims.db /tmp/0xpo11-lab/output/victims.db   # MATCH
```

Runbook: `DEMO.md` · command card: `/tmp/0xpo11-lab/DEMO_COMMANDS.md`

---

# Defensive takeaways

- **What defenders actually see:** mass writes of a new suffix in seconds,
  per-file entropy jumps, an unsigned process spawning `ssh`
- **Fail-clean is a design property:** HMAC verified *before* write — tamper and
  wrong-key attempts produce clean refusals, never partial plaintext
- **Recovery is the real story:** `golden → restore → diff` shows why offline /
  immutable backups beat any decryption hope
- Read the chain to build detections **for** the chain: canary files, EDR
  mass-write alerts, backup integrity checks

---

# Roadmap — what's done, what's deliberately not

| Phase | Status | Feature |
|---|---|---|
| 1–4 | ✅ | 30 ciphers · keyconsole · cracking + `hashid` · file encryption |
| 6 | ✅ | Ransom-note generator (full chain simulation) |
| 5 | ⬜ | Key-exchange simulation |
| 7 | ⬜ | C2 communication layer |
| 8 | ⬜ | Lateral movement module |
| 9 | ⬜ | Rust rewrite (speed · native binaries) |

> What you've seen is the cryptographic core. Propagation and command-and-control —
> the parts that make something *actually* ransomware — are **not built**, on purpose.

---

<!-- _class: lead -->

# Questions?

**repo:** github.com/0xClumzzy/0xPo11
**docs:** README.md · README.dev.md · DEMO.md
**try it:** `./setup_demo_env.sh && ./demo.sh`

Simulation only — built to be understood, not deployed.
