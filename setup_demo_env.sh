#!/usr/bin/env bash
#
# 0xPo11 Demo Environment Setup
#
# Builds a safe, disposable lab under /tmp/0xpo11-lab (override with --root)
# containing sample "victim" files for demonstrating the 0xPo11 ransomware
# simulation CLI and the web control panel. The script never encrypts or
# deletes anything outside the lab root, and it always starts from a clean
# slate so repeated demos behave identically.
#
# SIMULATION ONLY. Authorized lab systems only.
#
# Usage:
#   ./setup_demo_env.sh               build lab, print simulation parameters
#   ./setup_demo_env.sh --cleanup     remove the lab and exit
#   ./setup_demo_env.sh --root DIR    use a different lab root
#   ./setup_demo_env.sh --no-color    plain output (auto-off when piped)

set -euo pipefail

LAB_ROOT="${XPO11_LAB_ROOT:-/tmp/0xpo11-lab}"
MODE="setup"
COLOR="auto"

usage() {
  cat <<'EOF'
0xPo11 demo environment setup

Usage: ./setup_demo_env.sh [options]

Options:
  -r, --root DIR     Lab root directory (default: /tmp/0xpo11-lab)
  -c, --cleanup      Remove the lab directory and exit
  -n, --no-color     Disable colored output
  -h, --help         Show this help

Environment:
  XPO11_LAB_ROOT     Alternative to --root
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -r|--root)     LAB_ROOT="$2"; shift 2 ;;
    -c|--cleanup)  MODE="cleanup"; shift ;;
    -n|--no-color) COLOR="never"; shift ;;
    -h|--help)     usage; exit 0 ;;
    *) printf 'Unknown option: %s\n\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$LAB_ROOT" || "$LAB_ROOT" == "/" ]]; then
  printf 'Refusing unsafe lab root: %q\n' "$LAB_ROOT" >&2
  exit 2
fi

# ---------- colors (auto-off when piped) ----------
if [[ "$COLOR" == "never" || ! -t 1 ]]; then
  BOLD=''; DIM=''; RED=''; GREEN=''; CYAN=''; YELLOW=''; NC=''
else
  BOLD=$'\033[1m'; DIM=$'\033[2m'; RED=$'\033[0;31m'
  GREEN=$'\033[0;32m'; CYAN=$'\033[0;36m'; YELLOW=$'\033[1;33m'; NC=$'\033[0m'
fi

info() { printf '%s[* ]%s %s\n' "$CYAN" "$NC" "$*"; }
ok()   { printf '%s[+ ]%s %s\n' "$GREEN" "$NC" "$*"; }
warn() { printf '%s[! ]%s %s\n' "$YELLOW" "$NC" "$*"; }
fail() { printf '%s[x ]%s %s\n' "$RED" "$NC" "$*" >&2; }

TARGET_DIR="$LAB_ROOT/target"
OUTPUT_DIR="$LAB_ROOT/output"

# ---------- cleanup mode ----------
if [[ "$MODE" == "cleanup" ]]; then
  if [[ -d "$LAB_ROOT" ]]; then
    rm -rf "$LAB_ROOT"
    ok "Removed $LAB_ROOT"
  else
    info "Nothing to remove: $LAB_ROOT does not exist."
  fi
  exit 0
fi

