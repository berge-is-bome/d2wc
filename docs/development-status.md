# d2wc Development Status

## Current repository status

Current repository status after PR #15 and PR #16 research:

```text
Main: dfc6b325923348987cf36986e4fd617c69b61737
Latest merged proof: PR #15, read-only selected-window geometry proof
Draft research PR: PR #16, Devilspie2 window probe proof
Tracking issue: #17, Build GTK configurator UI around Devilspie2 event data
Next planned branch: configurator-event-data-ui-proof
```

The CLI/core edit-proof phase is complete for the six managed Lua sections:

1. `GEOM`
2. `WORKSPACE_PLACEMENT`
3. `WORKSPACE_ROUTES`
4. `PIN`
5. `EXCLUDE`
6. `LEFT_EDGE_CORRECTION`

The GTK launch proof is complete and merged through PR #14.

The selected-window geometry proof is complete and merged through PR #15. It confirmed that a read-only GTK path can run from dom0, call `xwininfo -frame`, and display selected-window geometry. This remains useful diagnostic knowledge, but it is no longer the active UI design direction.

PR #16 remains open as a draft research PR. It should not be merged as-is. The useful result from PR #16 is the design direction captured in [Event-Data GTK UI Direction](event-data-ui-direction.md) and Issue #17.

The current next direction is to build the GTK configurator around event-provided Devilspie2/Lua data rather than blocking UI work on perfect target selection.

## Latest confirmed local verification

Verification reported after PR #15 manual work:

```bash
PYTHONPATH=src python3 -m d2wc configure
```

Result:

```text
The selected-window geometry proof worked from dom0.
The GTK window displayed cleaned geometry fields from the selected window.
No config files were read or written.
```

Earlier source-checkout verification reported after PR #12 follow-up testing:

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

## Current UI direction

The next branch should be:

```text
configurator-event-data-ui-proof
```

Scope for that branch:

1. Accept representative Devilspie2/Lua event data from a Python fixture or command arguments.
2. Open GTK with clear sections for identity and geometry.
3. Display the captured event values.
4. Perform no config writes.
5. Perform no automatic rule generation.
6. Avoid live target-selection experiments in this branch.
7. Keep the UI branch focused on layout and event-data presentation.

Important design decisions:

1. Devilspie2/Lua remains the event source.
2. When a window event occurs, Lua captures the relevant data directly from Devilspie2 functions.
3. If the user chooses the configurator, GTK opens with the captured data from that Lua event.
4. Duplicate configurator launches are acceptable for now, for example one for a menu or launcher event and one for the actual application window event.
5. Later, `d2wc` should suppress automatically opening the configurator for windows that already have a profile, placement rule, route, pin, exclude, or other known handling rule.

See [Event-Data GTK UI Direction](event-data-ui-direction.md) for the full direction and Devilspie2 function references.

## Useful Devilspie2 event data

Start with these event-provided functions:

```lua
get_class_instance_name()
get_window_property( '_QUBES_VMNAME' )
get_screen_geometry()
get_window_geometry()
```

Keep the exact known-working Qubes property call form:

```lua
get_window_property( '_QUBES_VMNAME' )
```

Known behavior:

1. `devilspie2 --debug` prints an initial startup dump for all currently known or processed windows.
2. After startup, `devilspie2 --debug` behaves like an append-only event stream.
3. Capturing the first debug output is not target selection.
4. Capturing the next event after startup is unreliable because menus and launchers can generate intermediary events.
5. The current `d2wc.lua` already filters non-normal windows with `WINDOW_TYPE_NORMAL`.
6. The remaining practical issue is which normal event to act on.
7. For now, accept duplicate configurator openings and rely on later suppression for windows that already have a profile or handling rule.

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

## Completed selected-window geometry proof

PR #15 added a read-only selected-window geometry proof and has been merged into `main`.

Confirmed behavior:

1. `PYTHONPATH=src python3 -m d2wc configure` works from dom0.
2. `xwininfo -frame` changes the pointer and prompts for a target window.
3. Clicking a target window opens the GTK proof window.
4. Cleaned GTK output shows selected-window geometry fields.
5. No config files are read or written.

Important note:

```text
Lua/config requested: y=0
xwininfo can report:  y=46
Likely reason:        XFCE panel/workarea offset
Current decision:     do not compensate yet
```

## Draft PR #16 research outcome

PR #16 explored using Devilspie2 as a direct event-data source.

Current status:

```text
PR #16 is open as a draft.
Do not merge it as-is.
```

Useful research outcomes:

1. Devilspie2 is event-driven.
2. `devilspie2 --debug` emits a startup dump before later event output.
3. Lua can call the needed functions directly.
4. `debug_print` is useful only as a proof mechanism to get values back to Python through stdout.
5. Perfect target selection should not block UI work.
6. The UI should be built around event-provided data and later suppression logic.

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
17. Read-only selected-window geometry proof.

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

For a dom0 source-archive test without editable install, use:

```bash
PYTHONPATH=src python3 -m d2wc configure
```

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
