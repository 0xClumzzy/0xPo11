---
marp: true
theme: default
paginate: true
size: 16:9
footer: '0xPo11 · ransomware simulation framework · simulation only — lab-scoped'
style: |
  section { font-size: 20px; }
  h1 { color: #008b8b; font-size: 30px; }
  a { color: #008b8b; }
  code { background: #101418; color: #7fe3d4; padding: 0 4px; border-radius: 3px; font-size: 18px; }
  pre { background: #101418; }
  pre code { color: #d6f5ef; }
  table { font-size: 17px; }
  blockquote { border-left: 4px solid #008b8b; color: #444; }
  footer { color: #888; font-size: 13px; }
---

# 0xPo11 — What it is

**A ransomware *simulation* framework: the cryptographic core of a ransomware attack chain, rebuilt from first principles in Python.**

- **30 ciphers, built from scratch** — no external crypto libraries; byte-level Python
- **The whole chain is simulated** — obfuscation → sample identification → file encryption → remote execution → extortion note → recovery
- **Three interfaces** — `key` CLI · `keyconsole` interactive shell · localhost control-panel dashboard
- Built for **malware analysis and offensive-tooling fundamentals**: understand the primitives well enough to detect them

**Deliberately *not* included:** propagation · C2 channel · key exfiltration · persistence · loader.
Destructive behavior is opt-in and lab-scoped; every artifact carries a simulation marker.

> 30 ciphers · 6-phase chain · PBKDF2-HMAC + verify-before-write · 125 tests

*0xSESSIONS · github.com/0xClumzzy/0xPo11*

---

# How it works — the engine

- **Cipher registry** — every cipher self-registers (code, flags, encode/decode); the CLI, keyconsole and panel share one dispatch engine
- **Layered transforms** — chain ciphers with `+`, exactly how real obfuscators stack encodings:

```bash
key cc -e -t "payload" -k 3 + b64 -e        # -> c2Rib3JkZw==
```

- **`fe` — authenticated file encryption (the impact stage):**
  - PBKDF2-HMAC-SHA256 · 200,000 iterations → encryption key **+ separate MAC key**
  - SHA-256 counter-mode keystream · 1 MiB streaming chunks — the file is never fully in memory
  - HMAC-SHA256 over header + ciphertext — **verified before anything is written**; wrong key or a flipped byte → clean refusal, never garbage
  - random salt + nonce per file → the same password never repeats the ciphertext

```
file.enc = [ magic 0xFE | version | kdf | iters | salt | nonce ] | ciphertext | HMAC
```

- **Remote mode** — `--host` streams through the system `ssh` binary: no agent, no install; plaintext never touches the remote disk; `--local-in` / `--local-out` make every path's endpoint explicit

---

# How it works — the chain in action

| # | Phase | Command |
|---|---|---|
| 1 | Obfuscate | `key cc -e -t "payload" -k 3 + b64 -e` |
| 2 | Identify | `key md5 -e -t "payload.exe"` — sample fingerprints / IOCs |
| 3 | Impact | `key fe -e -i ./target -k "hunter2"` — recursive sweep, `*.enc` beside each source |
| 4 | Cross-machine | `key fe -e --host user@host -i /data/db.dump` — streams over ssh |
| 5 | Extort | `key fe ... --drop-note press` — note dropped + auto-printed on success |
| 6 | Recover | `key fe -d -i victims.db.enc -k "hunter2"` — fail-clean decrypt |

- **Guardrails:** non-destructive by default (`--remove-source` is opt-in, note drops first); the disposable lab rebuilds in one command; `golden/` copies make recovery *provable* (`diff` = MATCH); 125 tests + headless `demo.sh`
- **For defenders:** every phase is a detection opportunity — mass `.enc` writes, per-file entropy jumps, unsigned processes spawning `ssh`; fail-clean MACs + offline backups beat decryption hope
