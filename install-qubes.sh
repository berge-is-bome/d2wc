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
from d2wc.core.lua_blocks import ManagedBlockParser, is_d2wc_managed_source
from d2wc.core.validation import validate_managed_blocks

config = Path(sys.argv[1])
try:
    source = config.read_text(encoding="utf-8")
    if not is_d2wc_managed_source(source):
        raise SystemExit(1)
    parsed = ManagedBlockParser().parse(source)
except (OSError, ValueError):
    raise SystemExit(1)
raise SystemExit(0 if validate_managed_blocks(parsed.blocks).ok else 1)
PY
}

refresh_managed_lua_runtime_files() {
  local source_root="$1"

  echo "Refreshing d2wc managed Lua runtime files in: $MANAGED_DIR"
  if ! PYTHONPATH="$source_root/src" python3 -m d2wc.lua_runtime_migrations "$MANAGED_DIR"; then
    echo "ERROR: failed to refresh managed Lua runtime files" >&2
    exit 1
  fi
}

choose_available_managed_filename() {
  local preferred="$1"
  local name="$preferred"
  local stem
  local suffix

  if [ ! -e "$MANAGED_DIR/$name" ]; then
    printf '%s\n' "$name"
    return 0
  fi

  stem="${preferred%.lua}"
  suffix=1
  while [ -e "$MANAGED_DIR/${stem}-${suffix}.lua" ]; do
    suffix=$((suffix + 1))
  done
  printf '%s\n' "${stem}-${suffix}.lua"
}

install_managed_lua_file() {
  local source_root="$1"
  local source_file="$source_root/src/d2wc.lua"
  local active_target="$MANAGED_DIR/$DEFAULT_MANAGED_FILENAME"
  local target
  local chosen_name

  mkdir -p -- "$MANAGED_DIR" "$DEVILSPIE2_DIR"

  if [ -e "$active_target" ] && is_d2wc_managed_lua_file "$active_target" "$source_root"; then
    echo "Managed config already exists: $active_target"
    activate_managed_lua_file "$active_target"
    return 0
  fi

  chosen_name="$(choose_available_managed_filename "$DEFAULT_MANAGED_FILENAME")"
  target="$MANAGED_DIR/$chosen_name"
  cp -- "$source_file" "$target"
  echo "Installed managed config: $target"
  activate_managed_lua_file "$target"
}

activate_managed_lua_file() {
  local target="$1"

  mkdir -p -- "$DEVILSPIE2_DIR"

  if [ -e "$DEVILSPIE2_ENTRY" ] || [ -L "$DEVILSPIE2_ENTRY" ]; then
    if [ -L "$DEVILSPIE2_ENTRY" ] && [ "$(readlink -- "$DEVILSPIE2_ENTRY")" = "$target" ]; then
      echo "Active devilspie2 entry already points to: $target"
      return 0
    fi

    local timestamp
    timestamp="$(date +%Y%m%d-%H%M%S)"
    local backup="$DEVILSPIE2_ENTRY.backup-$timestamp"
    mv -- "$DEVILSPIE2_ENTRY" "$backup"
    echo "Backed up existing devilspie2 entry: $backup"
  fi

  ln -s -- "$target" "$DEVILSPIE2_ENTRY"
  echo "Activated devilspie2 entry symlink: $DEVILSPIE2_ENTRY -> $target"
}

install_python_entrypoint() {
  local source_root="$1"
  mkdir -p -- "$LOCAL_BIN"

  cat > "$D2WC_BIN" <<EOF
#!/usr/bin/env bash
PYTHONPATH="$source_root/src" exec python3 -m d2wc "\$@"
EOF
  chmod 755 "$D2WC_BIN"
  echo "Installed launcher: $D2WC_BIN"
}

ensure_local_bin_on_path() {
  local shell_name
  shell_name="$(basename -- "${SHELL:-}")"

  case "$shell_name" in
    fish)
      ensure_fish_path
      ;;
    bash|zsh)
      ensure_posix_shell_path "$HOME/.profile"
      ;;
    *)
      ensure_posix_shell_path "$HOME/.profile"
      ;;
  esac
}

ensure_fish_path() {
  local config_dir="$HOME/.config/fish"
  local config_file="$config_dir/config.fish"
  mkdir -p -- "$config_dir"

  if [ -f "$config_file" ] && grep -Fqx 'fish_add_path --path "$HOME/.local/bin"' "$config_file"; then
    echo "PATH already configured in: $config_file"
    return 0
  fi

  cat >> "$config_file" <<'EOF'

# >>> d2wc local bin >>>
fish_add_path --path "$HOME/.local/bin"
# <<< d2wc local bin <<<
EOF
  echo "Added ~/.local/bin to PATH in: $config_file"
}

ensure_posix_shell_path() {
  local profile_file="$1"
  touch "$profile_file"

  if grep -Fqx "$PATH_BLOCK_START" "$profile_file"; then
    echo "PATH block already present in: $profile_file"
    return 0
  fi

  cat >> "$profile_file" <<'EOF'

# >>> d2wc local bin >>>
case ":$PATH:" in
  *:"$HOME/.local/bin":*) ;;
  *) PATH="$HOME/.local/bin:$PATH" ;;
esac
export PATH
# <<< d2wc local bin <<<
EOF
  echo "Added ~/.local/bin to PATH in: $profile_file"
}

main() {
  parse_args "$@"
  mkdir -p -- "$CACHEDIR"

  SOURCE_VM="$(choose_source_vm "$SOURCE_VM")"
  copy_archive_from_vm "$SOURCE_VM" "$ARCHIVE"

  rm -rf -- "$SOURCE_ROOT"
  mkdir -p -- "$SOURCE_ROOT"
  tar xzf "$ARCHIVE" -C "$SOURCE_ROOT" --strip-components=1
  echo "Installed source snapshot: $SOURCE_ROOT"

  install_python_entrypoint "$SOURCE_ROOT"
  install_managed_lua_file "$SOURCE_ROOT"
  refresh_managed_lua_runtime_files "$SOURCE_ROOT"
  ensure_local_bin_on_path

  echo "d2wc install/update complete."
  echo "Open a new terminal or refresh your shell PATH, then run: d2wc"
}

main "$@"
