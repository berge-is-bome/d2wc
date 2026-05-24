# d2wc Development Status

## Current repository status

Current repository status after PR #23 and during known-window inventory parser work:

```text
Main: 7f4c0141b9a7a7220109ce43c2d65860a6f946dd
Latest merged proof: PR #23, managed-section test-config actions
Current known-window inventory branch: configurator-known-window-inventory
Current parser PR: PR #26, known-window inventory parser foundation
Parallel grid editor branch: configurator-grid-editor-ui
Tracking issue: #17, Build GTK configurator UI around Devilspie2 event data
Draft research PR: PR #16, Devilspie2 window probe proof
```

The CLI/core edit-proof phase is complete for the six managed Lua sections:

1. `GEOM`
2. `WORKSPACE_PLACEMENT`
3. `WORKSPACE_ROUTES`
4. `PIN`
5. `EXCLUDE`
6. `LEFT_EDGE_CORRECTION`

The GTK UI has moved beyond read-only display into a dedicated test-config editor. UI writes are scoped to:

```text
~/.config/devilspie2/d2wc-test.lua
```

The real user config remains out of scope for automatic GTK writes.

## Latest confirmed local verification

Verification reported on PR #26:

```bash
python3 -m d2wc validate --config src/d2wc.lua
python3 -m pytest
```

Result:

```text
The PR branch validation passed.
The full pytest suite passed locally with the known-window inventory parser tests included.
```

Verification reported on PR #23:

```bash
python3 -m d2wc validate --config src/d2wc.lua
python3 -m pytest
python3 -m d2wc configure --test-config
```

Result:

```text
257 pytest tests passed.
The dom0 installed-wheel test was clear.
The managed editor add, modify, delete, Apply, and field-clearing behavior were confirmed.
```

Earlier verification after PR #22 reported:

```text
251 pytest tests passed.
Add GEOM button added event_example to d2wc-test.lua.
Add placement button added d:work c:example g:event_example to d2wc-test.lua.
The GTK action result panel and managed-section display refreshed after writes.
```

Earlier verification after PR #21 reported:

```text
247 pytest tests passed.
d2wc-test.lua was created and read successfully.
--init-test-config, --test-config, and --replace-test-config worked as expected.
```

Earlier verification after PR #20 reported:

```text
238 pytest tests passed.
The GTK event proposal preview and vertical resize behavior worked as expected.
```

## Current UI direction

The active implementation direction is split across separate branches:

1. `configurator-grid-editor-ui` for the workflow-focused grid editor polish.
2. `configurator-known-window-inventory` for known-window inventory parsing, cleanup, and later UI row-source integration.

The first known-window inventory slice adds a parser/model/test foundation only. It does not yet wire live `devilspie2 --debug` capture or GTK Not configured population.

The GTK test-config workflow currently supports:

1. `--init-test-config`
2. `--test-config`
3. `--replace-test-config`
4. `--test-config-path`
5. Managed-section add, modify, and delete for all six sections.
6. Section/action-aware fields.
7. Visible action result text with backup archive path and member names.
8. Automatic reload of displayed test-config sections after writes.

See [Event-Data GTK UI Direction](event-data-ui-direction.md) for the full direction and Devilspie2 function references.

## Known-window inventory parser foundation

The first parser slice adds `src/d2wc/event_inventory.py` and `tests/test_event_inventory.py`.

Current behavior:

1. Parse captured Devilspie2 debug/event text into `KnownWindowCandidate` records.
2. Accept structured keys such as `_QUBES_VMNAME`, `application_name`, `wm_class_instance`, and `window_type`.
3. Accept documented human-readable labels such as `Domain:`, `Application name:`, `Window Type:`, and `Class instance name:`.
4. Keep only `WINDOW_TYPE_NORMAL` records.
5. Normalize an empty Qubes VM name to `dom0`.
6. Normalize machine/domain text to lowercase.
7. Derive an application token from the rightmost class-instance segment after `:`.
8. Preserve the raw class instance value and source block for debugging.

Not included yet:

1. Starting or managing a live `devilspie2 --debug` process.
2. Capturing a long-running event stream.
3. Deduplicating repeated candidates.
4. Feeding GTK Not configured rows.
5. Populating Machine/Application dropdowns.
6. Suppressing candidates already configured for the selected workflow.
7. Handling quoted or whitespace-containing rule tokens in the grammar.

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
16. GTK event-data fixture and command-argument plumbing.
17. Dedicated test-config preparation and loading.
18. Test-config-only generic add, modify, and delete backend for all six managed sections.
19. GTK managed-section editor scoped to `~/.config/devilspie2/d2wc-test.lua`.
20. Known-window inventory parser/model foundation for captured Devilspie2 debug/event text.

## Test command guidance

Install the project in editable mode from the repository root:

```bash
python3 -m pip install -e .
```

Use the four-command renderer verification path when renderer behavior changes:

```bash
python3 -m d2wc validate --config src/d2wc.lua
python3 -m d2wc render --config src/d2wc.lua --stdout > /tmp/d2wc-rendered.lua
python3 -m d2wc validate --config /tmp/d2wc-rendered.lua
python3 -m pytest
```

When renderer behavior has not changed, use this verification path:

```bash
python3 -m d2wc validate --config src/d2wc.lua
python3 -m pytest
```

For the current GTK test-config workflow:

```bash
python3 -m d2wc configure --test-config
```

For a clean GTK test-config baseline:

```bash
python3 -m d2wc configure --replace-test-config
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
7. Create timestamped backup members stored in .bak.tgz archives on successful writes.
8. Re-validate rendered output after edits.
9. Leave the original config unchanged after failed edits.
10. Preserve comments and blank lines where practical.
11. Preserve `-- add more here` marker-tail behavior in edited rule-list sections.
12. Match modify and delete requests by parsed meaning rather than token order where applicable.
13. Reject exact duplicate targets where duplicates would make behavior ambiguous.

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

## Completed proof summary

1. PR #3: safe-save proof.
2. PR #4: `GEOM` edit proof.
3. PR #5: `WORKSPACE_PLACEMENT` edit proof.
4. PR #7, PR #8, PR #9: `WORKSPACE_ROUTES` edit proof and comment preservation fixes.
5. PR #11: `PIN` and `EXCLUDE` edit proof.
6. PR #12: `LEFT_EDGE_CORRECTION` edit proof.
7. PR #13: documentation refresh after managed-section edit proofs.
8. PR #14: first GTK launch proof.
9. PR #15: selected-window geometry diagnostic proof.
10. PR #19: event-data GTK UI proof.
11. PR #20: read-only event proposal preview.
12. PR #21: test-config GTK UI proof.
13. PR #22: test-config proposal action buttons.
14. PR #23: managed-section test-config actions.
15. PR #26: known-window inventory parser foundation.