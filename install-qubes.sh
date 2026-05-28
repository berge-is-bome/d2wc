#!/usr/bin/env bash
set -euo pipefail

CACHEDIR="$HOME/.cache/d2wc"
ARCHIVE="$CACHEDIR/d2wc.tgz"
SOURCE_ROOT="$HOME/.local/share/d2wc/source"
SOURCE_ARCHIVE="/tmp/d2wc.tgz"

LOCAL_BIN="$HOME/.local/bin"
D2WC_BIN="$LOCAL_BIN/d2wc"
MANAGED_DIR="$HOME/.config/d2wc/lua"
DEVILSPIE2_DIR="$HOME/.config/devilspie2"
DEVILSPIE2_ENTRY="$DEVILSPIE2_DIR/d2wc.lua"
DEFAULT_MANAGED_FILENAME="d2wc.lua"
PATH_BLOCK_START="# >>> d2wc local bin >>>"
PATH_BLOCK_END="# <<< d2wc local bin <<<"

SOURCE_VM=""

usage() {
  cat <<'USAGE'
install-qubes.sh [<source-vm>] | --help

Install or update d2wc in dom0 from /tmp/d2wc.tgz in a running source VM.

Options:
  -h, --help    Show this help.

With no source VM argument, a zenity chooser is shown when available. The chooser
lists running AppVM and DispVM entries only. If zenity is unavailable, the script
falls back to an interactive command-line prompt.
USAGE
}

parse_args() {
  while [ "$#" -gt 0 ]; do
    case "$1" in
      -h|--help)
        usage
        exit 0
        ;;
      --)
        shift
        break
        ;;
      -*)
        echo "ERROR: unknown option: $1" >&2
        usage >&2
        exit 2
        ;;
      *)
        if [ -n "$SOURCE_VM" ]; then
          echo "ERROR: only one source VM may be supplied" >&2
          usage >&2
          exit 2
        fi
        SOURCE_VM="$1"
        ;;
    esac
    shift
  done

  if [ "$#" -gt 0 ]; then
    if [ -n "$SOURCE_VM" ]; then
      echo "ERROR: only one source VM may be supplied" >&2
      usage >&2
      exit 2
    fi
    SOURCE_VM="$1"
    shift
  fi

  if [ "$#" -gt 0 ]; then
    echo "ERROR: unexpected extra arguments" >&2
    usage >&2
    exit 2
  fi
}

list_source_vms() {
  if qvm-ls --raw-data >/dev/null 2>&1; then
    qvm-ls --raw-data 2>/dev/null |
      awk -F'|' '
        {
          name=$1
          state=$2
          class=$3
          gsub(/^[ \t]+|[ \t]+$/, "", name)
          gsub(/^[ \t]+|[ \t]+$/, "", state)
          gsub(/^[ \t]+|[ \t]+$/, "", class)
        }
        name != "dom0" && state == "Running" && (class == "AppVM" || class == "DispVM") {
          print name
        }
      ' |
      sort -f
    return
  fi

  qvm-ls 2>/dev/null |
    awk '
      NR > 1 && $1 != "dom0" && $2 == "Running" && ($3 == "AppVM" || $3 == "DispVM") {
        print $1
      }
    ' |
    sort -f
}

is_allowed_source_vm() {
  local vm="$1"

  [ -n "$vm" ] || return 1
  list_source_vms | grep -Fx -- "$vm" >/dev/null 2>&1
}

choose_source_vm_zenity() {
  command -v zenity >/dev/null 2>&1 || return 1
  [ -n "${DISPLAY-}" ] || return 1

  local list
  list="$(list_source_vms)" || return 1
  [ -n "$list" ] || return 2

  printf '%s\n' "$list" | zenity --list --height=420 \
    --title 'd2wc installer' \
    --text "Select the running VM that contains $SOURCE_ARCHIVE" \
    --column 'Running AppVM/DispVM' 2>/dev/null || return 3
}

