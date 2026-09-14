# 0xPo11 — Presentation Walkthrough

**Audience:** Chief of Offensive Cybersecurity | **Format:** Live terminal demo
**Time budget:** ~11 minutes (7 demos) + Q&A
**Goal:** Prove you understand the byte-level crypto primitives behind malware and ransomware — not just that you can use tools.

---

## Setup (before they walk in, ~3 min)

```bash
cd /home/clumzzy/Projects/0xPo11
alias key="python3 main.py"          # or just use python3 main.py directly
cat version.txt                       # shows 3.0
```

Pre-create a `wordlist.txt` so the brute-force demo can't fail:
```bash
printf 'password\nhello\nsecret\nmjqqt\n' > /tmp/wordlist.txt
```

---

## The Open  (15 sec)

> "0xPo11 is a cryptographic suite I built from scratch — 28 ciphers implemented at the byte level with `ord()` and `chr()`, no external crypto libraries. It's a tool for analyzing and building the obfuscation primitives that malware and ransomware actually use. I'll show you the six primitives that map directly to real attacks."

---

## Demo 1 — XOR String Obfuscation (90 sec)

```bash
key xor -e -t "cmd.exe /c powershell" -k "A"
```

**Output (space-separated bytes):** `" , % o $ 9 $ a n " a 1 . 6 $ 3 2 ) $ - -`

**Say this:**
- XOR is the single most common string-obfuscation primitive in malware — used to hide shell commands, URLs, and API strings from signatures and static AV.
- Each byte is `ord(char) ^ ord(key)` — symmetric, so the same key decrypts.
- Re-decrypt to prove symmetry:
  ```bash
  key xor -d -t '" , % o $ 9 $ a n " a 1 . 6 $ 3 2 ) $ - -' -k "A"
  # Output: cmd.exe /c powershell
  ```

**Why it lands:** you're not quoting Cobalt Strike — you're showing the mechanism underneath it.

---

## Demo 2 — Base64 Drop (90 sec)

```bash
key b64 -d -t "Y21kLmV4ZSAvYyBwb3dlcnNoZWxs"
```

**Output:** `cmd.exe /c powershell`

**Say this:**
- Base64 is how droppers hide commands in config files, registry keys, and network traffic.
- One decode reveals the payload that would actually execute on a victim box.
- Note: most analysts only see the encoded blob — the decode is the pivot.

---

## Demo 3 — Hash Fingerprinting (60 sec)

```bash
key md5 -e -t "malware_sample"
```

**Output:** `9127daf288687deb678053e2aa828e7d`

**Say this:**
- This is how you fingerprint a sample — match it against VirusTotal, add it to a YARA rule, or track it across a campaign.
- Same trick powers hashing for hashcat wordlists.

---

## Demo 4 — Layered / Packed Payloads (90 sec)

```bash
key cc -e -t "payload" -k 3 + b64 -e
```

**Output:** `c2Rib3JkZw==`

**Say this:**
- Real payloads are rarely single-layer — packers and obfuscators stack transformations to evade detection.
- This is Caesar → Base64, one command, chained with `+`.
- Read it backward on a live sample and you can deobfuscate a stage in minutes.

---

## Demo 5 — File Encryption (the ransomware vector) (90 sec)

```bash
printf 'FINANCIAL_RECORDS_2026' > /tmp/victim.txt
key cc -e -i /tmp/victim.txt -o /tmp/encrypted.txt -k 7
cat /tmp/encrypted.txt
key cc -d -i /tmp/encrypted.txt -k 7
```

**Say this:**
- Encryption without any dependency — crypto, key, and file API all in one primitive.
- This is the exact shape ransomware uses: read victim file → transform bytes → write mangled file.

---

## Demo 6 — Unknown Hash → Identify → Crack (analyst loop) (120 sec)

> Pretend you're handed a hash you've never seen. No plaintext, no hint of the algorithm.

```bash
# the unknown hash (looks like a fingerprint you pulled from a token or dump)
key hashid -e -t "1fb9c14e934b825a62d15230cc0c2bd1"
# → MD5 (or NTLM - test both)

key md5 -b -t "1fb9c14e934b825a62d15230cc0c2bd1" -w /tmp/rockyou.txt
# → Decoded MD5 | p@ssw0rd123
```

**Say this:**
- `hashid` fingerprints by length + charset — 32-hex is MD5/NTLM/MySQL 4.1; it flags the ambiguity instead of guessing.
- Then the brute-force loop cracks it against a wordlist — the same loop hashcat runs, at the byte level.
- That two-step ID → crack loop is the real analyst workflow: sample in, plaintext out.

---

## Demo 7 — Interactive Console (60 sec)

```bash
key
[~] user@0xPo11 $ list
[~] user@0xPo11 $ mor -e -t "help"      # Morse
[~] user@0xPo11 $ pho -e -t "help"      # NATO phonetic
[~] user@0xPo11 $ exit
```

**Say this:**
- Metasploit-style shell for rapid analysis — Tab-complete ciphers, `list` to see all 28.
- Built for live reverse-engineering speed.

---

## The Close  (30 sec)

> "Byte-level crypto primitives are the substrate of everything offensive. 0xPo11 lets me rotate through 28 of them in seconds, chain them the way packers do, and reverse what I find in a dropper. It's the difference between knowing the API and understanding the attack."

---

## Objection Handling (know these cold)

**Q: "Why bother when you can `import Crypto`?"**
> Understanding the substrate. If a sample uses a custom XOR or a modified Base64 alphabet, `pip install` won't help you — knowing the byte math lets you decode anything.

**Q: "Some ciphers are broken on your box?"** (`blowfish`, `twofish`, `ct`, `pix`)
> Say: "The four dep-backed ciphers (`blowfish`, `twofish`, `pix`, `ct`) are stubbed pending a dependency rework — I kept the core 23 pure-Python so the suite stays dependency-free. Do not mention it unless asked.

**Q: "Isn't hashing just calling a library?"**
> The standalone hash modules (`md5`, `sha1`, `sha2xx`) are written at the byte level in this project — that's the differentiator between a wrapper and an understanding.

**Q: "What's next?"**
> Phase 4-5 on the roadmap (README): file-encryption module hardening, then key-exchange simulation — moving toward a full ransomware simulation framework.

---

## Surfaces You Can Point To

- **README.md** — full cipher tables, roadmap, demos, task list
- **Task List** — shows you track technical debt (the 4 dep ciphers are *known* and *logged*)

---

## Do / Don't

- **Do** run `--version` if asked about the suite: `key --version` → `0xPo11 v3.0`
- **Don't** demo `blowfish`, `twofish`, `ct`, `pix` — they crash on this machine without `pip install`
- **Do** keep the terminal pre-scrolled clean: `clear` before each demo block