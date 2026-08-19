#!/usr/bin/env bash
# Installs the daemon, poketokenctl, and the plasmoid into the user's home.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
app="$HOME/.local/share/poketokenbar/app"
venv="$HOME/.local/share/poketokenbar/venv"

echo "==> installing python package to $app"
mkdir -p "$app/poketokenbar"
rsync -a --delete "$here/poketokenbar/" "$app/poketokenbar/"

echo "==> creating venv at $venv"
[ -d "$venv" ] || python3 -m venv "$venv"
"$venv/bin/pip" install -q --upgrade pip
"$venv/bin/pip" install -q orjson || echo "    orjson unavailable; falling back to json"

echo "==> installing poketokenctl"
mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/poketokenctl" <<EOF
#!/usr/bin/env bash
PYTHONPATH="$app" exec "$venv/bin/python" -m poketokenbar.ctl "\$@"
EOF
chmod +x "$HOME/.local/bin/poketokenctl"

echo "==> installing plasmoid"
plasmoid_dir="$HOME/.local/share/plasma/plasmoids/org.kde.plasma.poketokenbar"
mkdir -p "$plasmoid_dir"
rsync -a --delete "$here/plasmoid/org.kde.plasma.poketokenbar/" "$plasmoid_dir/"

echo "==> installing systemd unit"
mkdir -p "$HOME/.config/systemd/user"
install -m644 "$here/systemd/poketokend.service" "$HOME/.config/systemd/user/"
systemctl --user daemon-reload
systemctl --user enable --now poketokend.service

echo "==> done. check: systemctl --user status poketokend"
