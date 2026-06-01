# Install/Update for Qubes

This guide is for Qubes users who want to install or update `d2wc` in dom0.

The install flow uses a source VM to clone and archive the repository, then runs the installer in dom0. The source VM can be any running `AppVM` or `DispVM` with internet access.

## In the source VM:

1. Clone repository.
2. Create archive.
3. Copy install script to /tmp.
4. Leave the source VM running until the dom0 installation is finished.

```bash
cd /tmp
git clone git@github.com:berge-is-bome/d2wc.git
git -C d2wc archive --format=tar --prefix=d2wc/ HEAD | gzip > /tmp/d2wc.tgz
cp d2wc/install-qubes.sh .
```

## In dom0:

4. Copy `install-qubes.sh` from the source VM.
5. Make the script executable.
6. Run the script.
7. Shutdown the source VM when installation is complete.

Replace `<source-vm>` with the running VM that contains `/tmp/d2wc.tgz`.

```bash
cd /tmp
qvm-run --pass-io <source-vm> 'cat /tmp/d2wc/install-qubes.sh' > /tmp/install-qubes.sh
chmod 700 /tmp/install-qubes.sh
./install-qubes.sh
```

The script can also be called with a sourceVM parameter, `./install-qubes.sh <source-vm>`. If it is omitted, the installer shows a `zenity` chooser when available. The chooser lists running `AppVM` and `DispVM` entries only. If `zenity` is unavailable, the installer falls back to a command-line prompt.

## Installer update behavior

The installer copies and validates `/tmp/d2wc.tgz` before replacing the local source tree.

On update, the installer preserves the active managed file when `~/.config/devilspie2/d2wc.lua` is already a safe symlink into `~/.config/d2wc/lua/`.

The installer also refreshes marked managed Lua files under `~/.config/d2wc/lua/` with missing runtime code needed by the current bundled managed script. This is a targeted migration, not a full template rewrite. Existing user rules, comments, spacing, and existing toggle values are preserved.

Only files that contain the managed marker are migrated:

```lua
local D2WC_MANAGED = true
```

Files without that marker are skipped by the migration helper and are not considered valid active `d2wc` managed files by the installer.

## Launching d2wc

When the install completes, launch `d2wc`:

```bash
d2wc
```

You can also bind a keyboard shortcut to `d2wc`, or set how `d2wc` [behaves](configurator-options.md) on new window events.
