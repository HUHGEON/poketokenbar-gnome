#!/usr/bin/env bash
# Builds installable .plasmoid bundles (plain zips, the format kpackagetool6
# and "Install from local file" in Plasma's widget browser both accept).
#
# For people not on Arch: no build system, no venv, just two files to install.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
out="$here/dist"
mkdir -p "$out"

for pkg in org.kde.plasma.poketokenbar org.kde.plasma.poketokenpet; do
  src="$here/plasmoid/$pkg"
  [ -d "$src" ] || { echo "missing $src" >&2; exit 1; }
  target="$out/$pkg.plasmoid"
  rm -f "$target"
  # Zipped from inside the package so metadata.json sits at the archive root,
  # which is what kpackagetool6 expects.
  (cd "$src" && zip -qr "$target" . -x '*.pyc' '__pycache__/*')
  echo "built $target"
done

cat <<EOF

Install with:
  kpackagetool6 -t Plasma/Applet -i $out/org.kde.plasma.poketokenbar.plasmoid
  kpackagetool6 -t Plasma/Applet -i $out/org.kde.plasma.poketokenpet.plasmoid

Upgrade an existing install with -u instead of -i.

The widgets are only the front end — they render whatever the daemon writes to
~/.local/state/poketokenbar/state.json, so the daemon still has to be installed.
EOF
