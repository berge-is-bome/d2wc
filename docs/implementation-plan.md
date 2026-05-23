# d2wc Implementation Plan

## Purpose

This document turns the current planning documents into an ordered development plan.

The goal is to move from the current Lua rules script to a safe GTK configurator, then to event-driven configuration workflows and post-resize automation.

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
16. Read-only GTK launch proof.
17. Read-only Qubes/dom0 selected-window geometry proof.
18. Event-data UI direction notes in [Event-Data GTK UI Direction](event-data-ui-direction.md).
19. Dedicated GTK test-config workflow using `~/.config/devilspie2/d2wc-test.lua`.
20. GTK add/delete form for all six managed sections, scoped to the test config.
21. Development status notes in [Development Status](development-status.md).

The Lua script remains the execution layer while the configurator UI is developed.

## Guiding decisions

The implementation should follow these decisions:

1. Keep `devilspie2` as the active window-rule engine.
2. Keep the Lua script working throughout development.
3. Build a safe manual/configurator UI before post-resize automation.
4. Use Python for the first implementation.
5. Use GTK/PyGObject as the first UI proof target for Qubes/XFCE.
6. Keep PySide6/Qt on the roadmap for KDE-oriented users.
7. Keep parser/writer/validator logic independent from the UI toolkit.
8. Make the stable entry point a command that can be assigned to a keyboard shortcut or called from the Lua event context.
9. Treat tray behavior as optional.
10. Support source-checkout execution because Qubes dom0 is normally offline.
11. Treat generated split-profile settings such as `window_border_width` as configurator/runtime settings, not as ad hoc Lua rule strings.
12. Keep real user configuration writes guarded.
13. Treat a save as successful only after the staged file, backup file, backup directory, and target directory have all been synced successfully.
14. Make CLI save and edit operations safe by default: preview without writing, and require `--write` before modification.
15. Keep rule parsing token-order-independent, matching the Lua runtime principle that prefixed token order does not matter.
16. Keep Qubes OS as the real current target while preserving future non-Qubes design space.
17. Document historical design context and future roadmap items in the repository instead of relying on old conversations.
18. Build the GTK UI around representative Devilspie2/Lua event data, not around live target-selection experiments.
19. Accept duplicate configurator openings for intermediary events for now; later suppression should prevent automatic configurator launches for already-known windows.
20. Use `~/.config/devilspie2/d2wc-test.lua` as the GTK UI write target until the real-config write workflow has its own explicit review.

## Completed stages

### Stage 0: repository preparation

Complete.

### Stage 1: source layout for Python development

Complete.

### Stage 2: Lua managed-block parser

Complete for the current managed sections:

1. `EXCLUDE`
2. `PIN`
3. `WORKSPACE_ROUTES`
4. `GEOM`
5. `WORKSPACE_PLACEMENT`
6. `LEFT_EDGE_CORRECTION`

### Stage 3: rule model and validation

Complete for the current CLI/core proof.

Completed validation includes prefixed grammar, duplicate-prefix checks, required prefixes per section, duplicate target detection, shadow checks where practical, and token-order-independent parsing.

### Stage 4: renderer and safe file writer

Complete for the current CLI/core editing proofs.

Completed behavior includes deterministic managed-block rendering, comment preservation where practical, marker-tail preservation, safe-save staging, validation before replacement, timestamped backups, and `--write` guarded writes.

### Stage 5: safe save proof

Complete and merged through PR #3.

### Stage 6: GEOM editing proof

Complete and merged through PR #4.

### Stage 7: WORKSPACE_PLACEMENT editing proof

Complete and merged through PR #5.

### Stage 8: WORKSPACE_ROUTES editing proof

Complete and merged through PR #7, PR #8, and PR #9 follow-up work.

### Stage 9: PIN and EXCLUDE target-rule editing proof

Complete and merged through PR #11.

### Stage 10: LEFT_EDGE_CORRECTION editing proof

Complete and merged through PR #12.

### Stage 11: documentation refresh after managed-section edit proofs

Complete and merged through PR #13.

### Stage 12: first GTK configurator proof

Complete and merged through PR #14.

Confirmed behavior:

1. `python -m d2wc configure` opens a GTK window.
2. `d2wc configure` opens the same GTK window after editable install refresh.
3. The window closes cleanly.
4. No config files are read or written.
5. No rule editing UI is included.

### Stage 13: selected-window geometry diagnostic proof

Complete and merged through PR #15.

Confirmed behavior:

1. The proof can run from dom0.
2. `xwininfo -frame` can prompt for a selected window.
3. GTK can display cleaned selected-window geometry fields.
4. No config files are read or written.

Design outcome:

1. The proof is useful as a diagnostic.
2. It is not the active long-term UI direction.
3. The active UI direction now uses event-provided Devilspie2/Lua data.

### Stage 14: Devilspie2 probe research

PR #16 is open as a draft research PR and should not be merged as-is.

Research outcomes:

1. Devilspie2/Lua is the correct runtime source for event data.
2. `devilspie2 --debug` prints an initial startup dump before later event output.
3. Capturing the first debug output is not target selection.
4. Capturing the next event after startup is unreliable because intermediary UI windows can emit events first.
5. Lua can call the needed functions directly.
6. `debug_print` is only needed when a proof needs to emit values to Python through stdout.
7. Perfect target selection should not block UI work.
8. Duplicate configurator launches are acceptable for now and should later be reduced through suppression of already-known windows.

See [Event-Data GTK UI Direction](event-data-ui-direction.md).

