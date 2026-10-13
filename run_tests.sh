#!/bin/bash
# run_tests.sh - automated test runner for 0xPo11
#
# Manages a test virtualenv at .venv/ (gitignored, separate from the install
# venv at ~/.0xPo11/venv), installs the test dependencies, and runs pytest.
# Extra arguments not recognized below are forwarded to pytest verbatim.
#
# Usage:
#   ./run_tests.sh                 # run the whole suite
#   ./run_tests.sh -k xor          # forward any flags to pytest
#   ./run_tests.sh --cov           # run with coverage (term-missing + html)
#   ./run_tests.sh --full          # also install optional cipher deps (Pillow, ...)
#   ./run_tests.sh --rebuild       # wipe the venv and reinstall from scratch
#
# Environment:
#   PYTHON=/path/to/python         # interpreter used to create the venv
#   TEST_VENV=/path/to/venv        # override the test venv location

set -u

# colors
green='\033[0;32m'
red='\033[0;31m'
yellow='\033[0;33m'
cyan='\033[0;36m'
reset='\033[0m'

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="${TEST_VENV:-$REPO_ROOT/.venv}"

COV=0
FULL=0
REBUILD=0
PYTEST_ARGS=()

# split our own flags from pytest's
for arg in "$@"; do
    case "$arg" in
        --cov) COV=1 ;;
        --full) FULL=1 ;;
        --rebuild) REBUILD=1 ;;
        *) PYTEST_ARGS+=("$arg") ;;
    esac
done

fail() {
    echo -e "${red}[-] $1${reset}"
    exit 1
}

# --- pick a python (>= 3.10) -----------------------------------------------
PY="${PYTHON:-python3}"
command -v "$PY" >/dev/null 2>&1 \
    || fail "python3 not found on PATH (override with PYTHON=/path/to/python)"
"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' \
    || fail "Python 3.10+ required (got: $("$PY" -V 2>&1))"

# --- (re)create the test venv ------------------------------------------------
if [ "$REBUILD" = "1" ]; then
    echo -e "${yellow}[!] Rebuilding test venv at $VENV_DIR${reset}"
    rm -rf "$VENV_DIR"
fi

if [ ! -x "$VENV_DIR/bin/python" ]; then
    echo -e "${cyan}[*] Creating test venv at $VENV_DIR${reset}"
    "$PY" -m venv "$VENV_DIR" \
        || fail "Could not create venv (Debian/Ubuntu: sudo apt install python3-venv)"
fi

VENV_PY="$VENV_DIR/bin/python"

# --- install test dependencies ----------------------------------------------
echo -e "${cyan}[*] Installing test dependencies (first run takes a moment)${reset}"
if [ "$FULL" = "1" ]; then
    "$VENV_PY" -m pip install -q "$REPO_ROOT[dev,full]" \
        || fail "pip install failed for the dev/full extras"
else
    "$VENV_PY" -m pip install -q "$REPO_ROOT[dev]" \
        || fail "pip install failed for the dev extra"
fi

# --- run pytest --------------------------------------------------------------
PYTEST_CMD=("$VENV_PY" -m pytest)
if [ "$COV" = "1" ]; then
    "$VENV_PY" -c 'import pytest_cov' 2>/dev/null \
        || "$VENV_PY" -m pip install -q pytest-cov \
        || fail "Could not install pytest-cov"
    PYTEST_CMD+=(--cov=zeropo11 --cov-report=term-missing --cov-report=html)
fi

echo -e "${cyan}[*] Running tests (venv: $VENV_DIR)${reset}"
echo -e "${cyan}---------------------------------------------${reset}"

cd "$REPO_ROOT" || fail "Could not enter repo root"
PYTHONPATH="$REPO_ROOT/src" \
    "${PYTEST_CMD[@]}" ${PYTEST_ARGS[@]+"${PYTEST_ARGS[@]}"}
STATUS=$?

echo -e "${cyan}---------------------------------------------${reset}"
if [ "$STATUS" -eq 0 ]; then
    echo -e "${green}[+] All tests passed${reset}"
    [ "$COV" = "1" ] && echo -e "${cyan}    Coverage report: $REPO_ROOT/htmlcov/index.html${reset}"
else
    echo -e "${red}[-] Tests failed (pytest exit code $STATUS)${reset}"
fi

exit "$STATUS"
