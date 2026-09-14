#!/bin/bash
# updater for 0xPo11

echo "[*] Updating 0xPo11..."

# remove old version
rm -rf "$HOME/.0xPo11"

# clone latest
cd /tmp
git clone https://github.com/CosmodiumCS/SkeletonKey
cd SkeletonKey

# install
bash install.sh

echo "[+] 0xPo11 updated successfully!"
