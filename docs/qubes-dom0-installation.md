# Qubes dom0 Installation

This guide is for Qubes users who want to install `d2wc` in dom0 from a source archive prepared in a networked DisposableVM.

The example DisposableVM name below is `disp1234`. Replace `disp1234` with the actual DisposableVM name shown by Qubes.

## Condensed commands

In the networked DisposableVM:

```bash
git clone https://github.com/berge-is-bome/d2wc.git
cd d2wc
./d2wc-prepare-archive.sh
```

In dom0:

```bash
mkdir -p ~/Qubes
cd ~/Qubes

qvm-run --pass-io disp1234 'cat /tmp/d2wc-installation.sh' > d2wc-installation.sh
chmod 700 d2wc-installation.sh
```

Edit the DisposableVM name inside the dom0 installer if needed:

```bash
nvim d2wc-installation.sh
```

Run the dom0 installer:

```bash
./d2wc-installation.sh
```

After installation, a new terminal should be able to find the installed command:

```bash
command -v d2wc
d2wc configure
```

## Expanded steps

### 1. Prepare the source archive in a networked DisposableVM

Use a networked DisposableVM to clone the repository and prepare the source archive. dom0 should not need direct network access for this workflow.

The helper script `d2wc-prepare-archive.sh` prepares two files in `/tmp` inside the DisposableVM:

```text
/tmp/d2wc.tgz
/tmp/d2wc-installation.sh
```

The archive is created from the current Git checkout using:

```bash
git archive --format=tar --prefix=d2wc/ HEAD | gzip > /tmp/d2wc.tgz
```

The installer script is copied to `/tmp` so dom0 can copy it from the same DisposableVM.

### 2. Copy the dom0 installer script into dom0

In dom0, create `~/Qubes` if it does not already exist, then copy the installer script from the DisposableVM.

The command uses `qvm-run --pass-io` so the script content is passed directly to dom0 stdout and saved as `~/Qubes/d2wc-installation.sh`.

### 3. Set the correct DisposableVM name

Open `~/Qubes/d2wc-installation.sh` in an editor and check this line:

```bash
VM="disp1234"
```

Replace `disp1234` with the actual DisposableVM name that contains `/tmp/d2wc.tgz`.

### 4. Run the dom0 installer

The dom0 installer performs the dom0 side of the install/update workflow:

1. Copies `/tmp/d2wc.tgz` from the configured DisposableVM into `~/Qubes/d2wc.tgz`.
2. Removes the old extracted `~/Qubes/d2wc` source tree.
3. Extracts the new source tree into `~/Qubes/d2wc`.
4. Creates `~/.config/devilspie2/d2wc.lua` from the bundled `src/d2wc.lua` only if it does not already exist.
5. Removes any previous user-site `d2wc` Python package installation.
6. Installs the new package into the dom0 user Python site with `pip --user`.
7. Configures `$HOME/.local/bin` for Bash or Fish using a managed shell-config block.
8. Launches the installed command with the explicit path:

```bash
$HOME/.local/bin/d2wc configure
```

### 5. Existing Devilspie2 scripts are not overwritten

The installer creates only this d2wc-managed file when it is missing:

```text
~/.config/devilspie2/d2wc.lua
```

If that file already exists, the installer keeps it. Other Devilspie2 Lua scripts in `~/.config/devilspie2/` are not modified.

Devilspie2 can load multiple Lua scripts from the same folder, so an existing user script can coexist with `d2wc.lua`.

### 6. Shell PATH handling

The Python package installs the `d2wc` command under:

```text
~/.local/bin/d2wc
```

The installer adds `$HOME/.local/bin` to the user's Bash or Fish startup config if needed. It uses a managed block, so future installer runs replace that block instead of appending duplicates.

Open a new terminal after installation, then check:

```bash
command -v d2wc
```

Expected output:

```text
/home/user/.local/bin/d2wc
```

## Current implementation note

The installer is intentionally ahead of the final real-config plumbing. The next code change must make plain `d2wc configure` load `~/.config/devilspie2/d2wc.lua` as the managed config by default.
