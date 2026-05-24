#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$HOME/Qubes"
ARCHIVE="$BASE_DIR/d2wc.tgz"
WORKDIR="$BASE_DIR/d2wc"
VM="work"

D2WC_BIN="$HOME/.local/bin/d2wc"
DEVILSPIE2_DIR="$HOME/.config/devilspie2"
D2WC_CONFIG="$DEVILSPIE2_DIR/d2wc.lua"

cd "$BASE_DIR"

rm -rf -- "$WORKDIR"

qvm-run --pass-io "$VM" 'cat /tmp/d2wc.tgz' > "$ARCHIVE"

tar xzf "$ARCHIVE" -C "$BASE_DIR"

if [ ! -f "$WORKDIR/pyproject.toml" ]; then
  echo "ERROR: expected $WORKDIR/pyproject.toml after extracting archive" >&2
  exit 1
fi

if [ ! -f "$WORKDIR/src/d2wc.lua" ]; then
  echo "ERROR: expected $WORKDIR/src/d2wc.lua after extracting archive" >&2
  exit 1
fi

mkdir -p -- "$DEVILSPIE2_DIR"

if [ -e "$D2WC_CONFIG" ]; then
  echo "Keeping existing config: $D2WC_CONFIG"
else
  cp -- "$WORKDIR/src/d2wc.lua" "$D2WC_CONFIG"
  echo "Created config: $D2WC_CONFIG"
fi

if python3 -m pip show d2wc >/dev/null 2>&1; then
  python3 -m pip uninstall -y d2wc
fi

rm -f -- "$D2WC_BIN"

cd "$WORKDIR"

python3 -m pip install \
  --user \
  --no-index \
  --no-build-isolation \
  --no-deps \
  --force-reinstall \
  --no-warn-script-location \
  .

if [ ! -x "$D2WC_BIN" ]; then
  echo "ERROR: expected executable $D2WC_BIN after install" >&2
  exit 1
fi

cd "$BASE_DIR"

python3 -c 'import d2wc; print("Using d2wc from:", d2wc.__file__)'

"$D2WC_BIN" configure
