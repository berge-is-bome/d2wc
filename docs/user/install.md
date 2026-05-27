# Install/Update

This guide is for Qubes users who want to install/update `d2wc` in dom0.

## In dispVM:

1. Clone repository.
2. Create archive.
3. Leave the disposable running until the dom0 installation is finished.

```bash
cd /tmp
git clone git@github.com:berge-is-bome/d2wc.git
git -C d2wc archive --format=tar --prefix=d2wc/ HEAD | gzip > /tmp/d2wc.tgz
```

## In dom0:

4. Copy `install.sh` from the disposable.
5. Edit dispVM name to match your's.
6. Make the script executable.
7. Run the script.
8. Shutdown disposable.

```bash
qvm-run --pass-io disp1234 'cat /tmp/d2wc/install.sh' > ~/tmp/install.sh
nvim /tmp/install.sh
chmod 700 /tmp/install.sh
/tmp/install.sh
```

When the install completes, launch `d2wc`:


```bash
[<user>@dom0 ~]$ d2wc
```

