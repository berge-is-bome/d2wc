# Backup Archives

## Purpose

`d2wc` creates backups before guarded writes replace a managed Lua config file.

The active Lua file is not compressed and is not moved into an archive. Only backup snapshots are stored in the backup archive.

For the user-facing backup overview, see [Backups](../user/backups.md).

## Archive location

Backup archives follow the managed Lua file being written.

For the default installed managed config:

```text
~/.config/d2wc/lua/d2wc.lua
```

`d2wc` stores backup snapshots in:

```text
~/.config/d2wc/lua/d2wc.lua.bak.tgz
```

For another managed file such as:

```text
~/.config/d2wc/lua/work.lua
```

`d2wc` stores backup snapshots in:

```text
~/.config/d2wc/lua/work.lua.bak.tgz
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

## Save order

The safe-save path keeps the existing conservative order:

1. Validate the supplied rendered source in memory.
2. Write the replacement config to a temporary file in the target directory.
3. Sync the temporary file.
4. Validate the staged temporary file.
5. Create or update the backup archive.
6. Sync the backup archive and archive directory.
7. Atomically replace the target config with the staged file.
8. Sync the target directory.

If backup archive creation fails, `d2wc` leaves the active config unchanged.

## Archive update behavior

A new backup is added by building a temporary archive in the same directory, copying existing regular-file members into it, adding the new timestamped backup member, syncing the temporary archive, and atomically replacing the previous archive.

This keeps the archive transportable while preserving the safe-save model.

## Current scope

Current behavior is intentionally limited:

1. Backup archives are created only as part of guarded writes.
2. The GTK configurator can load and edit active managed Lua files under `~/.config/d2wc/lua/`.
3. `~/.config/devilspie2/d2wc.lua` is the Devilspie2-facing integration symlink, not the primary managed config store.
4. The development test-config workflow remains available for isolated UI testing at `~/.config/devilspie2/d2wc-test.lua`.
5. Backup retention is not implemented yet.
6. Diff-based backups are not implemented.
7. User-facing restore commands and GTK restore UI are not implemented yet.
