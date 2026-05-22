# d2wc Implementation Plan

## Purpose

This document turns the current planning documents into an ordered development plan.

The goal is to move from the current Lua-only rules script to a safe manual configurator, then to post-resize automation.

The plan should remain practical and test-driven. Each stage should produce something that can be run, inspected, and corrected before the next stage starts.

## Current baseline

The repository currently contains:

1. `src/d2wc.lua`, the current `devilspie2` Lua rules script.
2. Product and UI flow documentation.
3. Runtime architecture documentation.
4. Technology evaluation documentation.
5. Event monitoring documentation.
6. Left-edge correction testing documentation.
7. Packaging documentation.
8. Lua configurables documentation.
9. Lua design history notes recovered from archived pre-repository script versions.
10. Python package skeleton for the configurator core.
11. Parser, validator, renderer, settings, split-profile, backup path, duplicate-validation, and shadow-validation tests.
12. Core safe-save helper and temporary-directory tests.
13. Save preview behavior where `save` without `--write` reports the planned save and modifies nothing.
14. Guarded CLI save command requiring `--write` before modifying a config file.
15. Guarded `GEOM` add, modify, and delete commands.
16. Guarded `WORKSPACE_PLACEMENT` add, modify, and delete commands.
17. Guarded `WORKSPACE_ROUTES` add, modify, and delete commands.
18. Development status notes in [Development Status](development-status.md).

The Lua script remains the execution layer while the configurator is developed.

## Guiding decisions

The implementation should follow these decisions:

1. Keep `devilspie2` as the active window-rule engine.
2. Keep the Lua script working throughout development.
3. Build a safe manual configurator before post-resize automation.
4. Use Python for the first implementation.
5. Use GTK/PyGObject as the first UI proof target for Qubes/XFCE.
6. Keep PySide6/Qt on the roadmap for KDE-oriented users.
7. Keep parser/writer/validator logic independent from the UI toolkit.
8. Make the stable entry point a command that can be assigned to a keyboard shortcut.
9. Treat tray behavior as optional.
10. Support source-checkout execution because Qubes dom0 is normally offline.
11. Treat generated split-profile settings such as `window_border_width` as configurator/runtime settings, not as ad hoc Lua rule strings.
12. Keep real user configuration writes guarded.
13. Treat a save as successful only after the staged file, backup file, backup directory, and target directory have all been synced successfully.
14. Make CLI save and edit operations safe by default: preview without writing, and require `--write` before modification.
15. Keep rule parsing token-order-independent, matching the Lua runtime principle that prefixed token order does not matter.
16. Keep Qubes OS as the real current target while preserving future non-Qubes design space.
17. Document historical design context in the repository instead of relying on old conversations.

## Completed stages

### Stage 0: repository preparation

Complete.

Completed outputs:

1. Initial repository structure.
2. Current Lua script in `src/d2wc.lua`.
3. Core planning documentation.
4. Archived pre-repository Lua script history connected to `main`.
5. Lua design history notes in [Lua Design History Notes](lua-design-history.md).

### Stage 1: source layout for Python development

Complete.

Completed behavior:

1. `python -m d2wc --help` works from the source checkout.
2. `python -m d2wc configure` has a clear placeholder path.
3. The package can be imported without starting a UI.
4. No real user config is modified unless a guarded command is run with `--write`.

### Stage 2: Lua managed-block parser

Complete for the current managed sections:

1. `EXCLUDE`
2. `PIN`
3. `WORKSPACE_ROUTES`
4. `GEOM`
5. `WORKSPACE_PLACEMENT`
6. `LEFT_EDGE_CORRECTION`

Completed behavior:

1. Reads `src/d2wc.lua`.
2. Locates each managed block.
3. Preserves non-managed Lua program logic outside those blocks.
4. Reports clear errors if a managed block cannot be found or parsed.
5. Test coverage exists for managed-block parsing.

### Stage 3: rule model and validation

Complete for the current CLI/core proof.

Completed validation includes:

1. Valid prefixed grammar: `d:`, `c:`, `g:`, `le:`.
2. No duplicate prefixes inside one rule.
3. Required prefixes per section.
4. No duplicate workspace keys.
5. No unknown geometry profile references.
6. Valid left-edge correction modes.
7. Valid integer geometry values.
8. Valid numeric settings such as `window_border_width`.
9. Duplicate managed target detection.
10. Shadowed-rule detection where currently practical.
11. Useful user-facing error messages.
12. Token-order-independent parsing for prefixed rules.
13. Exact duplicate target detection for route, placement, and related rule lists.

