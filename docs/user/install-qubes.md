# Install/Update for Qubes

This guide is for Qubes users who want to install or update `d2wc` in dom0.

The install flow uses a source VM to clone and archive the repository, then runs the installer in dom0. The source VM can be any running `AppVM` or `DispVM` that contains `/tmp/d2wc.tgz`.

## In the source VM:

1. Clone repository.
2. Create archive.
3. Leave the source VM running until the dom0 installation is finished.

```bash
cd /tmp
git clone git@github.com:berge-is-bome/d2wc.git
git -C d2wc archive --format=tar --prefix=d2wc/ HEAD | gzip > /tmp/d2wc.tgz
```

## In dom0:

4. Copy `install-qubes.sh` from the source VM.
5. Make the script executable.
6. Run the script.
7. Shutdown the source VM when installation is complete.

Replace `<source-vm>` with the running VM that contains `/tmp/d2wc.tgz`.

```bash
qvm-run --pass-io <source-vm> 'cat /tmp/d2wc/install-qubes.sh' > /tmp/install-qubes.sh
chmod 700 /tmp/install-qubes.sh
/tmp/install-qubes.sh <source-vm>
```

The VM argument is optional. If it is omitted, the installer shows a `zenity` chooser when available. The chooser lists running `AppVM` and `DispVM` entries only. If `zenity` is unavailable, the installer falls back to a command-line prompt.

```bash
/tmp/install-qubes.sh
```

## Installer update behavior

The installer copies and validates `/tmp/d2wc.tgz` before replacing the local source tree.

The copied archive is cached under:

```text
~/.cache/d2wc/
```

The extracted local source is stored under:

```text
~/.local/share/d2wc/source/
```

User-owned managed Lua files are stored under:

```text
~/.config/d2wc/lua/
```

The active Devilspie2 integration path is:

```text
~/.config/devilspie2/d2wc.lua
```

When managed by `d2wc`, that path is a symlink to the active managed Lua file under `~/.config/d2wc/lua/`.

On update, the installer preserves the active managed file when `~/.config/devilspie2/d2wc.lua` is already a safe symlink into `~/.config/d2wc/lua/`.

The installer also refreshes marked managed Lua files under `~/.config/d2wc/lua/` with missing runtime code needed by the current bundled managed script. This is a targeted migration, not a full template rewrite. Existing user rules, comments, spacing, and existing toggle values are preserved.

Only files that contain the managed marker are migrated:

```text
d2wc managed
```

Files without that marker are skipped by the migration helper and are not considered valid active `d2wc` managed files by the installer.

## Launching d2wc

When the install completes, launch `d2wc`:

```bash
d2wc
```

The explicit configurator subcommand remains supported:

```bash
d2wc configure
```

## Automatic window-event launching

The active managed Lua file can open `d2wc` automatically when Devilspie2 sees a new normal application window that does not already match a managed rule.

The setting lives in the active managed Lua file:

```lua
local D2WC_EVENT_HANDOFF_ENABLED = true
```

Set it to `false` to disable automatic launching:

```lua
local D2WC_EVENT_HANDOFF_ENABLED = false
```

The same setting can be changed from the configurator:

```text
Menu -> Configure -> Window events
```

The checkbox is:

```text
Automatically open d2wc for unconfigured windows
```
