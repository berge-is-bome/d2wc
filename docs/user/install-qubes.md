# Install/Update for Qubes

This guide is for Qubes users who want to install/update `d2wc` in dom0.

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

Installed layout:

- Cached archive: `~/.cache/d2wc/d2wc.tgz`
- Extracted source tree: `~/.local/share/d2wc/source/`
- Managed Lua config files: `~/.config/d2wc/lua/`
- Devilspie2 integration path: `~/.config/devilspie2/d2wc.lua` (symlink to the active managed file)
- Executable: `~/.local/bin/d2wc`
- Python package: user site-packages under `~/.local/lib/pythonX.Y/site-packages/`


When the install completes, launch `d2wc`:

```bash
d2wc
```