### Stage 4: renderer and safe file writer

Complete for the current CLI/core editing proofs.

Completed renderer behavior includes:

1. Deterministic Lua rendering for managed blocks where practical.
2. Program logic outside managed blocks kept intact.
3. Dry-run render command through stdout.
4. Preservation of pure note comments and blank separator lines where practical.
5. Right-side comment preservation and alignment in managed rule-list sections where supported.
6. `GEOM` numeric column alignment.
7. `WORKSPACE_ROUTES` rows ordered by workspace number.
8. Blank lines between workspace route rows.
9. Marker-tail preservation for `-- add more here` in edited rule-list sections.
10. Rendered output validation in the standard verification path.

Completed safe-save behavior includes:

1. Render to a temporary file in the target directory.
2. Fsync the temporary file.
3. Validate staged rendered content before replacement.
4. Create a non-overwriting timestamped backup before replacement.
5. Fsync the backup file.
6. Fsync the backup directory.
7. Replace the target file with `os.replace()` only after staging, validation, and backup succeed.
8. Fsync the target directory after replacement.
9. Preview behavior where `save` without `--write` validates and reports the planned save without modifying files.
10. Guarded CLI save behavior where real writes require `--write`.

### Stage 5: safe save proof

Complete and merged through PR #3.

### Stage 6: GEOM editing proof

Complete and merged through PR #4.

Completed behavior:

1. Add a new `GEOM` profile in memory.
2. Modify an existing `GEOM` profile in memory.
3. Delete an unused `GEOM` profile in memory.
4. Preserve existing `GEOM` comments and blank lines where practical.
5. Keep `-- add more here` as the final table marker while it exists.
6. Reject duplicate profile names on add.
7. Reject missing profile names on modify or delete.
8. Reject deleting a `GEOM` profile still referenced by `WORKSPACE_PLACEMENT`.
9. Expose guarded CLI commands: `add-geom`, `modify-geom`, and `delete-geom`.
10. Preview by default and write only with `--write`.
11. Save through the safe-save helper.

### Stage 7: WORKSPACE_PLACEMENT editing proof

Complete and merged through PR #5.

Completed behavior:

1. Add a new `WORKSPACE_PLACEMENT` rule in memory.
2. Modify an existing `WORKSPACE_PLACEMENT` rule in memory.
3. Delete an existing `WORKSPACE_PLACEMENT` rule in memory.
4. Preserve existing placement comments and blank lines where practical.
5. Keep `-- add more here` as the final rule-list marker while it exists.
6. Reject duplicate placement targets on add.
7. Reject missing old rules on modify.
8. Reject missing rules on delete.
9. Reject missing `GEOM` profiles on add and modify.
10. Reject placement rules without a `d:` or `c:` target.
11. Reject placement rules without a `g:` profile.
12. Reject placement rules containing `le:`.
13. Match modify and delete requests by parsed rule meaning, not token order.
14. Render edited placement rules in canonical prefix order: `d:`, then `c:`, then `g:`.
15. Expose guarded CLI commands: `add-placement`, `modify-placement`, and `delete-placement`.
16. Preview by default and write only with `--write`.
17. Save through the safe-save helper.

### Stage 8: WORKSPACE_ROUTES editing proof

Complete and merged through PR #7, PR #8, and PR #9 follow-up work.

Completed behavior:

1. Add a new `WORKSPACE_ROUTES` rule in memory.
2. Modify an existing `WORKSPACE_ROUTES` rule in memory.
3. Delete an existing `WORKSPACE_ROUTES` rule in memory.
4. Preserve managed Lua program logic outside the route block.
5. Preserve route-row comments where the row still exists.
6. Preserve standalone comments after multiline route closing comments.
7. Preserve comments after the `-- add more here` marker as marker-tail content.
8. Keep the `-- add more here` marker tail after route rows.
9. Reject exact duplicate route targets across workspace buckets.
10. Allow broader and narrower targets side by side, for example `d:personal` and `d:personal c:navigator`.
11. Reject route rules without a `d:` or `c:` target.
12. Reject route rules containing `g:`.
13. Reject route rules containing `le:`.
14. Match modify and delete requests by parsed rule meaning, not token order.
15. Render edited route rules in canonical prefix order: `d:`, then `c:`.
16. Render workspace rows ordered by workspace number.
17. Insert blank lines between workspace rows.
18. Expose guarded CLI commands: `add-route`, `modify-route`, and `delete-route`.
19. Preview by default and write only with `--write`.
20. Save through the safe-save helper.

