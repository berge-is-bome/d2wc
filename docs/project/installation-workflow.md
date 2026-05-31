# Installation Workflow

`d2wc` currently ships one implemented installer path: the Qubes/dom0 source-archive installer.

For user-facing Qubes install and update steps, see [Install/Update for Qubes](../user/install-qubes.md).

## Current installer paths

Implemented:

1. Qubes/dom0 source-archive installer: `install-qubes.sh`

Future:

1. Fedora package or installer path.
2. Debian package or installer path.
3. Distribution-quality package behavior.

## Qubes/dom0 source-archive installer

The Qubes/dom0 installer is designed for dom0 systems without direct internet access.

The installer receives source from a running source VM that contains:

```text
/tmp/d2wc.tgz
```

The source VM may be supplied as a positional argument. If it is not supplied, the installer tries a `zenity` chooser first and falls back to an interactive command-line prompt when needed.

Only running `AppVM` and `DispVM` entries are accepted as source VMs.

## Archive copy and validation

Before replacing the extracted source tree, the installer copies `/tmp/d2wc.tgz` from the selected source VM into:

```text
~/.cache/d2wc/d2wc.tgz
```

The copied archive is validated before use. If the archive cannot be read, the installer exits before replacing the local source tree.

## Local source installation

After the archive is copied and validated, the installer extracts the source tree under a temporary directory and then installs it as the active local source tree:

```text
~/.local/share/d2wc/source/
```

The Python package is installed into the dom0 user site without using network access:

```bash
python3 -m pip install --user --no-index --no-build-isolation --no-deps --force-reinstall --no-warn-script-location .
```

The installed command is expected at:

```text
~/.local/bin/d2wc
```

## Managed config creation and preservation

The installer creates the managed Lua directory when needed:

```text
~/.config/d2wc/lua/
```

The default managed Lua file is:

```text
~/.config/d2wc/lua/d2wc.lua
```

On first install, if no managed file exists, the installer creates the default managed file from the bundled template:

```text
src/d2wc.lua
```

On update, the installer preserves the active managed file selection when the Devilspie2 integration symlink already points safely into:

```text
~/.config/d2wc/lua/
```

## Legacy managed-file migration

On first install only, if this path exists as a regular file:

```text
~/.config/devilspie2/d2wc.lua
```

and it is already a valid `d2wc` managed Lua file, the installer copies it into:

```text
~/.config/d2wc/lua/
```

The legacy regular file is then replaced by the managed integration symlink only after a successful migration.

Unmanaged regular files at `~/.config/devilspie2/d2wc.lua` are left untouched.

## Managed Lua runtime refresh

After the managed file path is selected, the installer refreshes marked managed Lua files under:

```text
~/.config/d2wc/lua/
```

The runtime migration helper requires the executable managed marker:

```lua
local D2WC_MANAGED = true
```

Files without that marker are skipped.

Runtime refreshes are targeted migrations. They may add missing runtime pieces needed by the current managed Lua runtime, but they must preserve user rules, user comments, spacing, and existing setting values.

## Devilspie2 integration symlink

Devilspie2 reads the active managed file through:

```text
~/.config/devilspie2/d2wc.lua
```

When managed by `d2wc`, that path is a symlink into:

```text
~/.config/d2wc/lua/
```

The installer creates or updates that symlink only when safe.

Safe cases:

1. The path does not exist.
2. The path is already a symlink into `~/.config/d2wc/lua/`.
3. A first-install legacy regular file has been migrated successfully.

Unsafe cases are left unchanged:

1. A regular file that is not a valid `d2wc` managed Lua file.
2. A symlink outside `~/.config/d2wc/lua/`.

## User settings preservation

The installer preserves existing UI settings under:

```text
~/.config/d2wc/settings.json
```

Installer updates must not overwrite user settings such as toast timeout, toast opacity, behavior mode, or active managed Lua setting values.

## Running configurator guard

On update, if one or more `d2wc` process candidates are running, the installer warns the user to close them and waits before continuing.

The update continues only after no running `d2wc` process candidates remain.

If the installer cannot wait because standard input is not interactive, it exits instead of updating while `d2wc` appears to be running.

## Shell path integration

The installer ensures the current shell process can find:

```text
~/.local/bin/d2wc
```

It also updates supported user shell startup files so future shells include `~/.local/bin`.

Current handled shells:

1. Bash: updates `~/.bashrc`.
2. Fish: updates `~/.config/fish/config.fish`.

For unsupported shells, the installer prints a warning and shows the full command path.

## First install and update completion

On first install, the installer launches `d2wc` after setup completes.

On update, the installer reports success and tells the user to launch `d2wc` manually.

## Future installer behavior

Future Fedora and Debian installer paths should preserve the same safety principles:

1. Do not overwrite unrelated Devilspie2 scripts.
2. Keep user-owned managed Lua files under `~/.config/d2wc/lua/`.
3. Keep `~/.config/devilspie2/d2wc.lua` as the Devilspie2-facing integration path.
4. Preserve user settings.
5. Preserve active managed file selection where practical.
6. Run targeted managed Lua runtime migrations instead of rewriting full user files.
7. Validate before replacing files.
8. Back up before guarded writes.
