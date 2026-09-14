#!/bin/bash
# installer for 0xPo11

# colors
blue='\033[0;34m'
green='\033[0;32m'
red='\033[0;31m'
yellow='\033[0;33m'
cyan='\033[0;36m'
reset='\033[0m'

install_zeropo11() {
    echo -e "${cyan}[*] Installing 0xPo11...${reset}"

    # check if already installed
    if [ -d "$HOME/.0xPo11" ]; then
        read -r -p "This will copy 0xPo11 to your home directory. If you already had 0xPo11 installed, this will reinstall it. Would you like to continue? [Y/n]" input
        case $input in
            [yY][eE][sS]|[yY]|'')
                echo -e "${green}[+] Reinstalling 0xPo11...${reset}"
                rm -rf "$HOME/.0xPo11"
                ;;
            *)
                echo -e "${red}[-] Installation cancelled.${reset}"
                exit 1
                ;;
        esac
    fi

    # copy to home directory
    cp -r "$(pwd)" "$HOME/.0xPo11"

    # check for bash
    if [ -n "$BASH_VERSION" ]; then
        if ! grep -q "0xPO11_PATH" "$HOME/.bashrc" 2>/dev/null; then
            echo "" >> "$HOME/.bashrc"
            echo "# 0xPo11" >> "$HOME/.bashrc"
            echo "export 0xPO11_PATH=\"~/.0xPo11\"" >> "$HOME/.bashrc"
            echo "alias key=\"python3 ~/.0xPo11/main.py\"" >> "$HOME/.bashrc"
        fi
    fi

    # check for zsh
    if [ -n "$ZSH_VERSION" ]; then
        if ! grep -q "0xPO11_PATH" "$HOME/.zshrc" 2>/dev/null; then
            echo "" >> "$HOME/.zshrc"
            echo "# 0xPo11" >> "$HOME/.zshrc"
            echo "export 0xPO11_PATH=\"~/.0xPo11\"" >> "$HOME/.zshrc"
            echo "alias key=\"python3 ~/.0xPo11/main.py\"" >> "$HOME/.zshrc"
        fi
    fi

    echo -e "${green}[+] 0xPo11 installed successfully!${reset}"
    echo -e "${cyan}[+] Type 'key' in a new terminal to launch 0xPo11${reset}"
}

# run installer
install_zeropo11
