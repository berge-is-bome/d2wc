# d2wc Development Status

## Current repository status

Current repository status for branch `configurator-active-window-proof`:

```text
Branch: configurator-active-window-proof
Status: read-only active-window capture proof implemented for review
Latest merged proof: PR #14, first GTK configurator launch proof
Current proof branch: configurator-active-window-proof
```

The CLI/core edit-proof phase is complete for the six managed Lua sections:

1. `GEOM`
2. `WORKSPACE_PLACEMENT`
3. `WORKSPACE_ROUTES`
4. `PIN`
5. `EXCLUDE`
6. `LEFT_EDGE_CORRECTION`

The GTK launch proof is complete and merged through PR #14. The current proof branch captures the active X11 window before the configurator window is shown and displays a read-only snapshot in the GTK window.

The active-window proof captures:

1. Active window id from `_NET_ACTIVE_WINDOW`.
2. Window title from `WM_NAME`.
3. Class instance and class from `WM_CLASS`.
4. Qubes domain from `_QUBES_VMNAME`, where available.
5. Empty `_QUBES_VMNAME` as `dom0`.
6. Window geometry from `xwininfo`.

The branch still performs no config reads, config writes, rule editing, runtime reloads, or restart actions.

Manual Qubes/XFCE launch verification is still required before this proof should be considered complete.

## Latest confirmed local verification

