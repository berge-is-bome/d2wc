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
15. Guarded add, modify, and delete commands for every managed Lua section:
    1. `GEOM`
    2. `WORKSPACE_PLACEMENT`
    3. `WORKSPACE_ROUTES`
    4. `PIN`
    5. `EXCLUDE`
    6. `LEFT_EDGE_CORRECTION`
16. Development status notes in [Development Status](development-status.md).

The Lua script remains the execution layer while the configurator UI is developed.

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
17. Document historical design context and future roadmap items in the repository instead of relying on old conversations.

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
13. Exact duplicate target detection for route, placement, target-rule, and left-edge rule lists.

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

### Stage 9: PIN and EXCLUDE target-rule editing proof

Complete and merged through PR #11.

Completed behavior:

1. Add a new `PIN` rule in memory.
2. Modify an existing `PIN` rule in memory.
3. Delete an existing `PIN` rule in memory.
4. Add a new `EXCLUDE` rule in memory.
5. Modify an existing `EXCLUDE` rule in memory.
6. Delete an existing `EXCLUDE` rule in memory.
7. Preserve comments, blank lines, and marker-tail behavior.
8. Reject exact duplicate targets.
9. Preserve token-order-independent matching.
10. Preview by default and write only with `--write`.
11. Save through the safe-save helper.
12. Expose guarded CLI commands: `add-pin`, `modify-pin`, `delete-pin`, `add-exclude`, `modify-exclude`, and `delete-exclude`.

### Stage 10: LEFT_EDGE_CORRECTION editing proof

Complete and merged through PR #12.

Completed behavior:

1. Add a new `LEFT_EDGE_CORRECTION` rule in memory.
2. Modify an existing `LEFT_EDGE_CORRECTION` rule in memory.
3. Delete an existing `LEFT_EDGE_CORRECTION` rule in memory.
4. Preserve comments, blank lines, and marker-tail behavior.
5. Reject exact duplicate left-edge targets.
6. Preserve token-order-independent matching.
7. Reject missing target prefixes.
8. Reject missing `le:` mode.
9. Reject invalid `le:` modes before rendering.
10. Reject `g:` tokens.
11. Preview by default and write only with `--write`.
12. Save through the safe-save helper.
13. Expose guarded CLI commands: `add-left-edge`, `modify-left-edge`, and `delete-left-edge`.

## Future implementation stages

### Stage 11: first GTK configurator proof

Build the smallest GTK configurator window.

Required behavior:

1. Open from `python -m d2wc configure`.
2. Show a main window.
3. Confirm the window opens cleanly on the Qubes/XFCE target environment.
4. Confirm the window closes cleanly.
5. Keep the first proof read-only.
6. Do not add active-window capture yet.
7. Do not add rule editing UI yet.
8. Do not write any user config from the first UI proof.

Purpose:

1. Prove the GTK/PyGObject dependency path.
2. Prove the source-checkout launch path.
3. Prove that the basic UI can run in the target Qubes/XFCE environment before workflows are built on top of it.

Expected branch:

```text
configurator-gtk-proof
```

### Stage 12: active-window capture proof

Add active-window identity capture.

Required data:

1. Window title.
2. Window type where available.
3. Application class.
4. Class instance where available.
5. Qubes domain from `_QUBES_VMNAME`, if available.
6. Empty `_QUBES_VMNAME` treated as `dom0`.
7. Workspace number where available.
8. Current geometry.
9. Screen geometry where available.

This stage should still avoid writing config changes by default. Its main goal is to prove that the configurator can identify the selected window correctly.

### Stage 13: geometry capture workflow

Implement the first UI-facing config workflow.

Required behavior:

1. Show current geometry as `{ x, y, w, h }`.
2. Let the user save current geometry as a named `GEOM` profile.
3. Suggest a profile name.
4. Warn if the profile already exists.
5. Preview the Lua change.
6. Save only after confirmation.
7. Use the tested `GEOM` core operations and safe-save helper.

### Stage 14: placement rule workflow

Implement the UI-facing `WORKSPACE_PLACEMENT` workflow.

