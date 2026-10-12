#!/bin/bash
# installer for 0xPo11 (pip-based)

# colors
blue='\033[0;34m'
green='\033[0;32m'
red='\033[0;31m'
yellow='\033[0;33m'
cyan='\033[0;36m'
reset='\033[0m'

# Remove the legacy copy-based install lines (alias key="python3 ~/.0xPo11/main.py")
# from a shell rc file, if present. The pip-installed `key` entry point must win.
cleanup_legacy_alias() {
    local rc="$1"
    [ -f "$rc" ] || return 0

    if grep -q '^# 0xPo11$' "$rc" 2>/dev/null; then
        grep -v -e '^# 0xPo11$' \
                 -e '^export 0xPO11_PATH=' \
                 -e '^alias key="python3 ~/.0xPo11/main.py"' "$rc" > "$rc.0xPo11.tmp"
        mv "$rc.0xPo11.tmp" "$rc"
        echo -e "${green}[+] Removed legacy 0xPo11 alias from $rc${reset}"
    fi
}

install_zeropo11() {
    echo -e "${cyan}[*] Installing 0xPo11 via pip...${reset}"

    # cd to repo root so the build picks up pyproject.toml
    cd "$(dirname "$0")" || { echo -e "${red}[-] Could not enter repo root${reset}"; exit 1; }

    # pick a python interpreter (override with PYTHON=/path/to/python)
    local PY="${PYTHON:-$(command -v python3)}"
    if [ -z "$PY" ] || ! command -v "$PY" >/dev/null 2>&1; then
        echo -e "${red}[-] python3 not found. Install Python 3.10+ and rerun.${reset}"
        exit 1
    fi

    # warn about the legacy copy-based install so there is no surprise
    if [ -d "$HOME/.0xPo11" ]; then
        echo -e "${yellow}[!] Found $HOME/.0xPo11 from an older copy-based install.${reset}"
        echo -e "${yellow}    Your payloads in $HOME/.0xPo11/resources/payloads (if any) are kept.${reset}"
        echo -e "${yellow}    The old 'key' alias will be removed below so the pip 'key' wins.${reset}"
    fi

    # install the wheel + `key` console script
    if ! "$PY" -m pip install . ; then
        echo -e "${red}[-] pip install failed.${reset}"
        echo -e "${yellow}    On PEP 668-managed (externally-managed) systems, do either:${reset}"
        echo -e "${yellow}      python3 -m venv ~/.0xPo11-venv && PYTHON=~/.0xPo11-venv/bin/python ./install.sh${reset}"
        echo -e "${yellow}      or: $PY -m pip install --break-system-packages .${reset}"
        exit 1
    fi

    # drop the legacy alias/export lines from bash and zsh rc files
    cleanup_legacy_alias "$HOME/.bashrc"
    cleanup_legacy_alias "$HOME/.zshrc"

    echo -e "${green}[+] 0xPo11 installed successfully!${reset}"
    echo -e "${cyan}[+] Type 'key' in a new terminal to launch 0xPo11${reset}"
    echo -e "${cyan}[+] Optional ciphers (pix/ct/blowfish/twofish): pip install '.[full]'${reset}"
}

# run installer
install_zeropo11