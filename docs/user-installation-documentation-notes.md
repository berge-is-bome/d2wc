# User Installation Documentation Notes

This note captures the intended shape of the future user-facing installation documentation.

## Manual installation document requirement

Create a dedicated user-facing document for Qubes users who want to install `d2wc` by hand instead of using the helper scripts.

The manual installation document must not be a copy/paste version of the scripts. It should describe the individual steps the user must follow and explain why each step exists.

Required structure:

1. Start with a condensed command section.
2. Keep the commands in the exact order the user should run them.
3. Use blank lines to split logical tasks, such as preparing the archive in the DisposableVM, copying the installer into dom0, installing in dom0, and launching `d2wc`.
4. Below the condensed command section, add an expanded explanation section.
5. The expanded section should explain what each command group does, including why the archive is created in a networked DisposableVM and why dom0 receives only the tarball and installer script.

The example DisposableVM name in documentation should be `disp1234`. The text should tell users to replace `disp1234` with the actual DisposableVM name shown by Qubes.

The document should cover at least these manual steps:

1. Start a DisposableVM with network access.
2. Clone the repository inside that DisposableVM.
3. Create `/tmp/d2wc.tgz` with:

```bash
git archive --format=tar --prefix=d2wc/ HEAD | gzip > /tmp/d2wc.tgz
```

4. Copy `d2wc-installation.sh` to `/tmp` in the same DisposableVM.
5. In dom0, create `~/Qubes` if it does not already exist.
6. Copy `/tmp/d2wc-installation.sh` from the DisposableVM into dom0.

```bash
```bash
qvm-run --pass-io disp1234 'cat /tmp/d2wc-installation.sh' > ~/Qubes/d2wc-installation.sh
```

8. Edit the `VM="disp1234"` line in the dom0 script so it matches the actual DisposableVM name.
9. Make the dom0 script executable.
10. Run the dom0 script.
11. Explain that the installer creates `~/.config/devilspie2/d2wc.lua` only if it does not already exist.
12. Explain that the installer configures `$HOME/.local/bin` for Bash or Fish so the installed `d2wc` command is available later.

Keep the document concise, practical, and Qubes-specific.
