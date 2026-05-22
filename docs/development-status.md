# d2wc Development Status

## Current Branch

Current repository status:

```text
Branch: configurator-routes-proof
Status: WORKSPACE_ROUTES core and CLI proof complete
Base: main after PR #5
Next action: merge the WORKSPACE_ROUTES proof into main
```

## Latest confirmed local verification

Verification reported on 2026-05-22 after the `WORKSPACE_ROUTES` CLI proof and route-row layout update:

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
148 pytest tests passed.
```

## Completed WORKSPACE_ROUTES edit proof

The `configurator-routes-proof` branch adds the tested config-editing operation set for `WORKSPACE_ROUTES` rules.

Confirmed core behavior:

1. Adds a new `WORKSPACE_ROUTES` rule to rendered Lua source in memory.
2. Modifies an existing `WORKSPACE_ROUTES` rule in memory.
3. Deletes an existing `WORKSPACE_ROUTES` rule in memory.
4. Preserves existing managed Lua program logic outside the route block.
5. Preserves route-row comments where the row still exists.
6. Keeps the `-- add more here` marker as the final route-table entry while the marker exists.
7. Rejects exact duplicate route targets across workspace buckets.
8. Allows broader and narrower targets side by side, for example `d:personal` and `d:personal c:navigator`.
9. Rejects missing old rules on modify.
10. Rejects missing rules on delete.
11. Rejects route rules without a `d:` or `c:` target.
12. Rejects route rules that include `g:`.
13. Rejects route rules that include `le:`.
14. Matches modify and delete requests by parsed rule meaning, not token order.
15. Renders route rules in canonical prefix order: `d:`, then `c:`.
16. Renders workspace route rows ordered by workspace number.
17. Inserts a blank line between workspace route rows.
18. Re-validates rendered output after each edit.

Confirmed CLI behavior:

1. `python -m d2wc add-route --config <path> --workspace <n> --rule "<rule>"` previews by default.
2. `python -m d2wc modify-route --config <path> --old-rule "<rule>" --new-workspace <n> --new-rule "<rule>"` previews by default.
3. `python -m d2wc delete-route --config <path> --rule "<rule>"` previews by default.
4. Each route edit command writes only when `--write` is supplied.
5. Writes route through the safe-save helper.
6. Successful writes create timestamped backups.
7. Failed edits leave the original config unchanged.

Manual route smoke testing used a copied `/tmp/d2wc-route-smoke.lua` config. The add-route preview/write path exposed the route-row layout UX issue, which was corrected before merge by ordering workspace rows and adding blank lines between route rows.

GTK UI work remains deferred.

## Completed WORKSPACE_PLACEMENT edit proof from PR #5

PR #5 added the tested config-editing operation set for `WORKSPACE_PLACEMENT` rules and has been merged into `main`.

Confirmed behavior:

1. Core add, modify, and delete operations are implemented.
2. Guarded CLI commands are implemented: `add-placement`, `modify-placement`, and `delete-placement`.
3. Preview is the default behavior.
4. Writes require `--write`.
5. Writes route through the safe-save helper.
6. Token-order-independent placement modify/delete matching is supported.
7. Placement rules render in canonical prefix order: `d:`, then `c:`, then `g:`.
8. Missing `GEOM` profiles are rejected.
9. Duplicate placement targets are rejected.
10. The `-- add more here` marker remains last.
11. Manual placement smoke testing passed on a copied temporary config.
12. The last confirmed PR #5 verification reported 124 passing tests.

## Completed GEOM edit proof from PR #4

PR #4 added the first tested config-editing operation set for `GEOM` profiles and has been merged into `main`.

Confirmed behavior:

1. Adds a new `GEOM` profile.
2. Modifies an existing `GEOM` profile.
3. Deletes an unused `GEOM` profile.
4. Preserves existing `GEOM` comments and blank lines where practical.
5. Keeps the `-- add more here` marker as the final entry while the marker exists.
6. Rejects duplicate profile names on add.
7. Rejects missing profile names on modify or delete.
8. Rejects deletion when `WORKSPACE_PLACEMENT` still references the profile.
9. Provides guarded CLI commands: `add-geom`, `modify-geom`, and `delete-geom`.
10. Preview is the default behavior and writes require `--write`.
11. Writes route through the safe-save helper.

## Completed safe-save proof from PR #3

PR #3 added core safe-save behavior, save preview, and guarded save writes.

Confirmed behavior:

1. `python -m d2wc save --config <path>` previews by default.
2. `python -m d2wc save --config <path> --write` uses the safe-save helper.
3. Rendered output is written to a temporary file in the target directory.
4. The temporary file is flushed and fsynced.
5. The staged temporary file is validated.
6. A non-overwriting timestamped backup is created.
7. The backup file is flushed and fsynced.
8. The backup directory is fsynced.
9. The target is replaced with `os.replace()`.
10. The target directory is fsynced after replacement.
11. Invalid configs and backup failures leave the original file unchanged.

## Current safe capability

The current Python core supports:

1. Editable development installation.
2. Read-only validation of managed Lua blocks.
3. Dry-run rendering to stdout.
4. Power-loss-oriented safe-save behavior.
5. Save preview by default.
6. Guarded CLI save behavior requiring `--write` before modification.
7. In-memory `GEOM` add, modify, and delete operations.
8. Guarded CLI GEOM add, modify, and delete commands.
9. In-memory `WORKSPACE_PLACEMENT` add, modify, and delete operations.
10. Guarded CLI WORKSPACE_PLACEMENT add, modify, and delete commands.
11. In-memory `WORKSPACE_ROUTES` add, modify, and delete operations.
12. Guarded CLI WORKSPACE_ROUTES add, modify, and delete commands.
13. Marker-tail preservation for `-- add more here`.
14. Token-order-independent rule parsing and modify/delete matching.
15. Exact duplicate target rejection where duplicates would make routing ambiguous.

## Test command guidance

Install the project in editable mode from the repository root:

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

## Next practical work

After the `WORKSPACE_ROUTES` proof is merged, the next implementation target should be selected deliberately. The most likely next CLI/core editing proof is `PIN` and `EXCLUDE`, because both are target-rule lists and can reuse the proven rule-list patterns. GTK UI work should remain deferred until the CLI/core editing operations are sufficiently proven.
