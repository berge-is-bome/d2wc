#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$HOME/Qubes"
ARCHIVE="$BASE_DIR/d2wc.tgz"
WORKDIR="$BASE_DIR/d2wc"
SOURCE_ARCHIVE="/tmp/d2wc.tgz"

LOCAL_BIN="$HOME/.local/bin"
D2WC_BIN="$LOCAL_BIN/d2wc"
DEVILSPIE2_DIR="$HOME/.config/devilspie2"
D2WC_CONFIG="$DEVILSPIE2_DIR/d2wc.lua"
PATH_BLOCK_START="# >>> d2wc local bin >>>"
PATH_BLOCK_END="# <<< d2wc local bin <<<"

TEST_RUN=0
SOURCE_VM=""

usage() {
  cat <<'USAGE'
install-qubes.sh [--test-run] [<source-vm>] | --help

Install or update d2wc in dom0 from /tmp/d2wc.tgz in a running source VM.

Options:
  --test-run    Select a source VM, copy and validate /tmp/d2wc.tgz, then stop
                before replacing files, installing d2wc, or changing configs.
  -h, --help    Show this help.

With no source VM argument, a zenity chooser is shown when available. The chooser
lists running AppVM and DispVM entries only. If zenity is unavailable, the script
falls back to an interactive command-line prompt.
USAGE
}

parse_args() {
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --test-run)
        TEST_RUN=1
        ;;
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
  if qvm-ls --raw-data --fields NAME,STATE,CLASS >/dev/null 2>&1; then
    qvm-ls --raw-data --fields NAME,STATE,CLASS 2>/dev/null |
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

  tmp_archive="$(mktemp --tmpdir="$BASE_DIR" d2wc.tgz.XXXXXX)"

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
mkdir -p -- "$BASE_DIR"

VM="$(choose_source_vm "$SOURCE_VM")"
copy_archive_from_vm "$VM" "$ARCHIVE"

if [ "$TEST_RUN" -eq 1 ]; then
  echo "Test run successful. Archive copied and validated from VM: $VM"
  echo "No source files, Python packages, or user configs were changed."
  exit 0
fi

cd "$BASE_DIR"

rm -rf -- "$WORKDIR"

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

if python3 -m pip show d2wc >/dev/null 2>&1 || [ -x "$D2WC_BIN" ]; then
  FIRST_INSTALL=0
else
  FIRST_INSTALL=1
fi

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

if [ "$FIRST_INSTALL" -eq 1 ]; then
  echo "First install complete. Launching d2wc."
  "$D2WC_BIN"
else
  echo "Updated d2wc."
  echo "Launch it with: d2wc"
fi
