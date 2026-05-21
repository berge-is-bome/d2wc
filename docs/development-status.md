# d2wc Development Status

## Current Branch

Current active branch:

```text
Branch: configurator-add-geom-proof
Base: main at PR #3 squash merge commit 71b0f911ce0b0e631cb891ed905056eae18a1aa8
Status: GEOM add, modify, delete, marker-tail behavior, and manual smoke checkpoint locally verified
```

## Latest confirmed local verification

Verification reported on 2026-05-21:

```bash
python -m d2wc validate --config src/d2wc.lua
python -m d2wc render --config src/d2wc.lua --stdout > /tmp/d2wc-rendered.lua
python -m d2wc validate --config /tmp/d2wc-rendered.lua
python -m pytest
```

Result:

```text
src/d2wc.lua validates successfully.
Rendered /tmp/d2wc-rendered.lua validates successfully.
99 pytest tests passed.
```

A later renderer verification and GEOM smoke rerun also passed after adding marker-tail behavior for `-- add more here`.

## Manual GEOM smoke verification

Manual smoke verification reported on 2026-05-21 using a copied temporary config.

Result:

```text
add-geom preview modified nothing.
add-geom --write added the test profile and created a backup.
modify-geom preview modified nothing.
modify-geom --write updated the test profile and created a backup.
delete-geom preview modified nothing.
delete-geom --write removed the test profile and created a backup.
The copied config validated after each write.
The -- add more here marker remained the final table entry after add/write testing.
```

## Current GEOM edit proof

The current branch adds the first tested config-editing operation set for `GEOM` profiles.

Confirmed core behavior:

1. Adds a new `GEOM` profile to rendered Lua source in memory.
2. Modifies an existing `GEOM` profile in memory.
3. Deletes an unused `GEOM` profile in memory.
4. Preserves existing `GEOM` comments and blank lines where practical.
5. Appends new profiles that did not exist in the original `GEOM` block.
6. Skips removed profiles when rendering the updated `GEOM` block.
7. Keeps the `-- add more here` marker as the final entry in managed table render paths while the marker exists.
8. Rejects duplicate profile names on add.
9. Rejects missing profile names on modify or delete.
10. Rejects deletion when `WORKSPACE_PLACEMENT` still references the profile.
11. Rejects invalid profile names.
12. Rejects profile width or height below the current minimum size.
13. Re-validates rendered output after each edit.

Confirmed CLI behavior:

1. `python -m d2wc add-geom --config <path> --name <name> --x <n> --y <n> --w <n> --h <n>` previews by default.
2. `python -m d2wc modify-geom --config <path> --name <name> --x <n> --y <n> --w <n> --h <n>` previews by default.
3. `python -m d2wc delete-geom --config <path> --name <name>` previews by default.
4. Each GEOM edit command writes only when `--write` is supplied.
5. Writes route through the safe-save helper.
6. Successful writes create timestamped backups.
7. Failed edits leave the original config unchanged.

This branch now exposes the GEOM edit proof through guarded CLI commands. GTK UI work remains deferred.

## Safe-save baseline from PR #3

PR #3 added core safe-save behavior, save preview, and guarded save writes.

Confirmed preview behavior:

1. `python -m d2wc save --config <path>` previews by default.
2. Preview validates and renders in memory.
3. Preview prints the config path, planned backup path, and rendered byte count.
4. Preview creates no backup files.
5. Preview creates no backup directories.
6. Preview modifies no config file.
7. Invalid config exits without writing and reports validation errors.

Confirmed write behavior:

1. `python -m d2wc save --config <path> --write` uses the safe-save helper.
2. Successful guarded saves print the config path, backup path, and success message.
3. `--backup-dir <path>` can direct backups to an explicit directory.
4. Invalid config exits without writing and reports validation errors.
5. Backup failures leave the original file unchanged.

Confirmed power-loss-oriented save behavior:

1. Rendered output is written to a temporary file in the target directory.
2. The temporary file is flushed and fsynced.
3. The staged temporary file is validated.
4. A non-overwriting timestamped backup is created.
5. The backup file is flushed and fsynced.
6. The backup directory is fsynced.
7. The target is replaced with `os.replace()`.
8. The target directory is fsynced after replacement.
9. Staged temporary files are cleaned up on failure.

## Test command guidance

Install `python3-pip` with your package manager, then install the project in editable mode from the repository root:

```bash
python -m pip install -e .
```

Use the four-command renderer verification path when renderer behavior changes:

```bash
python -m d2wc validate --config src/d2wc.lua
python -m d2wc render --config src/d2wc.lua --stdout > /tmp/d2wc-rendered.lua
python -m d2wc validate --config /tmp/d2wc-rendered.lua
python -m pytest
```

When renderer behavior has not changed, the shorter verification path is normally enough:

```bash
python -m d2wc validate --config src/d2wc.lua
python -m pytest
```

## Current safe capability

The current Python core supports:

1. Editable development installation.
2. Read-only validation of managed Lua blocks.
3. Dry-run rendering to stdout.
4. Parser and validator tests for managed Lua sections.
5. Renderer round-trip tests.
6. Runtime settings validation tests.
7. Split-profile generation tests.
8. Duplicate and shadow validation tests.
9. Core safe-save tests using temporary directories.
10. Power-loss-oriented fsync ordering for staged files, backup files, backup directories, and target directories.
11. Save preview by default.
12. Guarded CLI save behavior requiring `--write` before modification.
13. In-memory `GEOM` add, modify, and delete operations.
14. Guarded CLI GEOM add, modify, and delete commands.
15. Marker-tail preservation for `-- add more here`.

## Next practical work

The next practical step is to decide whether PR #4 is ready for review.

GTK UI work should remain deferred until the config-editing operation is proven through CLI/core tests.
