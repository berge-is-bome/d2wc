# Backups

`d2wc` creates a backup automatically before it saves a change to the active managed Lua file. Backups are stored in a `*.bak.tgz` archive beside that managed Lua file.

## Backup location

For the default managed Lua file:

```text
~/.config/d2wc/lua/d2wc.lua
```

The backup archive is:

```text
~/.config/d2wc/lua/d2wc.lua.bak.tgz
```

If you save or open another managed Lua file, its backup archive follows that file. For example:

```text
~/.config/d2wc/lua/work.lua
~/.config/d2wc/lua/work.lua.bak.tgz
```

## Backup entries

Each saved change adds a timestamped entry to the archive.

Example entries:

```text
d2wc.lua.2026-05-20-153000.bak
d2wc.lua.2026-05-20-153001.bak
d2wc.lua.2026-05-20-153002.bak
```

If more than one backup is created during the same second, `d2wc` adds a suffix so the entries stay unique:

```text
d2wc.lua.2026-05-20-153000.bak
d2wc.lua.2026-05-20-153000.bak.1
```

## Current restore status

`d2wc` creates backup archives automatically, but it does not yet provide a restore command or restore screen in the configurator.
