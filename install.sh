#!/usr/bin/env bash
# Installs the daemon, poketokenctl, and whichever desktop front end fits.
#
# Everything lands under $HOME. Nothing here needs root, and nothing is written
# outside the user's own directories.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
app="$HOME/.local/share/poketokenbar/app"
venv="$HOME/.local/share/poketokenbar/venv"
extension_uuid="poketokenbar@huhgeon.github.io"

# Which front ends to install. Default is "auto": whichever desktop is running,
# falling back to both when that cannot be told (a plain SSH session, say).
ui="${POKETOKENBAR_UI:-auto}"
# Set to skip the systemd bits, which is what the container test does.
no_service="${POKETOKENBAR_NO_SERVICE:-}"

copy_tree() {
  # rsync is not installed everywhere; cp is, and the delete is explicit.
  local src="$1" dest="$2"
  rm -rf "$dest"
  mkdir -p "$dest"
  cp -R "$src/." "$dest/"
}

echo "==> installing python package to $app"
copy_tree "$here/poketokenbar" "$app/poketokenbar"

echo "==> creating venv at $venv"
[ -d "$venv" ] || python3 -m venv "$venv"
"$venv/bin/pip" install -q --upgrade pip
# Optional: roughly twice as fast on a large log corpus, and the code falls
# back to the standard library when it is missing.
"$venv/bin/pip" install -q orjson || echo "    orjson unavailable; falling back to json"

echo "==> installing poketokenctl"
mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/poketokenctl" <<EOF
#!/usr/bin/env bash
PYTHONPATH="$app" exec "$venv/bin/python" -m poketokenbar.ctl "\$@"
EOF
chmod +x "$HOME/.local/bin/poketokenctl"

install_gnome() {
  local dest="$HOME/.local/share/gnome-shell/extensions/$extension_uuid"
  echo "==> installing GNOME Shell extension to $dest"
  copy_tree "$here/gnome-extension/$extension_uuid" "$dest"
  echo "    enable it in the Extensions app, or:"
  echo "      gnome-extensions enable $extension_uuid"
  echo "    on Xorg press Alt+F2 then r to reload the shell; on Wayland log out and back in."
}

install_plasma() {
  echo "==> installing Plasma widgets"
  for pkg in org.kde.plasma.poketokenbar org.kde.plasma.poketokenpet; do
    copy_tree "$here/plasmoid/$pkg" "$HOME/.local/share/plasma/plasmoids/$pkg"
  done
}

case "$ui" in
  gnome) install_gnome ;;
  plasma) install_plasma ;;
  none) echo "==> skipping the desktop front end" ;;
  auto)
    desktop="${XDG_CURRENT_DESKTOP:-}"
    case "$desktop" in
      *GNOME*) install_gnome ;;
      *KDE*) install_plasma ;;
      *)
        echo "==> no desktop detected in XDG_CURRENT_DESKTOP; installing both"
        install_gnome
        install_plasma
        ;;
    esac
    ;;
  *)
    echo "unknown POKETOKENBAR_UI=$ui (expected gnome, plasma, both or none)" >&2
    exit 2
    ;;
esac

if [ -n "$no_service" ]; then
  echo "==> skipping the systemd unit (POKETOKENBAR_NO_SERVICE set)"
  echo "==> done"
  exit 0
fi

echo "==> installing systemd unit"
mkdir -p "$HOME/.config/systemd/user"
install -m644 "$here/systemd/poketokend.service" "$HOME/.config/systemd/user/"
systemctl --user daemon-reload
systemctl --user enable --now poketokend.service

echo "==> done. check: systemctl --user status poketokend"
