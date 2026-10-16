#!/usr/bin/env bash
#
# 0xPo11 Demo Environment Setup
#
# Creates a safe, disposable lab directory with sample files for demonstrating
# the ransomware simulation CLI and web control panel. Nothing is encrypted
# here — this only prepares the files you will encrypt during the demo.
#
# SIMULATION ONLY. Authorized lab systems only.

set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

LAB_ROOT="/tmp/0xpo11-lab"
TARGET_DIR="$LAB_ROOT/target"
OUTPUT_DIR="$LAB_ROOT/output"

info() { printf '%s[* ]%s %s\n' "$CYAN" "$NC" "$*"; }
ok()   { printf '%s[+ ]%s %s\n' "$GREEN" "$NC" "$*"; }
warn() { printf '%s[! ]%s %s\n' "$YELLOW" "$NC" "$*"; }

echo
info "Creating 0xPo11 demo environment at $LAB_ROOT"

# ---------- directory structure ----------
mkdir -p "$TARGET_DIR" "$OUTPUT_DIR"
chmod 700 "$LAB_ROOT" "$TARGET_DIR" "$OUTPUT_DIR"

# ---------- sample files ----------
info "Creating sample files for encryption..."

echo "Q3 revenue projection: \$12.4M (CONFIDENTIAL)" > "$TARGET_DIR/finance_q3.xlsx"
echo "Customer list: acme@example.com, globex@example.com, soyuz@example.com" > "$TARGET_DIR/customers.csv"
echo "HR payroll dump: emp_001 \$98k, emp_042 \$145k" > "$TARGET_DIR/payroll.hr"
echo "Database connection string: postgres://admin:S3cret@db.internal:5432/prod" > "$TARGET_DIR/db.env"
echo "Log entry [2026-10-16] User lemonx accessed /etc/shadow" > "$TARGET_DIR/auth.log"
echo "fake-payload-data-for-demo" > "$TARGET_DIR/payload.bin"

info "Created $(find "$TARGET_DIR" -type f | wc -l) sample files."

# ---------- victims.db (simulated exfiltrated database) ----------
info "Creating victims.db for ransom-note demonstration..."
cat > "$TARGET_DIR/victims.db" <<'EOF'
-- 0xPo11 simulated exfiltrated database
-- This file is for demonstration only.
TABLE employees (
  id INTEGER PRIMARY KEY,
  name TEXT,
  email TEXT,
  salary INTEGER
);
INSERT INTO employees VALUES (1,'A. Example','a@example.com',95000);
INSERT INTO employees VALUES (2,'B. Test','b@example.com',110000);
INSERT INTO employees VALUES (3,'C. Demo','c@example.com',87500);
TABLE credentials (
  service TEXT,
  username TEXT,
  password_hash TEXT
);
INSERT INTO credentials VALUES ('vpn','svc_vpn','a1b2c3d4e5f6');
INSERT INTO credentials VALUES ('aws','admin','f6e5d4c3b2a1');
EOF

ok "victims.db created."

# ---------- verify SSH lab ----------
SSH_PID_FILE="/tmp/ssh/sshd.pid"
if [[ -f "$SSH_PID_FILE" ]] && kill -0 "$(cat "$SSH_PID_FILE")" 2>/dev/null; then
  ok "Local SSH lab is running on 127.0.0.1:2222 (pid $(cat "$SSH_PID_FILE"))"
else
  warn "Local SSH lab does not appear to be running."
  warn "Start it with: ./setup_local_ssh.sh"
fi

# ---------- demo command card ----------
cat > "$LAB_ROOT/DEMO_COMMANDS.md" <<EOF
# 0xPo11 Demo Command Card

## 1. Verify the lab
\`\`\`bash
ls -la $TARGET_DIR
cat $TARGET_DIR/victims.db
\`\`\`

## 2. Start the control panel (in another terminal)
\`\`\`bash
python3 control_panel.py
# open http://127.0.0.1:8765/
\`\`\`

## 3. Remote directory sweep (via control panel "Remote Host" view)
Host: \`127.0.0.1\`
Remote input: \`$TARGET_DIR\`
Local output: \`$OUTPUT_DIR/encrypted\`
Password: \`hunter2\`
Timeout: \`30\`
Direction: encrypt remote→local
--local-in: [x] checked
--local-out: [ ] unchecked
Drop note: [x] checked
Template: press
Remote note path: \`$LAB_ROOT/NOTE.txt\`

Equivalent shell command:
\`\`\`bash
key fe -e --host 127.0.0.1 -i $TARGET_DIR -o $OUTPUT_DIR/encrypted -k hunter2 --timeout 30 --local-in --drop-note press --note-out $LAB_ROOT/NOTE.txt
\`\`\`

## 4. Decrypt
Host: \`127.0.0.1\`
Remote input: \`$OUTPUT_DIR/encrypted\`
Local output: \`$OUTPUT_DIR/restored\`
Password: \`hunter2\`
Direction: decrypt local→remote
--local-out: [x] checked

## 5. Wrong password (fail clean)
Use the same decrypt fields but password \`wrongpass\`.

## 6. View the dropped note
\`\`\`bash
cat $LAB_ROOT/NOTE.txt
\`\`\`
EOF

ok "Demo command card written to $LAB_ROOT/DEMO_COMMANDS.md"

echo
ok "Demo environment ready."
info "Files in $TARGET_DIR:"
ls -la "$TARGET_DIR"
echo
warn "Remember: this is simulation only. Encrypt only files inside $LAB_ROOT."
info "When finished, clean up with: rm -rf $LAB_ROOT"