Latest reported local verification after PR #9 was `153 passed`.

## Stage 9: PIN and EXCLUDE target-rule editing proof

The next likely CLI/core editing proof is `PIN` and `EXCLUDE` because both are target-rule lists and can reuse the rule-list editing pattern already proven by placement and routes.

Required behavior:

1. Add a target rule.
2. Modify a target rule.
3. Delete a target rule.
4. Preserve comments, blank lines, and marker-tail behavior.
5. Reject exact duplicate targets.
6. Preserve token-order-independent matching.
7. Preview by default and write only with `--write`.
8. Save through the safe-save helper.
9. Preserve Qubes-first runtime assumptions.
10. Avoid broadening dotted/wildcard matching semantics unless that is explicitly chosen and tested.

Expected branch:

```text
configurator-pin-exclude-proof
```

GTK UI work should remain deferred until the current CLI/core editing proofs have been reviewed and merged.

## Later implementation stages

### Stage 10: first GTK configurator proof

Build the smallest GTK configurator window.

Required behavior:

1. Open from `python -m d2wc configure`.
2. Show a main window.
3. Load the managed Lua config from a test path or explicit argument.
4. Show basic parsed sections or a simple status summary.
5. Close cleanly.

### Stage 11: active-window capture proof

Add active-window identity capture.

Required data:

1. Window title.
2. Window type where available.
3. Application class.
4. Class instance where available.
5. Qubes domain from `_QUBES_VMNAME`, if available.
6. Workspace number where available.
7. Current geometry.
8. Screen geometry where available.

### Stage 12: geometry capture workflow

Implement the first UI-facing geometry workflow.

Required behavior:

1. Show current geometry as `{ x, y, w, h }`.
2. Let the user save current geometry as a named `GEOM` profile.
3. Suggest a profile name.
4. Warn if the profile already exists.
5. Preview the Lua change.
6. Save only after confirmation.
7. Use the tested `GEOM` core operations and safe-save helper.

### Stage 13: placement rule workflow

Implement the UI-facing `WORKSPACE_PLACEMENT` workflow.

### Stage 14: workspace route creation workflow

Implement the UI-facing `WORKSPACE_ROUTES` workflow.

### Stage 15: pin and exclude workflows

Implement UI-facing `PIN` and `EXCLUDE` workflows after the CLI/core proof is complete.

### Stage 16: generated split profiles

Implement generated `half_left` and `half_right` profile support.

### Stage 17: reload or restart managed runtime

Implement a safe reload/restart path that avoids killing unrelated `devilspie2` processes.

### Stage 18: left-edge correction test action

Implement the configurator-assisted left-edge test.

### Stage 19: post-resize monitoring proof

Begin Phase 2 automation by detecting active-window geometry changes and quiet periods.

### Stage 20: post-resize configurator entry

Add user-facing post-resize behavior.

### Stage 21: packaging proof

Create the first local package proof, with Fedora RPM first and Qubes/dom0 offline workflow documented.

### Stage 22: future Qt/KDE front end

Keep the architecture UI-toolkit-neutral enough that a future Qt front end can reuse the same backend.

## Review checkpoints

Review is useful at these points:

1. Before enabling any new real user config writes.
2. Before committing to GTK after the first UI proof.
3. Before adding reload/restart behavior.
4. Before adding post-resize automation.
5. Before building the first RPM.
6. Before expanding behavior beyond the Qubes-first target.

## Related documents

1. [Development Status](development-status.md)
2. [UI Flow](ui-flow.md)
3. [Runtime Architecture](runtime-architecture.md)
4. [Testing](testing.md)
5. [Packaging](packaging.md)
6. [Lua Configurables](lua-configurables.md)
7. [Lua Design History Notes](lua-design-history.md)

## Immediate next implementation tasks

Current branch recommendation:

```text
configurator-pin-exclude-proof
```

Likely next tasks:

1. Add `PIN` add, modify, and delete operations.
2. Add `EXCLUDE` add, modify, and delete operations.
3. Keep writes routed through the safe-save helper.
4. Preserve comments, blank lines, and `-- add more here` marker-tail behavior.
5. Keep token-order-independent rule handling.
6. Keep GTK UI work deferred until the target-rule operations are proven through CLI/core tests.
