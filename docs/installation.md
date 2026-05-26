In a disposable:

1. Clone repository.
2. Create archive.
3. Copy installer to temp.

```bash
git clone git@github.com:berge-is-bome/d2wc.git
git archive --format=tar --prefix=d2wc/ HEAD | gzip > /tmp/d2wc.tgz
cp install.sh /tmp
```

In dom0:

4. Copy `install.sh` from the disposable.
5. Edit VM name to match your's.
6. Make the script executable.
7. Run the script.
8. Shutdown disposable.

```bash
qvm-run --pass-io disp1234 'cat /tmp/install.sh' > ~/tmp/install.sh
nvim /tmp/install.sh
sudo chmod +x
./install.sh
```
