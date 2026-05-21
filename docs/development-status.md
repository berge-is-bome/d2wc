# d2wc Development Status

## Current Branch

Current active branch:

```text
Branch: configurator-save-proof
Base: main at PR #2 squash merge commit 903cc20f2133f359fa2280dd7fd5d7c49d17d917
Status: save preview and guarded write checkpoint locally verified
```

## What read-only core proof means

PR #2 was merged because it proves the parser, validator, renderer, CLI scaffold, settings model, split-profile logic, duplicate/shadow validation, and tests are working. But do not consider `d2wc` ready to save changes into a real user config yet.

## Latest confirmed local verification

Verification reported on 2026-05-21:

```bash
python -m d2wc validate --config src/d2wc.lua
python -m pytest
```

Result:

```text
src/d2wc.lua validates successfully.
78 pytest tests passed.
```

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

## Latest safe-save changes

The current `configurator-save-proof` branch adds core safe-save behavior, save preview, and guarded save writes.

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

The save command is user-facing, safe by default, and covered by temporary-directory tests.

## Latest renderer changes

The latest renderer patch confirms these behaviors:

1. Right-side comments in managed rule-list sections are aligned using the longest rendered left-side entry plus 5 spaces.
2. Pure note comments are preserved.
3. Blank separator lines are preserved.
4. `GEOM` `x`, `y`, `w`, and `h` numeric columns have a minimum width of 4.
5. `GEOM` right-side comments are aligned using the longest rendered `GEOM` left-side entry plus 5 spaces.
6. Renderer expectations in the test suite were updated with the code change.

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

## Next practical work

The next practical step is to run a manual verification using a copied temporary config, then decide whether PR #3 is ready for review.

GTK UI work should remain deferred until parser, validator, renderer, and safe save behavior are all covered by tests.
