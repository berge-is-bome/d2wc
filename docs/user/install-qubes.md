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

## Launching d2wc

When the install completes, launch `d2wc`:

```bash
d2wc
```
