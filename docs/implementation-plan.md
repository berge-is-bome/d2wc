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
11. Parser, validator, renderer, settings, split-profile, backup archive path and member name, duplicate-validation, and shadow-validation tests.
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
20. GTK managed-section editor for all six managed sections, scoped to the test config.
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
10. Support source-checkout execution because Qubes dom0 is often offline.
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
21. Query the current X11 workspace count for the GTK workspace selector when possible, falling back to workspaces `1` through `4` only when the desktop does not report a count.

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

Completed behavior includes deterministic managed-block rendering, comment preservation where practical, marker-tail preservation, safe-save staging, validation before replacement, timestamped backup members stored in .bak.tgz archives, and `--write` guarded writes.

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

1. `python3 -m d2wc configure` opens a GTK window.
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
4. The action-result panel reports success or error and backup archive path and member name.
5. The managed-section display refreshes after writes.

### Stage 19: managed-section editor for the test config

Complete and merged through PR #23.

Confirmed behavior:

1. All writes are scoped to `~/.config/devilspie2/d2wc-test.lua`.
2. GTK can add, modify, and delete entries for all six managed sections.
3. The editor reuses tested core edit operations and safe-save behavior.
4. The editor uses section/action-aware fields.

## Future implementation stages

### Stage 20: grid-style GTK editor

Current branch: `configurator-grid-editor-ui`.

Required behavior:

1. Use one section-focused editor area instead of separate configured, known-window, and selected-row panels.
2. Show normalized workflow labels such as `Window geometry` instead of raw all-caps section names.
3. Use searchable popup selectors for rule parts where the list can grow.
4. Split prefixed rules into separate editable fields, for example `Domain`, `Class`, `Window geometry`, and `Left edge`, instead of exposing `d:`, `c:`, `g:`, and `le:` as one combined string.
5. Keep the full original rule hidden for modify and delete matching.
6. Use separate editable rule-part fields for both new rows and existing configured rows.
7. Query the current X11 workspace count for the workspace selector when possible, falling back to workspaces `1` through `4` only if the desktop count is unavailable.
8. Writes remain scoped to `~/.config/devilspie2/d2wc-test.lua` until the real-config workflow is reviewed.

### Stage 21: known-window inventory from Devilspie2 event data

Build the list of known normal windows from Devilspie2/Lua event data.

Required behavior:

1. Capture `WINDOW_TYPE_NORMAL` windows from Devilspie2/Lua event data.
2. Extract and normalize the Qubes VM name as the domain value.
3. Extract and normalize the class token from `get_class_instance_name()`.
4. Suppress entries already known to the selected workflow.
5. Populate not-configured UI rows from the cleaned inventory.

### Stage 22: real-config write review

Do not enable real user config writes until this review is complete.

Required behavior:

1. Define explicit user confirmation behavior.
2. Define backup retention behavior.
3. Define recovery behavior.
4. Confirm whether writes go directly to the active script or through a staged promotion flow.
