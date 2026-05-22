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
8. Python package skeleton for the configurator core.
9. Parser, validator, renderer, settings, split-profile, backup path, duplicate-validation, and shadow-validation tests.
10. Core safe-save helper and temporary-directory tests.
11. Save preview behavior where `save` without `--write` reports the planned save and modifies nothing.
12. Guarded CLI save command requiring `--write` before modifying a config file.
13. Guarded `GEOM` add, modify, and delete commands.
14. Guarded `WORKSPACE_PLACEMENT` add, modify, and delete commands.
15. Guarded `WORKSPACE_ROUTES` add, modify, and delete commands on the `configurator-routes-proof` branch.
16. Development status notes in [Development Status](development-status.md).

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
12. Keep real user configuration writes guarded until safe save behavior is proven with temporary-directory tests.
13. Treat a save as successful only after the staged file, backup file, backup directory, and target directory have all been synced successfully.
14. Make CLI save and edit operations safe by default: preview without writing, and require `--write` before modification.
15. Keep rule parsing token-order-independent, matching the Lua runtime principle that prefixed token order does not matter.

## Stage 0: repository preparation

Stage 0 is complete.

Completed outputs:

1. Initial repository structure.
2. Current Lua script in `src/d2wc.lua`.
3. Core planning documentation.
4. Clear branch and PR for the initial structure and core proof.

## Stage 1: source layout for Python development

Stage 1 is complete.

Current structure:

```text
src/
  d2wc.lua
  d2wc/
    __init__.py
    __main__.py
    cli.py
    core/
      __init__.py
      backup.py
      geom_operations.py
      lua_blocks.py
      managed_config.py
      placement_operations.py
      rendering.py
      route_operations.py
      rule_grammar.py
      saving.py
      section_validation.py
      settings.py
      shadow_validation.py
      split_profiles.py
      validation.py
```

Completed behavior:

1. `python -m d2wc --help` works from the source checkout.
2. `python -m d2wc configure` has a clear placeholder path.
3. The package can be imported without starting a UI.
4. No real user config is modified unless a guarded edit command is run with `--write`.

## Stage 2: Lua managed-block parser

Stage 2 is complete for the current managed sections.

Managed sections:

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

## Stage 3: rule model and validation

Stage 3 is complete for the current core proof.

Completed validation:

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
13. Exact duplicate route target detection for `WORKSPACE_ROUTES`.

Completion criteria:

1. Current Lua script validates cleanly.
2. Invalid sample rules fail with useful messages.
3. Validation logic has no dependency on GTK.

## Stage 4: renderer and safe file writer

Stage 4 is complete for the current CLI/core editing proofs.

Completed renderer behavior:

1. Render deterministic Lua for managed blocks where practical.
2. Keep program logic outside managed blocks intact.
3. Support a dry-run render command through stdout only.
4. Preserve pure note comments and blank separator lines.
5. Align right-side comments in managed rule-list sections.
6. Align `GEOM` numeric columns with minimum width 4 for `x`, `y`, `w`, and `h`.
7. Align right-side comments in `GEOM` entries.
8. Keep `-- add more here` as the final managed table entry while that marker exists.
9. Apply updated rule tuples while preserving comments in rule-list sections.
10. Render `WORKSPACE_ROUTES` workspace rows ordered by workspace number.
11. Insert blank lines between `WORKSPACE_ROUTES` workspace rows.
12. Validate rendered output in the standard renderer verification path.

Completed core safe-save behavior:

1. Render to a temporary file in the target directory.
2. Fsync the temporary file.
3. Validate staged rendered content before replacement.
4. Create a non-overwriting timestamped backup before replacement.
5. Fsync the backup file.
6. Fsync the backup directory.
7. Replace the target file with `os.replace()` only after staging, validation, and backup succeed.
8. Fsync the target directory after replacement.
9. Add temporary-directory tests for success and failure cases.
10. Add preview behavior where `save` without `--write` validates and reports the planned save without modifying files.
11. Add guarded CLI save behavior where real writes require `--write`.
12. Support safe preview and write of supplied edited Lua source.

## Stage 5: safe save proof

Stage 5 is complete and merged through PR #3.

Completed behavior:

1. Accepts an explicit config path in the core helper and CLI save command.
2. Renders to a temporary file in the target directory when saving.
3. Validates the staged rendered file.
4. Creates a timestamped backup of the original file.
5. Replaces the target only after staging, validation, and backup succeed.
6. Leaves the original file intact on validation or backup failure.
7. Cleans up staged temporary files on failure.
8. Uses file and directory fsync calls to reduce power-loss risk.
9. Adds tests using temporary directories only.
10. Previews by default when `save` is run without `--write`.
11. Requires `--write` before CLI save modifies any file.

## Stage 6: GEOM editing proof

Stage 6 is complete and merged through PR #4.

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

## Stage 7: placement rule editing proof

Stage 7 is complete and merged through PR #5.

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