### Stage 15: event-data GTK UI proof

Complete and merged through PR #19.

Confirmed behavior:

1. Representative event data can be passed through a fixture or command arguments.
2. GTK displays identity and geometry sections.
3. No live target-selection experiments are included.
4. No config writes are included.

### Stage 16: read-only event proposal preview

Complete and merged through PR #20.

Confirmed behavior:

1. GTK displays an event-derived `GEOM` proposal.
2. GTK displays an event-derived `WORKSPACE_PLACEMENT` proposal.
3. Optional config read-only inspection reports existing matches.
4. A copy-proposal button is available.
5. Vertical resizing works through a scrollable content area.

### Stage 17: test-config GTK UI proof

Complete and merged through PR #21.

Confirmed behavior:

1. `--init-test-config` creates the dedicated test config when missing.
2. `--test-config` loads the existing test config.
3. `--replace-test-config` resets the test config from bundled `src/d2wc.lua`.
4. `--test-config-path` supports disposable paths for tests and experiments.
5. GTK displays all six managed sections from the test config.

### Stage 18: test-config proposal action buttons

Complete and merged through PR #22.

Confirmed behavior:

1. `Add GEOM` adds the event-derived `GEOM` profile to the test config.
2. `Add placement` adds the event-derived `WORKSPACE_PLACEMENT` rule to the test config.
3. `Add both` applies both actions in sequence.
4. The action-result panel reports success or error and backup path.
5. The managed-section display refreshes after writes.

### Stage 19: managed-section add/delete UI for the test config

Current branch: `configurator-managed-section-actions`.

Required behavior:

1. Keep all writes scoped to the loaded test config.
2. Add a GTK managed-section form for all six sections.
3. Support add and delete operations.
4. Reuse tested core edit operations and safe-save behavior.
5. Refresh displayed sections after each write.
6. Update documentation to match the current workflow.

## Future implementation stages

### Stage 20: event-data handoff proof from Lua to Python

After the UI layout and test-config editing workflow are proven, prove the handoff path from Lua event data to the configurator command.

Required behavior:

1. Lua captures event data directly from Devilspie2 functions.
2. Lua passes the event data to the configurator command through a safe handoff mechanism.
3. GTK displays exactly the event data it received.
4. Writes remain scoped to the selected development path until real-config write workflow is reviewed.

### Stage 21: suppression for already-known windows

Add logic to avoid automatically opening the configurator for windows that already have a profile or handling rule.

Candidate known handling rules:

1. `WORKSPACE_PLACEMENT`
2. `WORKSPACE_ROUTES`
3. `PIN`
4. `EXCLUDE`
5. `LEFT_EDGE_CORRECTION`

Purpose:

1. Allow duplicate configurator launches early.
2. Let the user configure intermediary menu/launcher events once.
3. Suppress repeated prompts for already-known windows later.
4. Make the real application-window configurator flow less noisy over time.

### Stage 22: real-config write review

Before enabling real user config writes in GTK, review:

1. Which config path is considered the active real user config.
2. How the UI shows the target path.
3. Whether real writes require a separate explicit mode.
4. Whether real writes should require a final confirmation dialog.
5. How backups are surfaced to the user.
6. Whether the UI should provide a restore-from-backup workflow.

### Stage 23: generated split profiles

Implement generated split-profile support.

### Stage 24: reload or restart managed runtime

Implement a safe reload or restart path that applies changed Lua config.

### Stage 25: post-resize monitoring proof

Begin Phase 2 automation by detecting active-window geometry changes and quiet periods.

Important note:

Devilspie2/Lua scripts are event-driven and should not be treated as the live resize monitor. Live move/resize tracking probably belongs in an X11/window-manager layer after a target window is known.

### Stage 26: post-resize configurator entry

Add user-facing post-resize behavior.

### Stage 27: packaging proof

Create the first local package proof.

Required behavior:

1. Fedora RPM first.
2. Qubes/dom0 offline installation route documented.
3. Source-checkout workflow remains supported.
4. User config is not overwritten on upgrade.
5. User config is preserved on uninstall.
6. Debian packaging remains a later target.

### Stage 28: future Qt/KDE front end

Keep the architecture UI-toolkit-neutral enough that a future Qt front end can reuse the same backend.

This is a later goal, not part of the current GTK-first proof path.

## Review checkpoints

Review is useful at these points:

1. Before enabling any new UI-driven real user config writes.
2. Before committing to GTK beyond the first UI proof.
3. Before adding event-data handoff from Lua to Python.
4. Before adding reload/restart behavior.
5. Before adding post-resize automation.
6. Before building the first RPM.
7. Before expanding behavior beyond the Qubes-first target.

## Related documents

1. [Development Status](development-status.md)
2. [Event-Data GTK UI Direction](event-data-ui-direction.md)
3. [UI Flow](ui-flow.md)
4. [Runtime Architecture](runtime-architecture.md)
5. [Testing](testing.md)
6. [Packaging](packaging.md)
7. [Lua Configurables](lua-configurables.md)
8. [Lua Design History Notes](lua-design-history.md)

## Immediate next implementation tasks

Current branch recommendation:

```text
configurator-managed-section-actions
```

Likely next tasks:

1. Pull the branch and run the full test suite.
2. Smoke-test `--replace-test-config` from the source checkout.
3. Add and delete one entry in each managed section through the GTK form.
4. Confirm the displayed sections refresh after each write.
5. Confirm backups are created for test-config writes.