# ---------- aligned box helpers (62-column interior) ----------
BOX_W=62
EQ="$(printf '═%.0s' $(seq 1 "$BOX_W"))"
rule_top() { printf '%s╔%s╗%s\n' "$BOLD" "$EQ" "$NC"; }
rule_mid() { printf '%s╠%s╣%s\n' "$BOLD" "$EQ" "$NC"; }
rule_bot() { printf '%s╚%s╝%s\n' "$BOLD" "$EQ" "$NC"; }
box_line() { printf '%s║ %-61s║%s\n' "$1" "$2" "$NC"; }           # box_line <color> <text>
shrink() {                                                         # shrink <value> <max>: keep the tail
  local v="$1" max="$2"
  if (( ${#v} > max )); then printf '...%s' "${v: -$((max-3))}"; else printf '%s' "$v"; fi
}
box_row() {                                                        # box_row <label> <value> [value-color]
  local label="$1" value="$2" color="${3:-$CYAN}" padded
  printf -v padded '%-32s' "$(shrink "$value" 32)"
  printf '%s║%s %-27s %s%s%s %s║%s\n' "$BOLD" "$NC" "$label" "$color" "$padded" "$NC" "$BOLD" "$NC"
}
dots() {                                                           # label + dots, padded to 27
  local s="$1" n
  n=$(( 27 - ${#s} ))
  printf '%s' "$s"
  (( n > 0 )) && printf '%.0s.' $(seq 1 "$n")
  return 0
}

# ---------- build the lab ----------
echo
info "Building 0xPo11 demo environment in $LAB_ROOT"

rm -rf "$LAB_ROOT"
mkdir -p "$TARGET_DIR" "$OUTPUT_DIR" "$TARGET_DIR/Documents"
chmod 700 "$LAB_ROOT" "$TARGET_DIR" "$OUTPUT_DIR" "$TARGET_DIR/Documents"

echo "Q3 revenue projection: \$12.4M (CONFIDENTIAL)"                > "$TARGET_DIR/finance_q3.xlsx"
echo "Customer list: acme@example.com, globex@example.com"         > "$TARGET_DIR/customers.csv"
echo "HR payroll dump: emp_001 \$98k, emp_042 \$145k"              > "$TARGET_DIR/payroll.hr"
echo "Database connection string: postgres://admin:S3cret@db:5432" > "$TARGET_DIR/db.env"
echo "Log entry [2026-10-16] User lemonx accessed /etc/shadow"     > "$TARGET_DIR/auth.log"
echo "fake-payload-data-for-demo"                                  > "$TARGET_DIR/payload.bin"
echo "Board minutes: budget approved, no public disclosure yet"    > "$TARGET_DIR/Documents/board_minutes.txt"
cat > "$TARGET_DIR/victims.db" <<'EOF'
-- 0xPo11 simulated exfiltrated database (demo data only)
TABLE employees (id INTEGER, name TEXT, email TEXT, salary INTEGER);
INSERT INTO employees VALUES (1,'A. Example','a@example.com',95000);
INSERT INTO employees VALUES (2,'B. Test','b@example.com',110000);
INSERT INTO employees VALUES (3,'C. Demo','c@example.com',87500);
TABLE credentials (service TEXT, username TEXT, password_hash TEXT);
INSERT INTO credentials VALUES ('vpn','svc_vpn','a1b2c3d4e5f6');
INSERT INTO credentials VALUES ('aws','admin','f6e5d4c3b2a1');
EOF

ok "Created $(find "$TARGET_DIR" -type f | wc -l) sample files + victims.db"

# ---------- verify local SSH lab ----------
SSH_PID_FILE="/tmp/ssh/sshd.pid"
if [[ -f "$SSH_PID_FILE" ]] && kill -0 "$(cat "$SSH_PID_FILE")" 2>/dev/null; then
  ok "Local SSH lab running on 127.0.0.1:2222 (pid $(cat "$SSH_PID_FILE"))"
else
  warn "Local SSH lab does not appear to be running."
  warn "Start it first with: ./setup_local_ssh.sh"
fi

# ---------- demo command card ----------
cat > "$LAB_ROOT/DEMO_COMMANDS.md" <<EOF
# 0xPo11 Demo Command Card

Lab root: \`$LAB_ROOT\`

## 0. Reset the lab

\`\`\`bash
./setup_demo_env.sh            # rebuild a clean lab
./setup_demo_env.sh --cleanup  # remove the lab entirely
\`\`\`

## 1. Start the control panel

\`\`\`bash
python3 control_panel.py
# open http://127.0.0.1:8765/
\`\`\`

## 2. Encrypt — Remote Host view (directory sweep)

| Field            | Value                          |
| ---------------- | ------------------------------ |
| Host             | \`127.0.0.1\`                    |
| Remote input     | \`$TARGET_DIR\` |
| Local output     | \`$OUTPUT_DIR/encrypted\` (ignored for sweeps) |
| Password         | \`hunter2\`                      |
| Timeout          | \`30\`                           |
| Direction        | \`encrypt remote→local\`         |
| --local-in       | [x] checked                    |
| --local-out      | [ ] unchecked                  |
| Drop ransom note | [x] checked                    |
| Note template    | \`press\`                        |
| Remote note path | \`$LAB_ROOT/NOTE.txt\` |

Every file under \`target/\` becomes \`<name>.enc\` beside the original, then
the dashboard cats the dropped note back from the remote host.

Shell equivalent:

\`\`\`bash
key fe -e --host 127.0.0.1 \\
    -i $TARGET_DIR -k hunter2 --timeout 30 --local-in \\
    --drop-note press --note-out $LAB_ROOT/NOTE.txt
\`\`\`

## 3. Decrypt one file (recovery proof)

| Field         | Value                          |
| ------------- | ------------------------------ |
| Host          | \`127.0.0.1\`                    |
| Remote input  | \`$TARGET_DIR/victims.db.enc\` |
| Local output  | \`$OUTPUT_DIR/victims.db\`    |
| Password      | \`hunter2\`                      |
| Timeout       | \`30\`                           |
| Direction     | \`decrypt local→remote\`         |
| --local-in    | [ ] unchecked                  |
| --local-out   | [x] checked                    |

Shell equivalent:

\`\`\`bash
key fe -d --host 127.0.0.1 \\
    -i $TARGET_DIR/victims.db.enc -o $OUTPUT_DIR/victims.db \\
    -k hunter2 --timeout 30 --local-out

diff $TARGET_DIR/victims.db $OUTPUT_DIR/victims.db   # identical => recovery works
\`\`\`

## 4. Wrong password (fails clean)

Same as step 3, but use Password \`wrongpass\` and Local output
\`$OUTPUT_DIR/bad.db\`. The run exits with an error and writes no plaintext.

## 5. Read the dropped note again

\`\`\`bash
ssh 127.0.0.1 cat $LAB_ROOT/NOTE.txt
\`\`\`
EOF

ok "Command card written to $LAB_ROOT/DEMO_COMMANDS.md"

# ---------- display simulation parameters ----------
echo
rule_top
box_line "$BOLD" "0xPo11 SIMULATION PARAMETERS"
rule_mid
box_line "$BOLD" "ENCRYPT - Remote Host view (directory sweep)"
box_row "$(dots Host)"                "127.0.0.1"
box_row "$(dots 'Remote input')"      "$TARGET_DIR"
box_row "$(dots 'Local output')"      "$OUTPUT_DIR/encrypted"
box_row "$(dots Password)"            "hunter2"
box_row "$(dots 'Timeout seconds')"   "30"
box_row "$(dots Direction)"           "encrypt remote -> local"
box_row "$(dots --local-in)"          "[x] checked"   "$GREEN"
box_row "$(dots --local-out)"         "[ ] unchecked" "$DIM"
box_row "$(dots 'Drop ransom note')"  "[x] checked"   "$GREEN"
box_row "$(dots 'Note template')"     "press"
box_row "$(dots 'Remote note path')"  "$LAB_ROOT/NOTE.txt"
box_line "$DIM" ""
box_line "$DIM" "Sweeps ignore the output path: each file is encrypted to"
box_line "$DIM" "<name>.enc right beside the source file."
rule_bot

echo
rule_top
box_line "$BOLD" "DECRYPT - recover one file"
rule_mid
box_row "$(dots Host)"                "127.0.0.1"
box_row "$(dots 'Remote input')"      "$TARGET_DIR/victims.db.enc"
box_row "$(dots 'Local output')"      "$OUTPUT_DIR/victims.db"
box_row "$(dots Password)"            "hunter2"
box_row "$(dots 'Timeout seconds')"   "30"
box_row "$(dots Direction)"           "decrypt local -> remote"
box_row "$(dots --local-in)"          "[ ] unchecked" "$DIM"
box_row "$(dots --local-out)"         "[x] checked"   "$GREEN"
box_line "$DIM" ""
box_line "$DIM" "Then verify: diff $TARGET_DIR/victims.db"
box_line "$DIM" "             $OUTPUT_DIR/victims.db"
rule_bot

echo
info "Shell equivalents:"
printf '  key fe -e --host 127.0.0.1 \\\n'
printf '      -i %s -k hunter2 --timeout 30 --local-in \\\n' "$TARGET_DIR"
printf '      --drop-note press --note-out %s/NOTE.txt\n' "$LAB_ROOT"
printf '  key fe -d --host 127.0.0.1 \\\n'
printf '      -i %s/victims.db.enc -o %s/victims.db \\\n' "$TARGET_DIR" "$OUTPUT_DIR"
printf '      -k hunter2 --timeout 30 --local-out\n'

echo
ok "Demo environment ready."
info "Files under $TARGET_DIR:"
( cd "$TARGET_DIR" && find . -type f | sort | sed 's|^\./|  |' )
echo
warn "Simulation only: encrypt only files inside $LAB_ROOT."
info "Clean up when finished: ./setup_demo_env.sh --cleanup"
