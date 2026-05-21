# d2wc Development Status

## Current Branch

Current active branch:

```text
Branch: configurator-add-geom-proof
Base: main at PR #3 squash merge commit 71b0f911ce0b0e631cb891ed905056eae18a1aa8
Status: first GEOM edit checkpoint locally verified
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
83 pytest tests passed.
```

## Current GEOM edit proof

The current branch adds the first in-memory config-editing operation for `GEOM` profiles.

Confirmed behavior:

1. Adds a new `GEOM` profile to rendered Lua source in memory.
2. Preserves existing `GEOM` comments and blank lines.
3. Appends new profiles that did not exist in the original `GEOM` block.
4. Rejects duplicate profile names unless replacement is explicitly requested.
5. Replaces an existing profile when requested.
6. Rejects invalid profile names.
7. Rejects profile width or height below the current minimum size.
8. Re-validates rendered output after the edit.

This branch does not yet expose a CLI command for adding a `GEOM` profile. The first slice is core-only.

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
13. In-memory `GEOM` add and replace operation.

## Next practical work

The next practical step is to expose the GEOM add operation through a guarded CLI preview/write flow that uses the safe-save helper.

GTK UI work should remain deferred until the config-editing operation is proven through CLI/core tests.