## Stage 8: workspace route editing proof

Stage 8 is complete on the `configurator-routes-proof` branch and ready to merge.

Completed behavior:

1. Add a new `WORKSPACE_ROUTES` rule in memory.
2. Modify an existing `WORKSPACE_ROUTES` rule in memory.
3. Delete an existing `WORKSPACE_ROUTES` rule in memory.
4. Preserve managed Lua program logic outside the route block.
5. Preserve route-row comments where the row still exists.
6. Keep `-- add more here` as the final route-table marker while it exists.
7. Reject exact duplicate route targets across workspace buckets.
8. Allow broader and narrower targets side by side, for example `d:personal` and `d:personal c:navigator`.
9. Reject route rules without a `d:` or `c:` target.
10. Reject route rules containing `g:`.
11. Reject route rules containing `le:`.
12. Match modify and delete requests by parsed rule meaning, not token order.
13. Render edited route rules in canonical prefix order: `d:`, then `c:`.
14. Render workspace rows ordered by workspace number.
15. Insert blank lines between workspace rows.
16. Expose guarded CLI commands: `add-route`, `modify-route`, and `delete-route`.
17. Preview by default and write only with `--write`.
18. Save through the safe-save helper.

Completion criteria:

1. Core tests pass.
2. CLI tests pass.
3. Renderer verification path passes.
4. Manual verification uses a copied temporary config.
5. Backups are created for writes.
6. GTK UI work remains deferred.

## Stage 9: next target-rule editing proof

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

GTK UI work should remain deferred until the current CLI/core editing proofs have been reviewed and merged.

## Stage 10: first GTK configurator proof

Build the smallest GTK configurator window.

Required behavior:

1. Open from `python -m d2wc configure`.
2. Show a main window.
3. Load the managed Lua config from a test path or explicit argument.
4. Show basic parsed sections or a simple status summary.
5. Close cleanly.

Completion criteria:

1. GTK window opens on the target Qubes/XFCE environment.
2. It can be launched from a command.
3. The command can be assigned to a desktop keyboard shortcut.
4. No permanent config changes happen yet.

## Stage 11: active-window capture proof

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

Required behavior:

1. User focuses a window.
2. User runs `d2wc configure` or presses the shortcut.
3. The configurator opens with active-window data preloaded.

Completion criteria:

1. Works on Qubes/XFCE for normal application windows.
2. Handles missing `_QUBES_VMNAME` without failing.
3. Treats empty `_QUBES_VMNAME` as `dom0` where relevant.
4. Refuses or ignores non-normal windows where detectable.

## Stage 12: geometry capture workflow

Implement the first UI-facing geometry workflow.

Required behavior:

1. Show current geometry as `{ x, y, w, h }`.
2. Let the user save current geometry as a named `GEOM` profile.
3. Suggest a profile name.
4. Warn if the profile already exists.
5. Preview the Lua change.
6. Save only after confirmation.
7. Use the tested `GEOM` core operations and safe-save helper.

Completion criteria:

1. User can capture a window's current geometry.
2. New `GEOM` profile appears in the managed Lua file.
3. Backup is created.
4. Validation runs before save.

## Stage 13: placement rule workflow

Implement the UI-facing `WORKSPACE_PLACEMENT` workflow.

Required behavior:

1. Let the user select an existing geometry profile.
2. Let the user choose rule scope.
3. Preview the generated rule.
4. Warn about duplicate or shadowed rules.
5. Save after confirmation.
6. Use the tested placement core operations and safe-save helper.

Completion criteria:

1. User can link a captured profile to the current window.
2. Reopening the application allows the Lua script to place the window.
3. The configurator shows existing matching placement rules.

## Stage 14: workspace route creation workflow

Implement the UI-facing `WORKSPACE_ROUTES` workflow.

Required behavior:

1. Show current workspace.
2. Let the user choose target workspace.
3. Let the user choose rule scope.
4. Append to an existing workspace list instead of creating duplicate workspace keys.
5. Keep route rows ordered by workspace number.
6. Preview and save.

Completion criteria:

1. User can create a route rule.
2. Duplicate workspace table keys are prevented.
3. Matching windows route correctly after reload/restart.

## Stage 15: pin and exclude workflows

Implement simple `PIN` and `EXCLUDE` workflows.

Required behavior:

1. Pin current window by selected scope.
2. Exclude current window by selected scope.
3. Explain that exclusions stop routing, pinning, geometry, and correction.
4. Preview rules before save.

Completion criteria:

1. Pin rules work after reload/restart.
2. Exclude rules short-circuit behavior as expected.
3. Existing matching rules are shown before saving.

## Stage 16: generated split profiles

Implement generated `half_left` and `half_right` profile support.

Required behavior:

1. Read screen or monitor geometry.
2. Read `window_border_width` from settings.
3. Generate matching `half_left` and `half_right` profiles.
4. Show a preview of both generated profiles together.
5. Let the user edit `window_border_width` and preview again.
6. Write generated profiles to `GEOM` only after confirmation.

