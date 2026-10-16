#!/usr/bin/env bash
#
# 0xPo11 Remote Ransomware Simulation Automation
#
# Interactive wrapper around `key fe --host` for authorized lab/presentation
# use. It streams a target over SSH using the system ssh binary — no remote
# agent, no remote install, nothing left on the far machine besides the
# simulated ciphertext note if requested.
#
# SIMULATION ONLY. Never run against systems you do not own or have written
# authorization to test.

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

fail() { printf '%s[!]%s %s\n' "$RED" "$NC" "$*" >&2; exit 1; }
info() { printf '%s[* ]%s %s\n' "$CYAN" "$NC" "$*"; }
ok()   { printf '%s[+ ]%s %s\n' "$GREEN" "$NC" "$*"; }
warn() { printf '%s[! ]%s %s\n' "$YELLOW" "$NC" "$*"; }

KEY_BIN="$(command -v key || true)"
[[ -x "$KEY_BIN" ]] || fail "key command not found. Install 0xPo11 first."

SSH_CONFIG="${HOME}/.ssh/config"
SSH_CONFIG_BAK="${HOME}/.ssh/config.bak"

cat <<'BANNER'
==============================================
  0xPo11 Remote Ransomware Simulation
  Interactive wrapper for `key fe --host`
  SIMULATION ONLY — authorized lab systems
==============================================
BANNER

echo

# ---------- sanity checks ----------
if grep -q "127.0.0.1:2222" "$SSH_CONFIG" 2>/dev/null; then
  ok "~/.ssh/config references local lab sshd at 127.0.0.1:2222"
elif [[ -f "$SSH_CONFIG_BAK" ]]; then
  warn "~/.ssh/config.bak exists; restore normal config after the demo:"
  warn "  cp $SSH_CONFIG_BAK $SSH_CONFIG"
else
  warn "~/.ssh/config does not reference 127.0.0.1:2222"
  warn "  Run setup_local_ssh.sh first, or confirm your remote host manually."
fi

# ---------- interactive input ----------
read -rp "Remote host alias or address (from ~/.ssh/config or user@host): " REMOTE_HOST
[[ -n "${REMOTE_HOST:-}" ]] || fail "remote host is required"

echo
echo "Mode:"
echo "  1) Encrypt directory (remote sweep)"
echo "  2) Encrypt single file"
echo "  3) Decrypt file"
echo "  4) Drop ransom note only (no encryption)"
read -rp "Select mode [1-4]: " MODE

case "${MODE:-}" in
  1) ACTION="encrypt-dir" ;;
  2) ACTION="encrypt-file" ;;
  3) ACTION="decrypt" ;;
  4) ACTION="drop-note" ;;
  *) fail "invalid mode selected" ;;
esac

read -rp "Input path (remote side unless --local-in is used): " INPUT_PATH
[[ -n "${INPUT_PATH:-}" ]] || fail "input path is required"

read -rp "Output path (remote side unless --local-out is used): " OUTPUT_PATH
[[ -n "${OUTPUT_PATH:-}" ]] || fail "output path is required"

read -rsp "Password for fe encryption/decryption: " PASS
echo
[[ -n "${PASS:-}" ]] || fail "password is required"

read -rp "PBKDF2 iterations [200000]: " ITERS
ITERS="${ITERS:-200000}"

LOCAL_IN=false
LOCAL_OUT=false
DROP_NOTE=false
NOTE_TMPL="press"
NOTE_OUT=""
REMOTE_NOTE_PATH=""

if [[ "$ACTION" != "decrypt" ]]; then
  read -rp "Treat INPUT as local and move it to remote? (--local-in) [y/N]: " ans
  [[ "${ans:-}" =~ ^[Yy]$ ]] && LOCAL_IN=true

  if [[ "$ACTION" != "drop-note" ]]; then
    read -rp "Treat OUTPUT as local result? (--local-out) [y/N]: " ans
    [[ "${ans:-}" =~ ^[Yy]$ ]] && LOCAL_OUT=true
  fi

  read -rp "Drop ransom note automatically? [y/N]: " ans
  if [[ "${ans:-}" =~ ^[Yy]$ ]]; then
    DROP_NOTE=true
    read -rp "Note template [generic/polite/press] (press): " NOTE_TMPL
    NOTE_TMPL="${NOTE_TMPL:-press}"

    # Derive a sensible default remote note path next to the output file.
    REMOTE_NOTE_DIR="$(dirname "$OUTPUT_PATH")"
    read -rp "Remote note path [$REMOTE_NOTE_DIR/NOTE.txt]: " REMOTE_NOTE_PATH
    REMOTE_NOTE_PATH="${REMOTE_NOTE_PATH:-$REMOTE_NOTE_DIR/NOTE.txt}"

    read -rp "Custom local note output path (default next to output file): " NOTE_OUT || true
  fi
fi

# ---------- build command ----------
if [[ "$ACTION" == "decrypt" ]]; then
  CMD=(-d -i "$INPUT_PATH" -o "$OUTPUT_PATH" -k "$PASS" --host "$REMOTE_HOST" -it "$ITERS")
else
  CMD=(-e -i "$INPUT_PATH" -o "$OUTPUT_PATH" -k "$PASS" --host "$REMOTE_HOST" -it "$ITERS")
  $LOCAL_IN   && CMD+=(--local-in)
  $LOCAL_OUT  && CMD+=(--local-out)

  if $DROP_NOTE; then
    CMD+=(--drop-note "$NOTE_TMPL")
    [[ -n "${NOTE_OUT:-}" ]] && CMD+=(--note-out "$NOTE_OUT")
  fi
fi

# ---------- confirmation ----------
echo
info "Constructed command:"
printf '  key %s\n' "${CMD[*]}"
echo

read -rp "Execute now? [y/N]: " CONFIRM
[[ "${CONFIRM:-}" =~ ^[Yy]$ ]] || { info "Aborted."; exit 0; }

# ---------- execute ----------
info "Running simulation on $REMOTE_HOST ..."
OUTPUT=$("$KEY_BIN" "${CMD[@]}" 2>&1) || {
  printf '%s\n' "$OUTPUT"
  fail "remote encryption failed"
}
printf '%s\n' "$OUTPUT"

ok "Remote encryption succeeded."

# ---------- cat remote ransom note if one was dropped ----------
if $DROP_NOTE; then
  echo
  info "Remote ransom note (cat'd from $REMOTE_HOST:$REMOTE_NOTE_PATH):"
  NOTE_OUTPUT=$(ssh "$REMOTE_HOST" "cat '$REMOTE_NOTE_PATH'" 2>&1) || {
    warn "Could not read remote note at $REMOTE_NOTE_PATH"
  }
  printf '%s\n' "$NOTE_OUTPUT"
fi

echo
ok "Simulation complete."
info "Restore normal SSH after presentation (if lab config was applied):"
info "  cp ~/.ssh/config.bak ~/.ssh/config"