choose_source_vm() {
  local vm="${1:-}"
  local selection
  local rc

  if [ -n "$vm" ]; then
    if ! is_allowed_source_vm "$vm"; then
      echo "ERROR: source VM must be a running AppVM or DispVM: $vm" >&2
      exit 1
    fi
    printf '%s\n' "$vm"
    return 0
  fi

  if selection="$(choose_source_vm_zenity)"; then
    printf '%s\n' "$selection"
    return 0
  fi

  rc=$?
  if [ "$rc" -eq 3 ]; then
    echo "Cancelled." >&2
    exit 1
  fi

  echo "zenity GUI not available or no running AppVM/DispVM entries found; falling back to interactive prompt." >&2
  read -rp "Running AppVM/DispVM containing $SOURCE_ARCHIVE: " vm

  if ! is_allowed_source_vm "$vm"; then
    echo "ERROR: source VM must be a running AppVM or DispVM: $vm" >&2
    exit 1
  fi

  printf '%s\n' "$vm"
}

validate_archive_file() {
  local archive="$1"
  local listing

  listing="$(mktemp)"
  if ! tar tzf "$archive" > "$listing" 2>/dev/null; then
    rm -f -- "$listing"
    echo "ERROR: copied archive is not a valid gzip tar archive" >&2
    return 1
  fi

  if ! grep -qx 'd2wc/pyproject.toml' "$listing"; then
    rm -f -- "$listing"
    echo "ERROR: archive does not contain d2wc/pyproject.toml" >&2
    return 1
  fi

  if ! grep -qx 'd2wc/src/d2wc.lua' "$listing"; then
    rm -f -- "$listing"
    echo "ERROR: archive does not contain d2wc/src/d2wc.lua" >&2
    return 1
  fi

  rm -f -- "$listing"
}

copy_archive_from_vm() {
  local vm="$1"
  local destination="$2"
  local tmp_archive

  tmp_archive="$(mktemp --tmpdir="$CACHEDIR" d2wc.tgz.XXXXXX)"

  if ! qvm-run --pass-io -- "$vm" 'test -r /tmp/d2wc.tgz && cat /tmp/d2wc.tgz' > "$tmp_archive"; then
    rm -f -- "$tmp_archive"
    echo "ERROR: could not read $SOURCE_ARCHIVE from VM: $vm" >&2
    exit 1
  fi

  if ! validate_archive_file "$tmp_archive"; then
    rm -f -- "$tmp_archive"
    exit 1
  fi

  mv -f -- "$tmp_archive" "$destination"
  echo "Copied and validated archive from $vm: $destination"
}


