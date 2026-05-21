# d2wc Development Status

## Current Branch

Current repository status:

```text
Branch: main
Status: PR #5 merged; WORKSPACE_PLACEMENT core and CLI proof complete
Next branch: configurator-routes-proof
Next implementation target: WORKSPACE_ROUTES add, modify, and delete operations
```

## Latest confirmed local verification

Verification reported on 2026-05-21 before PR #5 merge:

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
124 pytest tests passed.
```

## Completed WORKSPACE_PLACEMENT edit proof from PR #5

PR #5 added the first tested config-editing operation set for `WORKSPACE_PLACEMENT` rules and has been merged into `main`.

Confirmed core behavior:

1. Adds a new `WORKSPACE_PLACEMENT` rule to rendered Lua source in memory.
2. Modifies an existing `WORKSPACE_PLACEMENT` rule in memory.
3. Deletes an existing `WORKSPACE_PLACEMENT` rule in memory.
4. Preserves existing `WORKSPACE_PLACEMENT` comments and blank lines where practical.
5. Applies updated rule tuples while preserving managed rule-list comments.
6. Keeps the `-- add more here` marker as the final entry in managed rule-list render paths while the marker exists.
7. Rejects duplicate placement targets on add.
8. Rejects missing old rules on modify.
9. Rejects missing rules on delete.
10. Rejects missing `GEOM` profiles on add and modify.
11. Rejects placement rules without a `d:` or `c:` target.
12. Rejects placement rules without a `g:` profile.
13. Rejects placement rules that include `le:`.
14. Matches modify and delete requests by parsed rule meaning, not token order.
15. Renders placement rules in canonical prefix order: `d:`, then `c:`, then `g:`.
16. Re-validates rendered output after each edit.

Confirmed CLI behavior:

1. `python -m d2wc add-placement --config <path> --rule "<rule>"` previews by default.
2. `python -m d2wc modify-placement --config <path> --old-rule "<rule>" --new-rule "<rule>"` previews by default.
3. `python -m d2wc delete-placement --config <path> --rule "<rule>"` previews by default.
4. Each placement edit command writes only when `--write` is supplied.
5. Writes route through the safe-save helper.
6. Successful writes create timestamped backups.
7. Failed edits leave the original config unchanged.

Manual placement smoke test reported on 2026-05-21:

1. `add-placement` preview modified nothing.
2. `add-placement --write` added the test placement rule and created a backup.
3. `modify-placement` preview modified nothing.
4. `modify-placement --write` updated the test placement rule and created a backup.
5. `delete-placement` preview modified nothing.
6. `delete-placement --write` removed the test placement rule and created a backup.
7. The copied config validated after each write.
8. Token order did not matter for add, modify, or delete input.
9. Timestamped backups existed after writes.

GTK UI work remains deferred.

## GEOM edit baseline from PR #4

PR #4 added the first tested config-editing operation set for `GEOM` profiles.

Confirmed GEOM behavior:

1. Adds a new `GEOM` profile.
2. Modifies an existing `GEOM` profile.
3. Deletes an unused `GEOM` profile.
4. Preserves existing `GEOM` comments and blank lines where practical.
5. Appends new profiles that did not exist in the original `GEOM` block.
6. Skips removed profiles when rendering the updated `GEOM` block.
7. Keeps the `-- add more here` marker as the final entry while the marker exists.
8. Rejects duplicate profile names on add.
9. Rejects missing profile names on modify or delete.
10. Rejects deletion when `WORKSPACE_PLACEMENT` still references the profile.
11. Rejects invalid profile names.
12. Rejects profile width or height below the current minimum size.
13. Provides guarded CLI commands: `add-geom`, `modify-geom`, and `delete-geom`.

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
15. In-memory `WORKSPACE_PLACEMENT` add, modify, and delete operations.
16. Guarded CLI WORKSPACE_PLACEMENT add, modify, and delete commands.
17. Marker-tail preservation for `-- add more here`.
18. Token-order-independent rule parsing and placement modify/delete matching.

## Next practical work

The next implementation branch should be `configurator-routes-proof`.

The next practical implementation target is `WORKSPACE_ROUTES` add, modify, and delete operations:

1. Start with core in-memory operations.
2. Preserve comments, blank lines, and `-- add more here` marker-tail behavior in managed route lists.
3. Reject duplicate route targets across workspace buckets.
4. Support token-order-independent matching for modify and delete.
5. Render route rules in canonical prefix order: `d:`, then `c:`.
6. Add guarded CLI commands that preview by default and write only with `--write`.
7. Inspect and update stale tests and renderer-output expectations before handing back local test commands.

GTK UI work should remain deferred until the config-editing operations are proven through CLI/core tests.
