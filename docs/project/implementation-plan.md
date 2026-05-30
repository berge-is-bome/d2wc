# d2wc Implementation Plan

## Purpose

This document turns the current planning documents into an ordered development plan.

The goal is to move from the current Lua rules script to a safe GTK configurator, then to event-driven configuration workflows and post-resize automation.

The plan should remain practical and test-driven. Each stage should produce something that can be run, inspected, and corrected before the next stage starts.

## Current baseline

The repository currently contains:

1. `src/d2wc.lua`, the bundled `devilspie2` Lua rules template.
2. [Product Development Brief](product-development-brief.md) and [UI Flow](ui-flow.md) documentation.
3. [Runtime Architecture](runtime-architecture.md) documentation.
4. [Technology Evaluation](technology-evaluation.md) documentation.
5. [Event Monitoring](event-monitoring.md) documentation.
6. [Left-Edge Correction Testing](left-edge-correction-testing.md) documentation.
7. [Packaging](packaging.md) documentation.
8. [Lua Configurables](lua-configurables.md) documentation.
9. [Lua Design History Notes](lua-design-history.md) recovered from archived pre-repository script versions.
10. [Managed Config Workflow](managed-config-workflow.md) documentation for the installed user-path model.
11. [Lua Event Handoff](lua-event-handoff.md) documentation for automatic window-event launching.
12. Python package skeleton for the configurator core.
13. Parser, validator, renderer, settings, split-profile, backup archive path and member name, duplicate-validation, shadow-validation, and managed-user-path tests.
14. Core safe-save helper and temporary-directory tests.
15. Save preview behavior where `save` without `--write` reports the planned save and modifies nothing.
16. Guarded CLI save command requiring `--write` before modifying a config file.
17. Guarded add, modify, and delete commands for every managed Lua section:
    1. `GEOM`
    2. `WORKSPACE_PLACEMENT`
    3. `WORKSPACE_ROUTES`
    4. `PIN`
    5. `EXCLUDE`
    6. `LEFT_EDGE_CORRECTION`
18. Read-only GTK launch proof.
19. Read-only Qubes/dom0 selected-window geometry proof.
20. Event-data UI direction notes in [Event-Data GTK UI Direction](event-data-ui-direction.md).
21. Dedicated GTK test-config workflow for isolated development tests.
22. Workflow-focused GTK grid editor for all six managed sections.
23. Known-window inventory parser foundation in `src/d2wc/event_inventory.py`.
24. Known-window row-source helpers in `src/d2wc/ui/grid_rows.py`.
25. Bounded and continuous known-window inventory capture helpers in `src/d2wc/event_inventory_capture.py`.
26. Automatic GTK known-window inventory monitor integration.
27. Qubes/dom0 source-archive installation and update helper scripts.
28. Installed `d2wc` command that opens the GTK configurator directly.
29. Managed-config GTK editor for the active `d2wc` managed Lua file.
30. File Open and Save As for `d2wc` managed Lua files.
31. XDG-style user paths for source cache, installed source, managed Lua files, and UI settings.
32. Lua event handoff from managed Lua to the bare `d2wc` command.
33. Configured-window suppression for automatic handoff.
34. `Menu -> Configure -> Behavior` settings for automatic handoff and entry-point selection.
35. `d2wc prompt` as an optional event handoff entry point.
36. `local D2WC_MANAGED = true` as the required managed Lua marker.
37. Development status notes in [Development Status](development-status.md).

