# Demo Runbook — 0xPo11 as a Ransomware *Simulation*

A 15-minute, command-by-command script for presenting the suite as a simulation of a
ransomware attack chain. Every command below has been run against this repository; expected
output is what you should see. Timing adds up to ~12 minutes, leaving room for Q&A.

**Framing to say out loud at the start (and to put on slide 1):**

> "0xPo11 implements the *cryptographic core* of a ransomware chain from first principles —
> obfuscation, credential access, file encryption, and the extortion artifact. It is a
> simulation: no propagation, no C2, no key exfiltration, placeholder payment details. Its
> purpose is understanding the primitives well enough to detect them."

---

## 0. Pre-flight (do this the night before)

```bash
# from a checkout of the repo
bash install.sh && exec $SHELL -l        # installs ~/.0xPo11/venv + `key` on PATH

mkdir -p ~/demo && cd ~/demo
printf 'Q3 financials - CONFIDENTIAL\n' > victims.db

# small stand-in wordlist (never point the demo at a real leaked corpus)
printf 'password\n123456\nletmein\np@ssw0rd123\n' > wl.txt

# optional, for beat 7: any host you can ssh into (localhost works if sshd runs)
ssh -o BatchMode=yes localhost 'echo ok' || echo "skip beat 7 if unreachable"
```

Smoke-test the two headline commands once so nothing surprises you live:

```bash
key fe -e -i victims.db -k "demo" -o victims.db.enc && \
key rn -e -i victims.db.enc -k "demo" -tm press -o NOTE.txt && head -5 NOTE.txt
```

---

## 1. Obfuscation — "what a packer does" (2 min)

```bash
key cc -e -t "payload" -k 3 + b64 -e
```

Expected: `c2Rib3JkZw==` — Caesar by 3, then Base64. Two layers, one command; the `+`
splits layers and each result feeds the next.

- **Slide point:** every ransomware stage is wrapped in layers exactly like this; signature
  matching on the outer layer tells you nothing.
- **If asked:** reverse order to decode (`key b64 -d -t "c2Rib3JkZw==" + cc -d -k 3`) — that is why the suite has
  layered *decryption* too.

## 2. XOR — the primitive behind most string obfuscation (1 min)

```bash
key xor -e -t "cmd.exe /c powershell" -k "A"
```

Expected: an escaped binary blob. Then decode it back to prove it is symmetric:

```bash
key xor -d -t "<paste the output>" -k "A"    # -> cmd.exe /c powershell
```

- **Slide point:** a single-character key cycles across the whole string — the pattern that
  shows up in stolen malware samples. Key cycling is what makes it trivially reversible,
  which is the *detection* opportunity.

## 3. The delivery artifact (30 sec)

```bash
key cp -p powershell.ps1
```

Expected: `Payload copied to ./powershell.ps1` — a template straight out of the suite.

- **Slide point:** this is the "stage" a dropper hands to the OS. Templates ship inside the
  wheel and seed into `~/.0xPo11/resources/payloads/`; analysts can swap in their own.

## 4. Credential access — fingerprint, then crack (2 min)

```bash
key md5 -e -t "malware_sample"                                    # 9127daf288687deb678053e2aa828e7d
key hashid -e -t "1fb9c14e934b825a62d15230cc0c2bd1"               # MD5 (or NTLM - test both)
key -ad -t "1fb9c14e934b825a62d15230cc0c2bd1" -w wl.txt           # Found: p@ssw0rd123
```

- **Slide point:** `-ad` fuses identification and cracking. `hashid` is honest about ambiguity —
  it *says* "MD5 or NTLM, test both" instead of guessing, then tries both.
- **If asked:** unsalted MD5/SHA are trivial here; the brute force is single-threaded by design
  (this suite teaches the math, it does not replace hashcat).

## 5. Impact — the encryption stage (3 min)

```bash
key fe -e -i victims.db -k "hunter2" -o victims.db.enc
xxd -l 74 victims.db.enc        # show the header: magic, version, iterations, salt, nonce
```

Expected: `File encrypted to victims.db.enc`. The file grew by 74 bytes: a 42-byte header
(magic `0xFE`, version, KDF id, iteration count, random salt, random nonce) plus a 32-byte MAC.

- **Slide point:** PBKDF2 derives the encryption key and a *separate* MAC key from one
  password; SHA-256 in counter mode is the stream; HMAC-SHA256 covers the whole file.
  Random salt + nonce mean **the same password never yields the same ciphertext twice**.

