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

## Stage 0: repository preparation

Stage 0 is mostly complete in the current draft PR.

Required outputs:

1. Initial repository structure.
2. Current Lua script in `src/d2wc.lua`.
3. Core planning documentation.
4. A clear branch and PR for the initial structure.

Completion criteria:

1. The PR contains the Lua script and planning docs.
2. The docs agree on GTK-first, Python-first, command/shortcut-first direction.
3. The PR remains reviewable and mergeable.

## Stage 1: source layout for Python development

Create the initial Python package layout without building the full UI yet.

Proposed structure:

```text
src/
  d2wc.lua
  d2wc/
    __init__.py
    __main__.py
    cli.py
    core/
      __init__.py
      config_model.py
      lua_blocks.py
      validation.py
      rendering.py
      backup.py
    window/
      __init__.py
      active_window.py
      geometry.py
    ui/
      __init__.py
      gtk/
        __init__.py
        main_window.py
```

Required behavior:

1. `python -m d2wc --help` works from the source checkout.
2. `python -m d2wc configure` starts a placeholder configurator or prints a clear placeholder message.
3. The package can be imported without starting the UI.

Completion criteria:

1. CLI command exists.
2. Core modules import cleanly.
3. No real user config is modified.

## Stage 2: Lua managed-block parser

Build the parser that reads the known managed sections from the Lua script.

Managed sections:

1. `EXCLUDE`
2. `PIN`
3. `WORKSPACE_ROUTES`
4. `GEOM`
5. `WORKSPACE_PLACEMENT`
6. `LEFT_EDGE_CORRECTION`

Required behavior:

1. Read `src/d2wc.lua`.
2. Locate each managed block.
3. Parse block content into structured Python objects.
4. Preserve non-managed Lua program logic outside those blocks.
5. Report clear errors if a managed block cannot be found or parsed.

Completion criteria:

1. Parser can read the current `src/d2wc.lua`.
2. Parsed data matches the current Lua configuration.
3. Unit tests cover the current script and at least one malformed block.

## Stage 3: rule model and validation

Build the internal model for rules and validation.

Required validation:

1. Valid prefixed grammar: `d:`, `c:`, `g:`, `le:`.
2. No duplicate prefixes inside one rule.
3. Required prefixes per section.
4. No duplicate workspace keys.
5. No unknown geometry profile references.
6. Valid left-edge correction modes.
7. Valid integer geometry values.
8. Useful user-facing error messages.

Completion criteria:

1. Current Lua script validates cleanly or reports only intentional test/sample issues.
2. Invalid sample rules fail with useful messages.
3. Validation logic has no dependency on GTK.

## Stage 4: renderer and safe file writer

Build the renderer that writes managed blocks back to Lua.

Required behavior:

1. Render deterministic Lua for managed blocks.
2. Keep program logic outside managed blocks intact.
3. Create a backup before saving.
4. Write to a temporary file first.
5. Replace the target file only after successful render/write.
6. Support a dry-run or preview mode.

Completion criteria:

1. Parse and render the current file without changing semantics.
2. Backup is created before write.
3. Dry-run output can be inspected.
4. Tests use temporary files, not the user's real config.

## Stage 5: first GTK configurator proof

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

## Stage 6: active-window capture proof

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

## Stage 7: geometry capture and profile creation

Implement the first useful configurator action.

Required behavior:

1. Show current geometry as `{ x, y, w, h }`.
2. Let the user save current geometry as a named `GEOM` profile.
3. Suggest a profile name.
4. Warn if the profile already exists.
5. Preview the Lua change.
6. Save only after confirmation.

Completion criteria:

1. User can capture a window's current geometry.
2. New `GEOM` profile appears in the managed Lua file.
3. Backup is created.
4. Validation runs before save.

## Stage 8: placement rule creation

Implement `WORKSPACE_PLACEMENT` creation.

Required behavior:

1. Let the user select an existing geometry profile.
2. Let the user choose rule scope:
   1. Domain and class.
   2. Class everywhere.
   3. Domain generally.
3. Preview the generated rule.
4. Warn about duplicate or shadowed rules.
5. Save after confirmation.

Completion criteria:

1. User can link a captured profile to the current window.
2. Reopening the application allows the Lua script to place the window.
3. The configurator shows existing matching placement rules.

## Stage 9: workspace route creation

Implement `WORKSPACE_ROUTES` creation.

Required behavior:

1. Show current workspace.
2. Let the user choose target workspace.
3. Let the user choose rule scope.
4. Append to an existing workspace list instead of creating duplicate workspace keys.
5. Preview and save.

Completion criteria:

1. User can create a route rule.
2. Duplicate workspace table keys are prevented.
3. Matching windows route correctly after reload/restart.

## Stage 10: pin and exclude rules

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

## Stage 11: reload or restart managed runtime

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

## Stage 12: left-edge correction test action

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

## Stage 13: post-resize monitoring proof

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

## Stage 14: post-resize configurator entry

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

## Stage 15: packaging proof

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

## Stage 16: future Qt/KDE front end

This is not part of the first implementation, but the architecture should keep it possible.

Required design discipline from the beginning:

1. Core parser/writer/validator has no GTK dependency.
2. Window identity and geometry helpers expose toolkit-neutral data.
3. UI actions are represented as operations on the core model.
4. GTK-specific code stays under a GTK UI layer.
5. A future Qt UI can reuse the same backend.

Completion criteria for this stage later:

1. Qt proof opens the same core model.
2. Qt UI can preview and save the same managed Lua changes.
3. KDE-oriented behavior is documented separately if needed.

## Review checkpoints

Review is useful at these points:

1. Before merging the initial documentation PR.
2. Before committing to GTK after the first UI proof.
3. Before the parser/writer is allowed to modify a real user Lua file.
4. Before adding reload/restart behavior.
5. Before adding post-resize automation.
6. Before building the first RPM.

## Immediate next implementation tasks

After the initial documentation PR is merged, the next branch should likely be:

```text
configurator-core-proof
```

First tasks on that branch:

1. Create Python package skeleton.
2. Add CLI entry point.
3. Add parser for managed Lua blocks.
4. Add validation model.
5. Add tests using `src/d2wc.lua` as the fixture.
6. Add a dry-run render command.

No GTK UI should be built until the parser/validator can safely read the current Lua script.
