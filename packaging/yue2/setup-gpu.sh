#!/usr/bin/env bash
# Run as root in the existing WSL distribution. Does not install Linux GPU drivers.
set -euo pipefail
if [[ $(id -u) != 0 ]]; then
  echo 'Run this script as root inside WSL.' >&2
  exit 1
fi
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey |
  gpg --batch --yes --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -fsSL https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list |
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  > /etc/apt/sources.list.d/nvidia-container-toolkit.list
apt-get update
apt-get install -y nvidia-container-toolkit=1.19.0-1 nvidia-container-toolkit-base=1.19.0-1 \
  libnvidia-container-tools=1.19.0-1 libnvidia-container1=1.19.0-1
if [[ -f /etc/docker/daemon.json && ! -f /etc/docker/daemon.json.pre-yue2 ]]; then
  cp /etc/docker/daemon.json /etc/docker/daemon.json.pre-yue2
fi
nvidia-ctk runtime configure --runtime=docker
systemctl restart docker
