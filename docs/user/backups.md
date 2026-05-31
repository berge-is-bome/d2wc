# Backup Archives

## Purpose

`d2wc` creates backups before guarded writes replace a managed Lua config file.

The active Lua file is not compressed and is not moved into an archive. Only backup snapshots are stored in the backup archive.

## Archive location

For the installed managed config:

```text
~/.config/d2wc/lua/d2wc.lua
```

`d2wc` stores backup snapshots in:

```text
~/.config/d2wc/lua/d2wc.lua.bak.tgz
```

If `--backup-dir` is supplied, the archive is created in that directory and keeps the same filename pattern:

```text
<backup-dir>/<config-filename>.bak.tgz
```

## Archive members

Each successful write adds a timestamped backup member to the archive.

Example members:

```text
d2wc.lua.2026-05-20-153000.bak
d2wc.lua.2026-05-20-153001.bak
d2wc.lua.2026-05-20-153002.bak
```

If more than one backup is created during the same second, `d2wc` keeps member names unique by adding a suffix:

```text
d2wc.lua.2026-05-20-153000.bak
d2wc.lua.2026-05-20-153000.bak.1
```