Required behavior:

1. Select an existing `GEOM` profile.
2. Apply that profile to a domain, class, or domain/class target.
3. Preview the generated `WORKSPACE_PLACEMENT` rule.
4. Save only after confirmation.
5. Use the tested placement core operations and safe-save helper.

### Stage 15: workspace route creation workflow

Implement the UI-facing `WORKSPACE_ROUTES` workflow.

Required behavior:

1. Select the target workspace.
2. Route a domain, class, or domain/class target.
3. Preview the generated route.
4. Save only after confirmation.
5. Use the tested route core operations and safe-save helper.

### Stage 16: pin and exclude workflows

Implement UI-facing `PIN` and `EXCLUDE` workflows.

Required behavior:

1. Add or remove pin rules for the selected target.
2. Add or remove exclude rules for the selected target.
3. Show matching existing rules before saving.
4. Preview generated changes.
5. Save only after confirmation.
6. Use the tested target-rule core operations and safe-save helper.

### Stage 17: left-edge correction workflow

Implement a troubleshooting-oriented `LEFT_EDGE_CORRECTION` workflow.

Required behavior:

1. Keep this workflow out of the main first-run path.
2. Test placement at `x = 0`.
3. Try `le:pos1`.
4. Try `le:pos2`.
5. Show the measured result.
6. Save a correction rule only after confirmation.
7. Use the tested left-edge core operations and safe-save helper.

### Stage 18: generated split profiles

Implement generated split-profile support.

Required behavior:

1. Generate common profiles such as `half_left` and `half_right`.
2. Use screen geometry and `window_border_width`.
3. Preview generated `GEOM` entries before writing.
4. Avoid overwriting user profiles without confirmation.
5. Use the tested `GEOM` core operations and safe-save helper.

### Stage 19: reload or restart managed runtime

Implement a safe reload or restart path that applies changed Lua config.

Required behavior:

1. Avoid killing unrelated `devilspie2` processes.
2. Detect the managed process where practical.
3. Provide a manual restart option before automation.
4. Show what will be restarted before doing it.
5. Keep this separate from config rendering and saving.

### Stage 20: post-resize monitoring proof

Begin Phase 2 automation by detecting active-window geometry changes and quiet periods.

Required behavior:

1. Detect geometry changes for the active window.
2. Detect a quiet period after resizing stops.
3. Apply a threshold to avoid noise.
4. Log the final geometry first.
5. Do not open the configurator automatically yet.
6. Do not save rules from this proof.

### Stage 21: post-resize configurator entry

Add user-facing post-resize behavior.

Required behavior:

1. Offer a configure action after a meaningful resize.
2. Avoid interrupting normal desktop use.
3. Provide a cancellation path.
4. Suppress repeat prompts for the same resize action.
5. Reuse the manual configurator workflows.

### Stage 22: packaging proof

Create the first local package proof.

Required behavior:

1. Fedora RPM first.
2. Qubes/dom0 offline installation route documented.
3. Source-checkout workflow remains supported.
4. User config is not overwritten on upgrade.
5. User config is preserved on uninstall.
6. Debian packaging remains a later target.

### Stage 23: future Qt/KDE front end

Keep the architecture UI-toolkit-neutral enough that a future Qt front end can reuse the same backend.

This is a later goal, not part of the current GTK-first proof path.

## Review checkpoints

Review is useful at these points:

1. Before enabling any new UI-driven real user config writes.
2. Before committing to GTK beyond the first UI proof.
3. Before adding active-window capture.
4. Before adding reload/restart behavior.
5. Before adding post-resize automation.
6. Before building the first RPM.
7. Before expanding behavior beyond the Qubes-first target.

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
configurator-gtk-proof
```

Likely next tasks:

1. Add the minimal GTK dependency/import path.
2. Replace the current `configure` placeholder with a small GTK window.
3. Keep the UI proof read-only.
4. Add a basic launch test where practical.
5. Manually verify the window opens and closes on Qubes/XFCE.
6. Keep active-window capture and rule editing UI deferred to later branches.