The Lua script remains the execution layer. User-owned managed Lua files live under `~/.config/d2wc/lua/`, and Devilspie2 reads the active managed file through the integration symlink at `~/.config/devilspie2/d2wc.lua`.

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
9. Treat tray behavior as optional future work.
10. Support source-checkout execution because Qubes dom0 is often offline.
11. Treat generated split-profile settings such as `window_border_width` as configurator/runtime settings, not as ad hoc Lua rule strings.
12. Keep real user configuration writes guarded.
13. Treat a save as successful only after the staged file, backup file, backup directory, and target directory have all been synced successfully.
14. Make CLI save and edit operations safe by default: preview without writing, and require `--write` before modification.
15. Keep rule parsing token-order-independent, matching the Lua runtime principle that prefixed token order does not matter.
16. Keep Qubes OS as the real current target while preserving future non-Qubes design space.
17. Document historical design context and future roadmap items in the repository instead of relying on old conversations.
18. Build the GTK UI around real Devilspie2/Lua event data when event data is available, not around live target-selection experiments.
19. Keep representative event fixtures available for tests and manual experiments, but do not inject them into normal `d2wc` launches.
20. Allow automatic configurator launching only for unconfigured normal windows when the user enables the Lua event handoff setting.
21. Let the user choose whether automatic handoff opens the configurator directly or shows the prompt first.
22. Use dedicated test-config paths for isolated GTK UI testing.
23. Store user-owned managed Lua files under `~/.config/d2wc/lua/`.
24. Use `~/.config/devilspie2/d2wc.lua` only as the Devilspie2-facing integration symlink for the active managed file.
25. Do not overwrite unrelated Devilspie2 Lua scripts or unrelated symlinks.
26. Keep File Open and Save As scoped to `d2wc` managed Lua files, not arbitrary Devilspie2 scripts.
27. Query the current X11 workspace count for the GTK workspace selector, falling back to workspace 1 when the count cannot be read.
28. Build the known-window inventory in small testable slices: parser first, row source and suppression second, bounded and continuous capture third, GTK live refresh last.
29. Keep installer managed-Lua refreshes targeted; do not rewrite whole user-managed Lua files from the bundled template.
30. Treat `local D2WC_MANAGED = true` as executable marker state, not as removable documentation.

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

Completed behavior includes deterministic managed-block rendering, comment preservation where practical, marker-tail preservation, safe-save staging, validation before replacement, timestamped backup members stored in `.bak.tgz` archives, and `--write` guarded writes.

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

PR #16 was kept as draft research and should not be merged as-is.

Research outcomes:

1. Devilspie2/Lua is the correct runtime source for event data.
2. `devilspie2 --debug` prints an initial startup dump before later event output.
3. Capturing the first debug output is not target selection.
4. Capturing the next event after startup is unreliable because intermediary UI windows can emit events first.
5. Lua can call the needed functions directly.
6. `debug_print` is only needed when a proof needs to emit values to Python through stdout.
7. Perfect target selection should not block UI work.
8. Duplicate configurator launches are acceptable only for intermediary proof stages and should be reduced through suppression of already-known windows.

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

1. All writes are scoped to the configured test file.
2. GTK can add, modify, and delete entries for all six managed sections.
3. The editor reuses tested core edit operations and safe-save behavior.
4. The editor uses section/action-aware fields.

### Stage 20: grid-style GTK editor

Complete and merged through PR #27.

Confirmed behavior:

1. The workflow-focused grid editor is the active UI.
2. Rows are wrapped and aligned with GTK size groups.
3. Action row colours are:
   1. `Add` = green
   2. `Modify` = purple
   3. `Delete` = red
4. Dirty rows split the action area:
   1. left half: amber `Undo`
   2. right half: action-coloured `Apply`
5. Successful apply actions show a compact translucent toast.
6. Errors and validation failures still use blocking dialogs.
7. Workspace selector reads the X11 workspace count when available.
8. Workspace fallback is workspace 1 only.
9. Configurator publishes stable GTK/X11 class `d2wc-configurator`.
10. Per-workflow help is available from the menu.

### Stage 21: known-window inventory parser foundation

Complete through PR #26.

Current parser foundation behavior:

1. Parse captured Devilspie2 debug/event text into `KnownWindowCandidate` records.
2. Accept structured keys such as `_QUBES_VMNAME`, `application_name`, `wm_class_instance`, and `window_type`.
3. Accept documented human-readable probe labels such as `Domain:`, `Application name:`, `Window Type:`, and `Class instance name:`.
4. Keep only `WINDOW_TYPE_NORMAL` candidates.
5. Normalize an empty Qubes VM name to `dom0`.
6. Normalize machine/domain text to lowercase.
7. Derive an application token from the rightmost class-instance segment after `:`.
8. Preserve the raw class instance value and source block for debugging.