Verification reported on 2026-05-22 after PR #12 follow-up testing:

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
197 pytest tests passed.
```

Manual copied-config smoke testing also passed for the `LEFT_EDGE_CORRECTION` add, modify, and delete CLI commands before PR #12 was merged.

The `configurator-active-window-proof` branch adds automated parser and formatter tests for active-window capture. Manual GTK launch testing should be run on Qubes/XFCE with:

```bash
python -m d2wc configure
d2wc configure
```

## Historical Lua script preservation

The pre-repository `d2wc.lua` history has been preserved in Git and connected to `main`.

A tag points to the archived history:

```text
archive/d2wc-lua-pre-repo-history
```

Inspect the preserved Lua evolution with:

```bash
git log --oneline --reverse archive/d2wc-lua-pre-repo-history -- src/d2wc.lua
```

Design context recovered from that history is recorded in [Lua Design History Notes](lua-design-history.md).

## Completed managed-section edit proofs

All six managed Lua sections now have the same core editing proof pattern:

1. Add one managed entry or rule.
2. Modify one managed entry or rule.
3. Delete one managed entry or rule.
4. Preview by default.
5. Write only when `--write` is supplied.
6. Route writes through the safe-save helper.
7. Create timestamped backups on successful writes.
8. Re-validate rendered output after edits.
9. Leave the original config unchanged after failed edits.
10. Preserve comments and blank lines where practical.
11. Preserve `-- add more here` marker-tail behavior in edited rule-list sections.
12. Match modify and delete requests by parsed meaning rather than token order where applicable.
13. Reject exact duplicate targets where duplicates would make behavior ambiguous.

## Completed GTK launch proof

PR #14 added the first read-only GTK launch proof and has been merged into `main`.

Confirmed behavior:

1. `python -m d2wc configure` opens a GTK window.
2. `d2wc configure` opens the same GTK window after refreshing the editable install.
3. The window closes cleanly.
4. The proof remains read-only.
5. No config files are read or written.
6. No active-window capture was included in PR #14.
7. No rule editing UI was included in PR #14.

## Completed LEFT_EDGE_CORRECTION edit proof

PR #12 added the tested config-editing operation set for `LEFT_EDGE_CORRECTION` rules and has been merged into `main`.

Confirmed behavior:

1. Adds a new `LEFT_EDGE_CORRECTION` rule in memory.
2. Modifies an existing `LEFT_EDGE_CORRECTION` rule in memory.
3. Deletes an existing `LEFT_EDGE_CORRECTION` rule in memory.
4. Preserves comments and blank lines where practical.
5. Keeps `-- add more here` as the final rule-list marker while it exists.
6. Rejects duplicate left-edge targets on add.
7. Rejects missing old rules on modify.
8. Rejects missing rules on delete.
9. Rejects left-edge rules without a `d:` or `c:` target.
10. Rejects left-edge rules without `le:`.
11. Rejects left-edge rules containing `g:`.
12. Rejects invalid left-edge modes such as `le:pos3` before rendering.
13. Matches modify and delete requests by parsed rule meaning, not token order.
14. Renders edited rules in canonical prefix order: `d:`, then `c:`, then `le:`.
15. Exposes guarded CLI commands: `add-left-edge`, `modify-left-edge`, and `delete-left-edge`.
16. Preview is the default behavior.
17. Writes require `--write`.
18. Writes route through the safe-save helper.

Manual left-edge smoke testing used a copied temporary config, not the repository `src/d2wc.lua`.

## Completed PIN and EXCLUDE edit proof

PR #11 added the tested config-editing operation set for `PIN` and `EXCLUDE` rules and has been merged into `main`.

Confirmed behavior:

1. Adds a new `PIN` rule in memory.
2. Modifies an existing `PIN` rule in memory.
3. Deletes an existing `PIN` rule in memory.
4. Adds a new `EXCLUDE` rule in memory.
5. Modifies an existing `EXCLUDE` rule in memory.
6. Deletes an existing `EXCLUDE` rule in memory.
7. Preserves comments and blank lines where practical.
8. Keeps `-- add more here` as the final rule-list marker while it exists.
9. Rejects duplicate targets on add.
10. Rejects missing old rules on modify.
11. Rejects missing rules on delete.
12. Rejects rules without a `d:` or `c:` target.
13. Rejects rules containing `g:`.
14. Rejects rules containing `le:`.
15. Matches modify and delete requests by parsed rule meaning, not token order.
16. Renders edited rules in canonical prefix order: `d:`, then `c:`.
17. Exposes guarded CLI commands: `add-pin`, `modify-pin`, `delete-pin`, `add-exclude`, `modify-exclude`, and `delete-exclude`.
18. Preview is the default behavior.
19. Writes require `--write`.
20. Writes route through the safe-save helper.

Manual PIN and EXCLUDE smoke testing used a copied temporary config, not the repository `src/d2wc.lua`.

## Completed WORKSPACE_ROUTES edit proof

The `WORKSPACE_ROUTES` editing proof is merged through PR #7, PR #8, and PR #9 follow-up work.

Confirmed behavior:

1. Adds a new `WORKSPACE_ROUTES` rule to rendered Lua source in memory.
2. Modifies an existing `WORKSPACE_ROUTES` rule in memory.
3. Deletes an existing `WORKSPACE_ROUTES` rule in memory.
4. Preserves existing managed Lua program logic outside the route block.
5. Preserves route-row comments where the row still exists.
6. Preserves standalone comments after multiline route closing comments.
7. Keeps comments after the `-- add more here` marker in the marker tail.
8. Keeps the `-- add more here` marker as tail content while the marker exists.
9. Rejects exact duplicate route targets across workspace buckets.
10. Allows broader and narrower targets side by side, for example `d:personal` and `d:personal c:navigator`.
11. Rejects missing old rules on modify.
12. Rejects missing rules on delete.
13. Rejects route rules without a `d:` or `c:` target.
14. Rejects route rules that include `g:`.
15. Rejects route rules that include `le:`.
16. Matches modify and delete requests by parsed rule meaning, not token order.
17. Renders route rules in canonical prefix order: `d:`, then `c:`.
18. Renders workspace route rows ordered by workspace number.
19. Inserts a blank line between workspace route rows.
20. Re-validates rendered output after each edit.
21. Exposes guarded CLI commands: `add-route`, `modify-route`, and `delete-route`.
22. Preview is the default behavior.
23. Writes require `--write`.
24. Writes route through the safe-save helper.

Manual route smoke testing used a copied temporary config. Review follow-up work after PR #8 fixed route comment preservation around multiline route closing comments and marker-tail comments.

## Completed WORKSPACE_PLACEMENT edit proof

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

## Completed GEOM edit proof

PR #4 added the first tested config-editing operation set for `GEOM` profiles and has been merged into `main`.

Confirmed behavior:

1. Adds a new `GEOM` profile.
2. Modifies an existing `GEOM` profile.
3. Deletes an unused `GEOM` profile.
4. Preserves existing `GEOM` comments and blank lines where practical.
5. Keeps the `-- add more here` marker as the final entry while it exists.
6. Rejects duplicate profile names on add.
7. Rejects missing profile names on modify or delete.
8. Rejects deletion when `WORKSPACE_PLACEMENT` still references the profile.
9. Provides guarded CLI commands: `add-geom`, `modify-geom`, and `delete-geom`.
10. Preview is the default behavior and writes require `--write`.
11. Writes route through the safe-save helper.

## Completed safe-save proof

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
7. In-memory and guarded CLI add, modify, and delete operations for `GEOM`.
8. In-memory and guarded CLI add, modify, and delete operations for `WORKSPACE_PLACEMENT`.
9. In-memory and guarded CLI add, modify, and delete operations for `WORKSPACE_ROUTES`.
10. In-memory and guarded CLI add, modify, and delete operations for `PIN`.
11. In-memory and guarded CLI add, modify, and delete operations for `EXCLUDE`.
12. In-memory and guarded CLI add, modify, and delete operations for `LEFT_EDGE_CORRECTION`.
13. Marker-tail preservation for `-- add more here` in edited rule-list sections.
14. Token-order-independent rule parsing and modify/delete matching.
15. Exact duplicate target rejection where duplicates would make behavior ambiguous.
16. Read-only GTK launch proof.
17. Read-only active-window capture proof.

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

For the active-window proof, also run the manual desktop check on Qubes/XFCE:

```bash
python -m d2wc configure
d2wc configure
```

Expected result:

1. A window titled `d2wc Configurator` opens.
2. The window states that it is an active-window capture proof only.
3. The window shows the previously active window id, title, class instance, class, Qubes domain, and geometry where available.
4. The close button closes the window.
5. Closing the window manager decoration also exits cleanly.
6. No config files are read or written.

## Next practical work

The current branch is:

```text
configurator-active-window-proof
```

Scope for this branch:

1. Capture the active X11 window before the configurator window appears.
2. Display captured identity and geometry in the GTK proof window.
3. Treat empty `_QUBES_VMNAME` as `dom0`.
4. Keep the proof read-only.
5. Do not perform real config writes from the UI.
6. Do not add rule editing UI yet.

After this branch is reviewed and manually verified, the next practical branch should start a small UI workflow around selecting or previewing a target. That later branch should still avoid config writes by default unless the preview and confirmation path is explicitly implemented and tested.