Completion criteria:

1. The user can generate split profiles without manually calculating border offsets.
2. Updating `window_border_width` changes the generated `x` and `w` values predictably.
3. Generated profile changes are previewed before save.
4. Validation rejects invalid border widths.

## Stage 17: reload or restart managed runtime

Implement a safe reload/restart path.

Required behavior:

1. Avoid killing unrelated `devilspie2` processes.
2. Prefer a managed `d2wc` runtime process.
3. Provide clear success or failure messages.
4. Allow manual reload command.

Possible command:

```bash
d2wc reload
```

Completion criteria:

1. Saved rules can be activated without manual process hunting.
2. Failure leaves the saved file intact and reports the problem clearly.

## Stage 18: left-edge correction test action

Implement the configurator-assisted left-edge test.

Required behavior:

1. Show test action when selected geometry has `x = 0`.
2. Apply normal geometry.
3. Read actual geometry with `get_window_geometry()` or equivalent capture.
4. Detect whether actual `x` differs from requested `x`.
5. Try `pos1` and `pos2` on request.
6. Save the working `LEFT_EDGE_CORRECTION` rule only after confirmation.

Completion criteria:

1. The configurator can detect the left-edge offset.
2. The configurator can identify which correction mode works.
3. The saved rule uses the prefixed grammar.

## Stage 19: post-resize monitoring proof

Begin Phase 2 automation.

Required behavior:

1. Detect active window geometry changes.
2. Determine resize completion using a quiet period.
3. Apply a threshold to ignore tiny changes.
4. Log the captured final geometry.
5. Do not open the configurator yet.

Completion criteria:

1. Resize completion is detected reliably in Qubes/XFCE testing.
2. Automated `d2wc` placements do not trigger false positives, or suppression design is ready.

## Stage 20: post-resize configurator entry

Add user-facing post-resize behavior.

Required behavior:

1. Setting: disabled.
2. Setting: open configurator directly.
3. Setting: show pointer-anchored `Cancel` / `Configure` menu.
4. Suppression for automated placement.
5. Captured geometry preloaded into configurator.

Completion criteria:

1. User can resize a window and open the configurator from the captured geometry.
2. Pointer menu defaults to safe cancellation.
3. Mouse-button swapping is handled or documented.

## Stage 21: packaging proof

Create the first local package proof.

Required behavior:

1. Fedora RPM proof first.
2. Source-checkout workflow remains supported.
3. Local/offline install path is documented for Qubes/dom0.
4. User config is initialized under `~/.config/d2wc/`.
5. Backups/logs go under `~/.local/state/d2wc/`.
6. Uninstall preserves user config by default.

Completion criteria:

1. Local RPM installs on a test Fedora-family system.
2. A Qubes/dom0 offline workflow is documented.
3. The package does not overwrite user-managed Lua rules.

## Stage 22: future Qt/KDE front end

This is not part of the first implementation, but the architecture should keep it possible.

Required design discipline from the beginning:

1. Core parser/writer/validator has no GTK dependency.
2. Window identity and geometry helpers expose toolkit-neutral data.
3. UI actions are represented as operations on the core model.
4. GTK-specific code stays under a GTK UI layer.
5. A future Qt UI can reuse the same backend.

## Review checkpoints

Review is useful at these points:

1. Before merging the read-only core proof.
2. Before enabling any real user config writes.
3. Before committing to GTK after the first UI proof.
4. Before adding reload/restart behavior.
5. Before adding post-resize automation.
6. Before building the first RPM.

## Related documents

1. [Development Status](development-status.md)
2. [UI Flow](ui-flow.md)
3. [Runtime Architecture](runtime-architecture.md)
4. [Testing](testing.md)
5. [Packaging](packaging.md)

## Immediate next implementation tasks

Current branch:

```text
configurator-routes-proof
```

Current status:

1. `WORKSPACE_ROUTES` core add, modify, and delete operations are implemented.
2. Guarded CLI commands are implemented: `add-route`, `modify-route`, and `delete-route`.
3. Route commands preview by default and write only with `--write`.
4. Writes route through the safe-save helper.
5. Route rows render ordered by workspace number with blank lines between rows.
6. Automated verification has passed.
7. Manual route smoke testing used a copied temporary config and led to the route-row layout correction.
8. The branch is ready to merge after final review.

Likely next branch after this merge:

1. Start `PIN` and `EXCLUDE` target-rule add, modify, and delete operations.
2. Keep writes routed through the safe-save helper.
3. Preserve comments, blank lines, and `-- add more here` marker-tail behavior.
4. Keep token-order-independent rule handling.
5. Keep GTK UI work deferred until the target-rule operations are proven through CLI/core tests.

No GTK UI should be built until the current CLI/core editing proofs have been reviewed and merged.