### Stage 22: known-window inventory row source

Complete through PR #28.

Current row-source behavior:

1. Convert repeated candidate observations into one selectable rule target where they describe the same machine/application target.
2. Do not display observation counts, because repeated entries in `devilspie2 --debug` output are normal.
3. Skip unsafe whitespace-containing rule tokens until the grammar supports them.
4. Suppress targets already configured for the selected workflow where practical.
5. Use inventory targets to populate Machine/Application dropdown values for target-based workflows.
6. Do not create `GEOM` suggestions from inventory targets, because this inventory slice only carries machine/application data.
7. Expose a clean row-builder interface for GTK without coupling GTK to raw debug text parsing.

The row-source logic lives in `src/d2wc/ui/grid_rows.py`, while `src/d2wc/ui/managed_actions.py` remains focused on GTK widget assembly and row control behavior.

### Stage 23: bounded and continuous Devilspie2 inventory capture

Complete through PR #28.

Current behavior:

1. Use a temporary read-only probe Lua script rather than the active `d2wc.lua` rules script.
2. Print only the values needed for inventory, currently domain/machine, class instance, and window type.
3. Provide a bounded startup snapshot helper for initial inventory capture.
4. Treat startup output as inventory input, not as target selection.
5. Provide `KnownWindowInventoryStreamParser` for continuous debug output.
6. Allow later debug output to add newly opened domain/class pairs while the monitor is running.
7. Return parsed `KnownWindowTarget` values through core APIs.
8. Avoid persistent changes to the user's real Devilspie2 config.
9. Terminate the temporary Devilspie2 process when the GTK monitor is stopped.

### Stage 24: automatic GTK inventory monitor integration

Complete through PR #28 and the `lua-event-handoff` branch cleanup.

Current behavior:

1. Start the inventory monitor automatically when the GTK configurator opens.
2. Use startup debug output to populate initial Machine/Application dropdown values.
3. Use later debug-output events to add newly seen domain/class values while the configurator remains open.
4. Merge captured targets into editor state while preserving first-seen order.
5. Remove the separate Not configured mode.
6. Keep one top `Add` row per workflow, with configured rows below it.
7. Feed captured machine/application values into the top `Add` row dropdowns.
8. Stop the monitor when the GTK window closes.
9. Stop the stream through a stop event so temporary inventory processes do not accumulate.
10. Keep status visibility and non-blocking monitor error UX as future polish.

### Stage 25: installed command and first public Qubes installer polish

Complete through PR #29.

Current behavior at that historical stage:

1. `d2wc` opens the GTK configurator directly.
2. `d2wc configure` remains available as an explicit subcommand.
3. The dom0 installer creates a managed config only when missing.
4. Existing Devilspie2 scripts are not overwritten.
5. The Qubes/dom0 source-archive installer supports user-site installation without dom0 network access.
6. Normal `Apply` buttons match the width of dirty `Undo` / `Apply` rows.

### Stage 26: public-release documentation refresh

Complete through PR #30.

Current behavior:

1. README is a public-facing description of what `d2wc` is.
2. User documentation lives under `docs/user/`.
3. Project documentation lives under `docs/project/`.
4. The Qubes install guide is the public install/update entry point.
5. README points users to [Install/Update for Qubes](../user/install-qubes.md).

### Stage 27: managed-config path and installer workflow rework

Complete through PR #31.

Current behavior:

1. The installer no longer hardcodes the source VM.
2. The installer accepts a source VM as a positional argument.
3. When no VM is supplied, the installer can use a `zenity` chooser or command-line prompt.
4. The installer copies and validates `/tmp/d2wc.tgz` before replacing local source files.
5. The copied archive is staged under `~/.cache/d2wc/`.
6. The extracted local installation source is stored under `~/.local/share/d2wc/source/`.
7. User-owned managed Lua files are stored under `~/.config/d2wc/lua/`.
8. User UI settings are stored under `~/.config/d2wc/settings.json`.
9. Devilspie2 reads the active managed file through the integration symlink at `~/.config/devilspie2/d2wc.lua`.
10. The installer preserves unrelated Devilspie2 scripts and unrelated symlinks.
11. The installer preserves existing `d2wc` UI settings.
12. The installer warns and waits when configurator instances are running during an update.
13. The configurator can File Open another `d2wc` managed Lua file.
14. The configurator can Save As to a safe new managed Lua filename.
15. All edit operations, validation, guarded writes, and backups target the currently open managed file.
16. File Open and Save As update the Devilspie2 integration symlink only when safe.
17. Blank Machine/Application match components are displayed as `All` while preserving generated Lua rule format.

### Stage 28: Lua event handoff and configured-window suppression

Complete through PR #34.

Current behavior:

1. The managed Lua script can launch bare `d2wc` through `os.execute()` when a normal application window opens.
2. The launch is controlled by `D2WC_EVENT_HANDOFF_ENABLED` in the active managed Lua file.
3. The configurator publishes the stable GTK/X11 class `d2wc-configurator`.
4. Lua suppresses configurator recursion by comparing the current window class to `D2WC_CONFIGURATOR_CLASS`.
5. Lua suppresses automatic launching for windows that already match configured target rules.
6. Configured-window suppression covers `EXCLUDE`, `PIN`, `WORKSPACE_ROUTES`, `WORKSPACE_PLACEMENT`, and `LEFT_EDGE_CORRECTION`.
7. `GEOM` alone does not suppress handoff, because geometry profiles do not target windows by themselves.
8. Installer updates run targeted managed Lua runtime migrations for marked managed files.
9. Existing user comments, managed rules, spacing, and existing toggle values are preserved.

### Stage 29: post-handoff GTK polish and prompt entry point

Complete on the `gtk-ui-improvement-post-lua-handoff` branch.

Current behavior:

1. `Menu -> Configure` replaces the editor area with an in-window settings view.
2. The settings view has `Behavior` and `Notifications` sections.
3. `Behavior` controls `D2WC_EVENT_HANDOFF_ENABLED`.
4. `Behavior` controls `D2WC_EVENT_HANDOFF_ENTRY_POINT`.
5. Supported entry-point values are `configurator` and `prompt`.
6. The `prompt` entry point launches `d2wc prompt`.
7. The prompt shows `Cancel` and `Configure` actions.
8. The pointer is positioned on `Cancel` when the prompt opens.
9. Prompt mode receives event-window geometry from Lua and places the prompt near the triggering window.
10. The prompt publishes the stable GTK/X11 class `d2wc-action-prompt`.
11. Lua suppresses prompt recursion by comparing the current window class to `D2WC_ACTION_PROMPT_CLASS`.
12. The managed Lua marker is now executable state: `local D2WC_MANAGED = true`.
13. The old comment marker is no longer accepted as the managed-file test.
14. The default managed Lua template is version `0.1.13`.
15. Normal `d2wc` launches no longer inject the example event fixture into Machine/Application dropdowns.
16. The example fixture remains available only through `--event-fixture`.
17. Missing managed-marker load errors use the message `could not load config file: missing D2WC_MANAGED marker`.
18. Missing managed-marker load errors are shown as toasts.

## Future implementation stages

### Stage 30: applied-write restore and backup recovery

Add a user-facing restore workflow for changes that have already been applied to a managed config.

Required behavior:

1. Treat this as separate from row-level unsaved-edit undo.
2. Restore from the existing safe-save backup archive path rather than from transient UI state.
3. Show available backup members in a clear order, newest first.
4. Allow previewing or inspecting the selected restore target before writing.
5. Validate the restored candidate before replacing the active file.
6. Reuse the same staged write, sync, and backup safety rules as normal guarded writes.
7. Document how restore interacts with backup retention before enabling it broadly.

### Stage 31: generated split profiles

Generated split-profile work remains future work and should be kept separate from the Lua event handoff branch.
