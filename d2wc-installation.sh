#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$HOME/Qubes"
ARCHIVE="$BASE_DIR/d2wc.tgz"
WORKDIR="$BASE_DIR/d2wc"
VM="work"

LOCAL_BIN="$HOME/.local/bin"
D2WC_BIN="$LOCAL_BIN/d2wc"
DEVILSPIE2_DIR="$HOME/.config/devilspie2"
D2WC_CONFIG="$DEVILSPIE2_DIR/d2wc.lua"
PATH_BLOCK_START="# >>> d2wc local bin >>>"
PATH_BLOCK_END="# <<< d2wc local bin <<<"

add_local_bin_to_current_path() {
  case ":$PATH:" in
    *":$LOCAL_BIN:"*) ;;
    *) export PATH="$LOCAL_BIN:$PATH" ;;
  esac
}

detect_user_shell() {
  local shell_path="${SHELL:-}"

  if [ -z "$shell_path" ] && command -v getent >/dev/null 2>&1; then
    shell_path="$(getent passwd "$(id -un)" | cut -d: -f7 || true)"
  fi

  basename -- "$shell_path"
}

ensure_bash_local_bin_path() {
  local bashrc="$HOME/.bashrc"

  touch "$bashrc"
  if grep -Fqx "$PATH_BLOCK_START" "$bashrc"; then
    echo "Bash PATH already configured in: $bashrc"
    return
  fi

  cat >> "$bashrc" <<'EOF'

# >>> d2wc local bin >>>
case ":$PATH:" in
  *":$HOME/.local/bin:"*) ;;
  *) export PATH="$HOME/.local/bin:$PATH" ;;
esac
# <<< d2wc local bin <<<
EOF

  echo "Added $HOME/.local/bin to PATH in: $bashrc"
}

ensure_fish_local_bin_path() {
  local fish_config_dir="$HOME/.config/fish"
  local fish_config="$fish_config_dir/config.fish"

  mkdir -p -- "$fish_config_dir"
  touch "$fish_config"
  if grep -Fqx "$PATH_BLOCK_START" "$fish_config"; then
    echo "Fish PATH already configured in: $fish_config"
    return
  fi

  cat >> "$fish_config" <<'EOF'

# >>> d2wc local bin >>>
if type -q fish_add_path
    fish_add_path $HOME/.local/bin
else if not contains $HOME/.local/bin $PATH
    set -gx PATH $HOME/.local/bin $PATH
end
# <<< d2wc local bin <<<
EOF

  echo "Added $HOME/.local/bin to PATH in: $fish_config"
}

ensure_local_bin_path_for_user_shell() {
  local user_shell
  user_shell="$(detect_user_shell)"

  add_local_bin_to_current_path

  case "$user_shell" in
    bash)
      ensure_bash_local_bin_path
      ;;
    fish)
      ensure_fish_local_bin_path
      ;;
    *)
      echo "WARNING: shell '$user_shell' is not handled automatically." >&2
      echo "WARNING: add $HOME/.local/bin to PATH manually, or launch d2wc by full path:" >&2
      echo "WARNING: $D2WC_BIN configure" >&2
      ;;
  esac
}

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

ensure_local_bin_path_for_user_shell

cd "$BASE_DIR"

python3 -c 'import d2wc; print("Using d2wc from:", d2wc.__file__)'

"$D2WC_BIN" configure
