# d2wc Development Status

## Current Branch

Current active branch:

```text
Branch: configurator-save-proof
Base: main at PR #2 squash merge commit 903cc20f2133f359fa2280dd7fd5d7c49d17d917
Status: guarded save CLI checkpoint locally verified
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
73 pytest tests passed.
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

The four-command path confirms both the original Lua source and the rendered output validate cleanly. The shorter path is appropriate for documentation-only changes and most non-renderer logic changes unless those changes can affect generated Lua output.

## Latest safe-save changes

The current `configurator-save-proof` branch adds core safe-save behavior and a guarded save CLI.

Confirmed core behavior:

1. Renders the target config in memory.
2. Writes rendered output to a temporary file in the target directory.
3. Flushes and fsyncs the staged temporary file.
4. Validates the staged temporary file.
5. Creates a non-overwriting timestamped backup.
6. Flushes and fsyncs the backup file.
7. Fsyncs the backup directory after backup creation.
8. Replaces the target with `os.replace()` only after staging, validation, and backup succeed.
9. Fsyncs the target directory after replacement.
10. Cleans up staged temporary files on failure.
11. Leaves the original file intact when validation or backup creation fails.

Confirmed CLI behavior:

1. `python -m d2wc save --config <path>` refuses to write.
2. `python -m d2wc save --config <path> --write` uses the safe-save helper.
3. Successful guarded saves print the config path, backup path, and success message.
4. `--backup-dir <path>` can direct backups to an explicit directory.
5. Invalid config exits without writing and reports validation errors.
6. Backup failures leave the original file unchanged.

The save command is now user-facing, but it is guarded by the explicit `--write` flag and covered by temporary-directory tests.

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
11. Guarded CLI save behavior requiring `--write`.

## Next practical work

The next practical step is to open or update a draft PR for `configurator-save-proof` and continue the safe-save proof in small slices.

Recommended next implementation slice:

1. Add a dry-run save preview command or option that reports what would happen without writing.
2. Add tests proving the preview path does not create backups or modify the config.
3. Consider whether the final CLI should use `save --dry-run` or a separate `plan-save` command.
4. Keep GTK UI work deferred.

GTK UI work should remain deferred until parser, validator, renderer, and safe save behavior are all covered by tests.
