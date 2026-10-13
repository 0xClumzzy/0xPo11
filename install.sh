#!/bin/bash
# installer for 0xPo11 (dedicated venv + pip, no system packages touched)

# colors
blue='\033[0;34m'
green='\033[0;32m'
red='\033[0;31m'
yellow='\033[0;33m'
cyan='\033[0;36m'
reset='\033[0m'

# venv location (override with: ZEROPO11_VENV=/some/path ./install.sh)
VENV_DIR="${ZEROPO11_VENV:-$HOME/.0xPo11/venv}"
BIN_DIR="$HOME/.local/bin"

# tracks whether we appended $BIN_DIR to any rc file
PATH_EXTENDED=0

# Strip legacy copy-based install lines (alias key="python3 ~/.0xPo11/main.py")
# so the venv's `key` entry point is the only `key` on PATH.
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

# Make sure ~/.local/bin is on PATH; append an export line to rc files if not.
ensure_local_bin_on_path() {
    # already on PATH -> nothing to do
    case ":$PATH:" in
        *":$BIN_DIR:"*) return 0 ;;
    esac

    for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
        [ -f "$rc" ] || continue
        if grep -qF "$BIN_DIR" "$rc" 2>/dev/null; then
            continue
        fi
        {
            echo ""
            echo "# 0xPo11 (added by install.sh)"
            echo 'export PATH="$HOME/.local/bin:$PATH"'
        } >> "$rc"
        echo -e "${yellow}    Added $BIN_DIR to PATH in $rc${reset}"
        PATH_EXTENDED=1
    done
}

install_zeropo11() {
    echo -e "${cyan}[*] Installing 0xPo11 into a dedicated venv...${reset}"

    # cd to repo root so the build picks up pyproject.toml
    cd "$(dirname "$0")" || { echo -e "${red}[-] Could not enter repo root${reset}"; exit 1; }

    # need python3 (>= 3.10)
    if ! command -v python3 >/dev/null 2>&1; then
        echo -e "${red}[-] python3 not found. Install Python 3.10+ and rerun.${reset}"
        exit 1
    fi

    # warn about a legacy copy-based install so nothing surprising happens
    if [ -d "$HOME/.0xPo11" ] && [ ! -d "$VENV_DIR" ]; then
        echo -e "${yellow}[!] Found $HOME/.0xPo11 from an older copy-based install.${reset}"
        echo -e "${yellow}    Your payloads in $HOME/.0xPo11/resources/payloads (if any) are kept.${reset}"
        echo -e "${yellow}    The old 'key' alias will be removed below so the venv 'key' wins.${reset}"
    fi

    # (re)create the venv
    echo -e "${cyan}[*] Creating venv at $VENV_DIR${reset}"
    if ! python3 -m venv "$VENV_DIR"; then
        echo -e "${red}[-] Could not create venv.${reset}"
        echo -e "${yellow}    Debian/Ubuntu: sudo apt install python3-venv${reset}"
        exit 1
    fi

    # upgrade pip best-effort (quiet, never fatal)
    "$VENV_DIR/bin/python" -m pip install -q --upgrade pip 2>/dev/null || true

    # install the project (deps included) + the `key` console script
    if ! "$VENV_DIR/bin/python" -m pip install .; then
        echo -e "${red}[-] pip install failed inside the venv${reset}"
        exit 1
    fi

    # expose `key` on PATH via a symlink into the venv
    mkdir -p "$BIN_DIR" || { echo -e "${red}[-] Could not create $BIN_DIR${reset}"; exit 1; }
    ln -sf "$VENV_DIR/bin/key" "$BIN_DIR/key"
    ensure_local_bin_on_path

    # drop the legacy alias/export lines from bash and zsh rc files
    cleanup_legacy_alias "$HOME/.bashrc"
    cleanup_legacy_alias "$HOME/.zshrc"

    echo -e "${green}[+] 0xPo11 installed into $VENV_DIR${reset}"
    echo -e "${green}[+] 'key' command: $BIN_DIR/key -> $VENV_DIR/bin/key${reset}"
    echo -e "${cyan}[+] Optional ciphers (pix/ct/blowfish/twofish):${reset}"
    echo -e "${cyan}    $VENV_DIR/bin/pip install '0xPo11[full]'${reset}"
    if [ "$PATH_EXTENDED" = "1" ]; then
        echo -e "${cyan}[+] Restart your terminal (or run: export PATH=\"$BIN_DIR:\$PATH\")${reset}"
        echo -e "${cyan}    then type 'key' to launch 0xPo11${reset}"
    else
        echo -e "${cyan}[+] Type 'key' in a new terminal to launch 0xPo11${reset}"
    echo -e "${cyan}    then run cipher commands directly (no 'key' prefix inside the keyconsole)${reset}"
    fi
}

# run installer
install_zeropo11