Restore it, to close the loop cleanly before the failure modes:

```bash
key fe -d -i victims.db.enc -o victims.db.restored -k "hunter2" && cat victims.db.restored
```

- **Reveal the failure modes (this is the part the room remembers)** — note that the
  tamper step corrupts the file, so do the failure modes *last* in this beat:

```bash
key fe -d -i victims.db.enc -k "wrongpass"        # -> Decryption failed: wrong password or file has been tampered with
printf '\xff' | dd of=victims.db.enc bs=1 seek=60 conv=notrunc
key fe -d -i victims.db.enc -k "hunter2"          # -> same refusal, even with the right key
```

- **Slide point:** verification happens *before* decryption is written, so a wrong key yields a
  clean refusal instead of garbage. For the blue team: that refusal message is not what an
  attacker leaves behind — but the *behavior* it models (mass writes of a new suffix, entropy
  jump per file) is exactly what you alert on.

## 6. Remote hosts — encryption that crosses machines (2 min, needs a reachable ssh target)

```bash
key fe -e --host demo@localhost -i /tmp/victims.db -k "hunter2" --local-out victims.db.enc
```

Expected: `File encrypted to victims.db.enc` — pulled over ssh, encrypted locally.

```bash
key fe -d --host demo@localhost --local-in -i victims.db.enc -o /tmp/victims.db -k "hunter2"
```

- **Slide point:** no agent is installed on the far side, no plaintext is written to the remote
  disk, and the same file format means local and remote ciphertext interoperate. `--local-in` /
  `--local-out` make each endpoint explicit — you always know which machine a path refers to.
- **If unreachable:** show the command and the expected output; the transport is three small
  classes in `ciphers/fe.py` worth a code-tour slide instead.

## 7. The extortion artifact (2 min)

```bash
key rn -e -i victims.db.enc -k "hunter2" -tm press -o NOTE.txt
key rn -e -i victims.db.enc -k "hunter2" -tm press    # run twice: victim ID is stable
```

Expected: the same `Victim ID : XXXX-XXXX-XXXX-XXXX` both times — it is derived from the
encrypted file's own salt, so the note and the ciphertext are coupled exactly as a real chain
couples them.

- **Slide point:** three operator voices ship in the suite — `generic` (threat), `polite`
  (customer support), `press` (threatened publication). Every one is built from the same
  pressure mechanics: deadline, "free test decryption", anti-forensic warnings.
- **Say plainly:** payment details are placeholders and the footer marks it as a simulation.
  The artifact exists to study the social engineering, not to send.

## 8. Where this stops (the honest slide) (1 min)

Show the roadmap table from the README and point at phases 7–8 unchecked:

- **Built:** ciphers/encodings, hashing + cracking, keyconsole, file encryption, remote
  encryption, ransom notes (phases 1–6)
- **Not built:** C2 channel (7), lateral movement (8), Rust rewrite (9)

> "What you have seen is the core of the chain. The parts that make something *actually*
> ransomware — propagation and command-and-control — are deliberately not implemented, and
> that boundary is the project's scope."

---

## Q&A prep — the four questions you will get

**"Is this a working ransomware kit?"**
No. There is no propagation, no C2, no key upload, no deletion. It encrypts and it writes notes,
both with simulation markers. The roadmap documents the missing stages.

**"Could someone weaponize it?"**
Any cryptographic primitive can be wrapped in anything; the suite ships no loader, no
persistence, and no exfiltration. The value is understanding what defenders actually see:
file-suffix changes, entropy jumps, mass writes in short windows — and what *effective*
controls look like (offline/immutable backups, per-file MAC meaning tamper is detectable).

**"Why hand-rolled crypto instead of real libraries?"**
Two reasons: zero dependencies for a teaching tool, and every primitive is small enough to read
in one sitting. The docs point at `age`/GPG for anything real, and the roadmap has a Rust
rewrite for performance.

**"What is the key management story?"**
PBKDF2 (200k iterations, tunable) derives an encryption key and a separate MAC key from the
password; salt and nonce are random per file; no key material is ever stored. The consequence:
identical passwords produce unrelated ciphertext, and a wrong password cannot partially decrypt.

## Cleanup after the demo

```bash
cd ~ && rm -rf ~/demo && rm -f ~/powershell.ps1
key --remove          # if you installed into ~/.0xPo11/venv just for the demo
```
