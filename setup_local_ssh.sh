#!/usr/bin/env bash
# setup_local_ssh.sh - create a local SSH target on 127.0.0.1 for "remote"
# fe --host demos. This is a lab-only convenience script.

set -euo pipefail

PORT="${PORT:-2222}"
SSH_DIR="${SSH_DIR:-/tmp/ssh}"
SSH_USER="${SSH_USER:-$(id -un)}"
CONFIG_FILE="${HOME}/.ssh/config"
BACKUP_FILE="${HOME}/.ssh/config.bak"

mkdir -p \
  "$SSH_DIR/home" \
  "$SSH_DIR/run" \
  "$SSH_DIR/etc" \
  "$HOME/.ssh"

chmod 700 "$HOME/.ssh"

HOST_KEY="$SSH_DIR/hostkey"
USER_KEY="$SSH_DIR/userkey"
AUTH_KEYS="$SSH_DIR/authorized_keys"
PID_FILE="$SSH_DIR/sshd.pid"
SSHD_CONFIG="$SSH_DIR/sshd_config"

if [[ ! -s "$HOST_KEY" ]]; then
  ssh-keygen -q -t ed25519 -N "" -f "$HOST_KEY"
fi

if [[ ! -s "$USER_KEY" ]]; then
  ssh-keygen -q -t ed25519 -N "" -f "$USER_KEY"
fi

chmod 600 "$HOST_KEY" "$USER_KEY"
cp -f "$USER_KEY.pub" "$AUTH_KEYS"
chmod 600 "$AUTH_KEYS"

cat > "$SSHD_CONFIG" <<EOF
Port $PORT
ListenAddress 127.0.0.1
HostKey $HOST_KEY
PidFile $PID_FILE
UsePAM no
PasswordAuthentication yes
PubkeyAuthentication yes
AuthorizedKeysFile $AUTH_KEYS
StrictModes no
PermitRootLogin no
EOF

# Stop any previous run on the lab port.
if [[ -f "$PID_FILE" ]]; then
  kill "$(cat "$PID_FILE" 2>/dev/null)" 2>/dev/null || true
  rm -f "$PID_FILE"
fi
pkill -f "sshd -f $SSHD_CONFIG" 2>/dev/null || true

/usr/sbin/sshd -t -f "$SSHD_CONFIG"

# Preserve an ordinary client config exactly once before switching to the lab target.
if [[ -f "$CONFIG_FILE" && ! -e "$BACKUP_FILE" ]]; then
  cp "$CONFIG_FILE" "$BACKUP_FILE"
fi

cat > "$CONFIG_FILE" <<EOF
Host 127.0.0.1
    Port $PORT
    User $SSH_USER
    IdentityFile $USER_KEY
    IdentitiesOnly yes
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
EOF

/usr/sbin/sshd -f "$SSHD_CONFIG"

for _ in $(seq 1 20); do
  if ssh -o BatchMode=yes -o ConnectTimeout=1 127.0.0.1 'echo ssh-ok' >/dev/null 2>&1; then
    echo "[+] SSH target ready at 127.0.0.1:$PORT"
    echo "[i] SSH key: $USER_KEY"
    echo "[i] Client config: $CONFIG_FILE"
    if [[ -e "$BACKUP_FILE" ]]; then
      echo "[i] Restore with: mv \"$BACKUP_FILE\" \"$CONFIG_FILE\""
    fi
    exit 0
  fi
  sleep 0.25
done

echo "[x] Failed to reach the SSH target." >&2
exit 1
EOF