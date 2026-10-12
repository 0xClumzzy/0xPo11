#!/bin/bash
# updater for 0xPo11 (pip-based)

echo "[*] Updating 0xPo11..."

# build in a temp dir; never clobber a local working copy
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

if ! git clone --quiet https://github.com/0xClumzzy/0xPo11 "$TMP_DIR/0xPo11"; then
    echo "[-] git clone failed"
    exit 1
fi

cd "$TMP_DIR/0xPo11" || exit 1

# reuse the pip-based installer; PYTHON is inherited when set
bash install.sh

echo "[+] 0xPo11 updated successfully!"