is_safe_managed_filename() {
  local name="$1"
  [ -n "$name" ] || return 1
  case "$name" in
    *.lua) ;;
    *) return 1 ;;
  esac
  case "$name" in
    */*|*..*) return 1 ;;
  esac
}

is_d2wc_managed_lua_file() {
  local path="$1"
  local source_root="$2"
  [ -f "$path" ] || return 1
  PYTHONPATH="$source_root/src" python3 - "$path" <<'PY'
import sys
from pathlib import Path
from d2wc.core.lua_blocks import ManagedBlockParser
from d2wc.core.validation import validate_managed_blocks

config = Path(sys.argv[1])
try:
    source = config.read_text(encoding="utf-8")
    parsed = ManagedBlockParser().parse(source)
except (OSError, ValueError):
    raise SystemExit(1)
raise SystemExit(0 if validate_managed_blocks(parsed.blocks).ok else 1)
PY
}

choose_available_managed_filename() {
  local preferred="$1"
  local name="$preferred"
  if [ ! -e "$MANAGED_DIR/$name" ]; then
    printf "%s\n" "$name"
    return 0
  fi

  while true; do
    read -rp "Managed config $name exists. Enter alternate .lua filename: " name
    if ! is_safe_managed_filename "$name"; then
      echo "ERROR: filename must be non-empty, end with .lua, and not contain / or .." >&2
      continue
    fi
    if [ -e "$MANAGED_DIR/$name" ]; then
      echo "ERROR: $MANAGED_DIR/$name already exists" >&2
      continue
    fi
    printf "%s\n" "$name"
    return 0
  done
}

migrate_devilspie2_regular_managed_file() {
  local source_root="$1"

  if [ -L "$DEVILSPIE2_ENTRY" ]; then
    return 0
  fi

  if [ ! -f "$DEVILSPIE2_ENTRY" ]; then
    return 0
  fi

  if ! is_d2wc_managed_lua_file "$DEVILSPIE2_ENTRY" "$source_root"; then
    return 0
  fi

  local filename target
  filename="$(choose_available_managed_filename "$DEFAULT_MANAGED_FILENAME")"
  target="$MANAGED_DIR/$filename"
  cp -- "$DEVILSPIE2_ENTRY" "$target"
  echo "Migrated managed Devilspie2 file to: $target"
  MIGRATED_MANAGED_PATH="$target"
}

link_devilspie2_entry_safely() {
  local managed_path="$1"
  mkdir -p -- "$DEVILSPIE2_DIR"

  if [ -L "$DEVILSPIE2_ENTRY" ]; then
    local resolved managed_root
    resolved="$(readlink -f -- "$DEVILSPIE2_ENTRY" || true)"
    managed_root="$(readlink -f -- "$MANAGED_DIR" || true)"
    case "$resolved" in
      "$managed_root"/*) rm -f -- "$DEVILSPIE2_ENTRY" ;;
      *)
        echo "WARNING: leaving unrelated Devilspie2 symlink unchanged: $DEVILSPIE2_ENTRY -> $resolved" >&2
        return 0
        ;;
    esac
  elif [ -e "$DEVILSPIE2_ENTRY" ]; then
    echo "WARNING: leaving existing unmanaged Devilspie2 file unchanged: $DEVILSPIE2_ENTRY" >&2
    return 0
  fi

  ln -s -- "$managed_path" "$DEVILSPIE2_ENTRY"
  echo "Configured Devilspie2 symlink: $DEVILSPIE2_ENTRY -> $managed_path"
}

running_d2wc_processes() {
  local user_id pattern
  user_id="$(id -u)"
  pattern='(^|[ /])d2wc($|[[:space:]])|python[0-9.]*([[:space:]].*)?-m[[:space:]]+d2wc'

  if command -v pgrep >/dev/null 2>&1; then
    pgrep -u "$user_id" -fa "$pattern" || true
    return 0
  fi

  ps -u "$user_id" -o pid=,args= |
    awk '
      /(^|[ \/])d2wc($|[[:space:]])|python[0-9.]*([[:space:]].*)?-m[[:space:]]+d2wc/ {
        print
      }
    '
}

wait_until_d2wc_closed_for_update() {
  local running

  while true; do
    running="$(running_d2wc_processes)"

    if [ -z "$running" ]; then
      return 0
    fi

    echo "WARNING: d2wc appears to be running." >&2
    echo "Close all d2wc configurator windows before updating." >&2
    echo >&2
    echo "Running d2wc process candidates:" >&2
    echo "$running" >&2
    echo >&2

    if [ ! -t 0 ]; then
      echo "ERROR: cannot wait for d2wc to close because stdin is not interactive." >&2
      exit 1
    fi

    read -rp "After closing d2wc, press Enter to continue, or press Ctrl+C to abort. "
  done
}
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

remove_managed_path_block() {
  local config_file="$1"
  local tmp_file

  tmp_file="$(mktemp)"
  awk \
    -v start="$PATH_BLOCK_START" \
    -v end="$PATH_BLOCK_END" \
    '$0 == start { skip = 1; next } $0 == end { skip = 0; next } !skip { print }' \
    "$config_file" > "$tmp_file"
  cat "$tmp_file" > "$config_file"
  rm -f -- "$tmp_file"
}

ensure_bash_local_bin_path() {
  local bashrc="$HOME/.bashrc"

  touch "$bashrc"
  remove_managed_path_block "$bashrc"

  cat >> "$bashrc" <<'EOF_BASHRC'

# >>> d2wc local bin >>>
case ":$PATH:" in
  *":$HOME/.local/bin:"*) ;;
  *) export PATH="$HOME/.local/bin:$PATH" ;;
esac
# <<< d2wc local bin <<<
EOF_BASHRC

  echo "Configured $HOME/.local/bin in: $bashrc"
}

ensure_fish_local_bin_path() {
  local fish_config_dir="$HOME/.config/fish"
  local fish_config="$fish_config_dir/config.fish"

  mkdir -p -- "$fish_config_dir"
  touch "$fish_config"
  remove_managed_path_block "$fish_config"

  cat >> "$fish_config" <<'EOF_FISH'

# >>> d2wc local bin >>>
if type -q fish_add_path
    fish_add_path $HOME/.local/bin
else if not contains $HOME/.local/bin $PATH
    set -gx PATH $HOME/.local/bin $PATH
end
# <<< d2wc local bin <<<
EOF_FISH

  echo "Configured $HOME/.local/bin in: $fish_config"
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
      echo "WARNING: $D2WC_BIN" >&2
      ;;
  esac
}

parse_args "$@"
mkdir -p -- "$CACHEDIR"

VM="$(choose_source_vm "$SOURCE_VM")"
copy_archive_from_vm "$VM" "$ARCHIVE"

SOURCE_PARENT="$HOME/.local/share/d2wc"
mkdir -p -- "$SOURCE_PARENT"
TMP_SOURCE="$(mktemp -d --tmpdir="$SOURCE_PARENT" d2wc-source.XXXXXX)"
trap 'rm -rf -- "$TMP_SOURCE"' EXIT

tar xzf "$ARCHIVE" -C "$TMP_SOURCE"
EXTRACTED="$TMP_SOURCE/d2wc"

if [ ! -f "$EXTRACTED/pyproject.toml" ]; then
  echo "ERROR: expected $EXTRACTED/pyproject.toml after extracting archive" >&2
  exit 1
fi

if [ ! -f "$EXTRACTED/src/d2wc.lua" ]; then
  echo "ERROR: expected $EXTRACTED/src/d2wc.lua after extracting archive" >&2
  exit 1
fi

if python3 -m pip show d2wc >/dev/null 2>&1 || [ -x "$D2WC_BIN" ]; then
  FIRST_INSTALL=0
else
  FIRST_INSTALL=1
fi

if [ "$FIRST_INSTALL" -eq 0 ]; then
  wait_until_d2wc_closed_for_update
fi

mkdir -p -- "$(dirname "$SOURCE_ROOT")"
rm -rf -- "$SOURCE_ROOT"
mkdir -p -- "$(dirname "$SOURCE_ROOT")"
mv -- "$EXTRACTED" "$SOURCE_ROOT"

MIGRATED_MANAGED_PATH=""
mkdir -p -- "$MANAGED_DIR"
if [ "$FIRST_INSTALL" -eq 1 ]; then
  migrate_devilspie2_regular_managed_file "$SOURCE_ROOT"
  if [ -n "$MIGRATED_MANAGED_PATH" ] && [ -f "$DEVILSPIE2_ENTRY" ] && [ ! -L "$DEVILSPIE2_ENTRY" ]; then
    rm -f -- "$DEVILSPIE2_ENTRY"
  fi
fi

if [ -n "$MIGRATED_MANAGED_PATH" ]; then
  MANAGED_PATH="$MIGRATED_MANAGED_PATH"
else
  MANAGED_PATH="$MANAGED_DIR/$DEFAULT_MANAGED_FILENAME"
  if [ ! -e "$MANAGED_PATH" ]; then
    cp -- "$SOURCE_ROOT/src/d2wc.lua" "$MANAGED_PATH"
    echo "Created managed config: $MANAGED_PATH"
  elif [ "$FIRST_INSTALL" -eq 1 ] && ! is_d2wc_managed_lua_file "$MANAGED_PATH" "$SOURCE_ROOT"; then
    alt_name="$(choose_available_managed_filename "$DEFAULT_MANAGED_FILENAME")"
    MANAGED_PATH="$MANAGED_DIR/$alt_name"
    cp -- "$SOURCE_ROOT/src/d2wc.lua" "$MANAGED_PATH"
    echo "Created managed config: $MANAGED_PATH"
  fi
fi

if ! is_d2wc_managed_lua_file "$MANAGED_PATH" "$SOURCE_ROOT"; then
  echo "ERROR: managed config is not a valid d2wc-managed Lua file: $MANAGED_PATH" >&2
  exit 1
fi

link_devilspie2_entry_safely "$MANAGED_PATH"

if python3 -m pip show d2wc >/dev/null 2>&1; then
  python3 -m pip uninstall -y d2wc
fi

rm -f -- "$D2WC_BIN"

cd "$SOURCE_ROOT"
python3 -m pip install --user --no-index --no-build-isolation --no-deps --force-reinstall --no-warn-script-location .

if [ ! -x "$D2WC_BIN" ]; then
  echo "ERROR: expected executable $D2WC_BIN after install" >&2
  exit 1
fi

ensure_local_bin_path_for_user_shell
python3 -c 'import d2wc; print("Using d2wc from:", d2wc.__file__)'

if [ "$FIRST_INSTALL" -eq 1 ]; then
  echo "First install complete. Launching d2wc."
  "$D2WC_BIN"
else
  echo "Updated d2wc."
  echo "Launch it with: d2wc"
fi
