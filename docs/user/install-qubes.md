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

Before replacing the local installation source, the installer copies and validates `/tmp/d2wc.tgz` from the selected source VM.

## Installed user files

The installer stores the copied archive cache under:

```text
~/.cache/d2wc/
```

The installer extracts the local installation source under:

```text
~/.local/share/d2wc/source/
```

The configurator stores user-owned `d2wc` managed Lua files under:

```text
~/.config/d2wc/lua/
```

The default managed Lua file is:

```text
~/.config/d2wc/lua/d2wc.lua
```

The configurator stores its UI settings under:

```text
~/.config/d2wc/settings.json
```

Devilspie2 reads the active managed file through this integration symlink:

```text
~/.config/devilspie2/d2wc.lua
```

The installer and configurator update that symlink only when it is safe. Existing unrelated Devilspie2 scripts and unrelated symlinks under `~/.config/devilspie2/` are left unchanged.

## Update behavior

On update, the installer preserves existing managed Lua files under `~/.config/d2wc/lua/`.

If `~/.config/devilspie2/d2wc.lua` already points safely to a managed file under `~/.config/d2wc/lua/`, the update preserves that active managed file selection.

If `d2wc` is already running during an update, the installer warns the user to close all running configurator windows before continuing. The installer continues after `d2wc` has been closed.

Existing UI settings in `~/.config/d2wc/settings.json` are not overwritten by updates.

## Launching d2wc

When the install completes, launch `d2wc`:

```bash
d2wc
```

When launched normally, `d2wc` opens the current active managed file. If the Devilspie2 integration symlink is not present or is not safe, `d2wc` falls back to `~/.config/d2wc/lua/d2wc.lua`.
