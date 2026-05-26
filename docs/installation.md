In the disposable:

1. Clone repository.
2. Create archive.
3. Copy installer to temp.

```bash
git clone git@github.com:berge-is-bome/d2wc.git
git archive --format=tar --prefix=d2wc/ HEAD | gzip > /tmp/d2wc.tgz
cp install.sh /tmp
```

In dom0:

4. Create `~/d2wc`.
5. Copy `install.sh` from the disposable.
6. Edit VM name to match your's.
8. Make the script executable.
9. Run the script.
10. Shutdown disposable.

```bash
cd $HOME
mkdir -p d2wc
qvm-run --pass-io disp1234 'cat /tmp/install.sh' > ~/tmp/install.sh
nvim /tmp/install.sh
sudo chmod +x
./install.sh
```

Explain that the installer creates `~/.config/devilspie2/d2wc.lua` only if it does not already exist.

Explain that the installer configures `$HOME/.local/bin` for Bash or Fish so the installed `d2wc` command is available later.
