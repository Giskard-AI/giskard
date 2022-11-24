pip="${1:-pip}"
rm -f /tmp/giskard*whl* || true
wget https://nightly.link/Giskard-AI/giskard-client/workflows/install-test/main/giskard-dev-3.7.whl.zip -P /tmp
unzip -o /tmp/giskard-dev-3.7.whl.zip -d /tmp
$pip install --upgrade "$(ls /tmp/giskard*whl)"
rm -f /tmp/giskard*whl*