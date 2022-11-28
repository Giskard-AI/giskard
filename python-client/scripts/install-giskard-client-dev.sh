pip="${1:-pip}"
rm -f /tmp/giskard*whl* || true
wget https://nightly.link/Giskard-AI/giskard/workflows/build/main/giskard-dev.whl.zip -P /tmp
unzip -o /tmp/giskard-dev.whl.zip -d /tmp
$pip install --upgrade "$(ls /tmp/giskard*whl)"
rm -f /tmp/giskard*whl*