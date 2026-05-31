# d2wc Implementation Plan

The implementation plan turns the product direction and technical design notes into an ordered development roadmap.

The goal is to move from the current Devilspie2 Lua rules script to a safe GTK configurator, then to event-driven configuration workflows and post-resize automation.

The plan should remain practical and test-driven. Each stage should produce something that can be run, inspected, and corrected before the next stage starts.

## Current baseline

The current baseline is the completed implementation state that future work builds on.

Detailed implemented behavior is documented in focused reference documents:

1. [Development Status](development-status.md) tracks current status, latest verification, and active working notes.
2. [UI Flow](ui-flow.md) documents the current user-facing configurator behavior.
3. [Managed Config Workflow](managed-config-workflow.md) documents active managed-file ownership, path selection, File Open, Save As, and symlink safety.
4. [Installation Workflow](installation-workflow.md) documents installer behavior and managed Lua runtime refreshes.
5. [Lua Configurables](lua-configurables.md) documents the internal managed Lua rule grammar and rule-section behavior.
6. [Lua Event Handoff](lua-event-handoff.md) documents automatic window-event launching, prompt mode, recursion suppression, process locks, and managed Lua runtime migrations.
7. [Backup Archives](backup-archives.md) documents backup archive creation and safe-save ordering.
8. [Testing](testing.md) documents verification strategy.

### Baseline implementation capabilities

The repository currently contains:

1. `src/d2wc.lua`, the bundled Devilspie2 Lua runtime template.
2. Python package skeleton and console entry point for `d2wc`.
3. Parser, validator, renderer, and rule-editing core for all six managed Lua sections.
4. Guarded CLI save/edit operations that preview by default and require `--write` before modification.
5. Safe-save behavior with validation, temporary staging, backup archive creation, and atomic replacement.
6. GTK configurator with workflow-focused editing for all six managed sections.
7. Known-window inventory parser, row source, bounded capture, continuous capture, and GTK monitor integration.
8. Qubes/dom0 source-archive installation and update support.
9. XDG-style user paths for source cache, installed source, managed Lua files, UI settings, and Devilspie2 integration.
10. Managed-config File Open and Save As workflows.
11. Lua event handoff from the managed Lua runtime to `d2wc`.
12. Configured-window suppression for automatic handoff.
13. Behavior settings for automatic handoff and direct/prompt entry-point selection.
14. `d2wc prompt` as an optional event handoff entry point.
15. `local D2WC_MANAGED = true` as the required managed Lua marker.
16. User-facing documentation under `docs/user/` and project documentation under `docs/project/`.

The Lua script remains the execution layer. User-owned managed Lua files live under `~/.config/d2wc/lua/`, and Devilspie2 reads the active managed file through the integration symlink at `~/.config/devilspie2/d2wc.lua`.

### Completed implementation stages

Completed stages remain listed here as the implementation history that produced the current baseline.

1. Stage 0: repository preparation.
2. Stage 1: source layout for Python development.
3. Stage 2: Lua managed-block parser for `EXCLUDE`, `PIN`, `WORKSPACE_ROUTES`, `GEOM`, `WORKSPACE_PLACEMENT`, and `LEFT_EDGE_CORRECTION`.
4. Stage 3: rule model and validation for the CLI/core proof.
5. Stage 4: renderer and safe file writer for CLI/core editing proofs.
6. Stage 5: safe save proof, merged through PR #3.
7. Stage 6: `GEOM` editing proof, merged through PR #4.
8. Stage 7: `WORKSPACE_PLACEMENT` editing proof, merged through PR #5.
9. Stage 8: `WORKSPACE_ROUTES` editing proof, merged through PR #7, PR #8, and PR #9 follow-up work.
10. Stage 9: `PIN` and `EXCLUDE` target-rule editing proof, merged through PR #11.
11. Stage 10: `LEFT_EDGE_CORRECTION` editing proof, merged through PR #12.
12. Stage 11: documentation refresh after managed-section edit proofs, merged through PR #13.
13. Stage 12: first GTK configurator proof, merged through PR #14.
14. Stage 13: selected-window geometry diagnostic proof, merged through PR #15.
15. Stage 14: Devilspie2 probe research, retained as draft PR #16 research.
16. Stage 15: event-data GTK UI proof, merged through PR #19.
17. Stage 16: read-only event proposal preview, merged through PR #20.
18. Stage 17: test-config GTK UI proof, merged through PR #21.
19. Stage 18: test-config proposal action buttons, merged through PR #22.
20. Stage 19: managed-section editor for the test config, merged through PR #23.
21. Stage 20: grid-style GTK editor, merged through PR #27.
22. Stage 21: known-window inventory parser foundation, completed through PR #26.
23. Stage 22: known-window inventory row source, completed through PR #28.
24. Stage 23: bounded and continuous Devilspie2 inventory capture, completed through PR #28.
25. Stage 24: automatic GTK inventory monitor integration, completed through PR #28 and later cleanup.
26. Stage 25: installed command and first public Qubes installer polish, completed through PR #29.
27. Stage 26: public-release documentation refresh, completed through PR #30.
28. Stage 27: managed-config path and installer workflow rework, completed through PR #31.
29. Stage 28: Lua event handoff and configured-window suppression, completed through PR #34.
30. Stage 29: post-handoff GTK polish and prompt entry point.

### Historical stage notes that still matter

Stage 12 confirmed that the first GTK proof opened and closed cleanly, read no config files, wrote no config files, and included no rule editing UI.

Stage 13 confirmed that `xwininfo -frame` can capture useful selected-window geometry from dom0. That proof remains useful as a diagnostic, but it is not the active long-term UI direction.

Stage 14 established the current event-data direction:

1. Devilspie2/Lua is the correct runtime source for event data.
2. `devilspie2 --debug` prints an initial startup dump before later event output.
3. Capturing the first debug output is not target selection.
4. Capturing the next event after startup is unreliable because intermediary UI windows can emit events first.
5. Lua can call the needed functions directly.
6. `debug_print` is only needed when a proof needs to emit values to Python through stdout.
7. Perfect target selection should not block UI work.
8. Duplicate configurator launches were acceptable only for intermediary proof stages and have since been reduced through suppression of already-configured windows.

The repository-local record for that design turn is [Event-Data GTK UI Direction](event-data-ui-direction.md). Some of that document is now historical and may be reduced during the documentation cleanup.

Stage 15 proved representative event data could be passed through fixtures or command arguments and displayed by GTK without live target-selection experiments or config writes.

Stage 16 proved read-only event-derived `GEOM` and `WORKSPACE_PLACEMENT` proposal previews with optional read-only config inspection and copy-proposal support.

Stage 17 established the dedicated test-config workflow for isolated UI development:

1. `--init-test-config`
2. `--test-config`
3. `--replace-test-config`
4. `--test-config-path`

Stage 18 and Stage 19 proved GTK writes against the dedicated test config, using the same core edit operations and safe-save behavior that later became the managed-config editor path.

Stage 20 established the current workflow-focused grid editor. Current user-facing UI behavior now lives in [UI Flow](ui-flow.md).

Stages 21 through 24 established the known-window inventory pipeline. The important development notes are:

1. Inventory uses a temporary read-only probe Lua script rather than the active rules script.
2. Startup output is inventory input, not target selection.
3. Later debug output can add newly opened domain/class values while the monitor is running.
4. Temporary inventory processes must be stopped when the configurator closes or the stream is stopped.
5. Inventory targets populate Machine/Application choices and should not create `GEOM` suggestions by themselves.

Stage 25 made bare `d2wc` the normal installed configurator launch command while preserving `d2wc configure` as an explicit supported subcommand.

Stage 26 moved public documentation toward the current structure: user-facing documentation under `docs/user/`, project documentation under `docs/project/`, and Qubes install/update steps in [Install/Update for Qubes](../user/install-qubes.md).

Stage 27 established the current installed path model and managed-config behavior. Current details now live in [Managed Config Workflow](managed-config-workflow.md) and [Installation Workflow](installation-workflow.md).

Stage 28 established Lua event handoff, configured-window suppression, and targeted managed Lua runtime migrations. Current details now live in [Lua Event Handoff](lua-event-handoff.md).

Stage 29 established the prompt entry point, Behavior settings, Notifications settings, executable managed marker, prompt recursion suppression, and opt-in event fixture behavior. Current UI details now live in [UI Flow](ui-flow.md) and handoff details in [Lua Event Handoff](lua-event-handoff.md).

## Guiding decisions

The implementation should continue to follow these decisions:

1. Keep Devilspie2 as the active window-rule engine.
2. Keep the Lua runtime working throughout development.
3. Build safe manual/configurator workflows before post-resize automation.
4. Use Python for the first implementation.
5. Use GTK/PyGObject as the first UI target for Qubes/XFCE.
6. Keep PySide6/Qt on the roadmap for KDE-oriented users.
7. Keep parser, writer, validator, backup, and safe-save logic independent from the UI toolkit.
8. Make the stable entry point a command that can be assigned to a keyboard shortcut or called from the Lua event context.
9. Support source-checkout and source-archive execution because Qubes dom0 is often offline.
10. Keep real user configuration writes guarded.
11. Treat a save as successful only after staged content, backup archive, backup directory, and target directory safety steps have completed.
12. Make CLI save and edit operations safe by default: preview without writing, and require `--write` before modification.
13. Keep rule parsing token-order-independent, matching the Lua runtime principle that prefixed token order does not matter.
14. Keep Qubes OS as the real current target while preserving future non-Qubes design space.
15. Document historical design context and future roadmap items in the repository instead of relying on old conversations.
16. Build GTK workflows around real Devilspie2/Lua event data when event data is available, not around live target-selection experiments.
17. Keep representative event fixtures available for tests and manual experiments, but do not inject them into normal `d2wc` launches.
18. Allow automatic configurator launching only for unconfigured normal windows when the user enables Lua event handoff.
19. Let the user choose whether automatic handoff opens the configurator directly or shows the prompt first.
20. Use dedicated test-config paths for isolated GTK UI testing.
21. Store user-owned managed Lua files under `~/.config/d2wc/lua/`.
22. Use `~/.config/devilspie2/d2wc.lua` only as the Devilspie2-facing integration symlink for the active managed file.
23. Do not overwrite unrelated Devilspie2 Lua scripts or unrelated symlinks.
24. Keep File Open and Save As scoped to `d2wc` managed Lua files, not arbitrary Devilspie2 scripts.
25. Query the current X11 workspace count for the GTK workspace selector, falling back to workspace 1 when the count cannot be read.
26. Build the known-window inventory in small testable slices: parser first, row source and suppression second, bounded and continuous capture third, GTK live refresh last.
27. Keep installer managed-Lua refreshes targeted; do not rewrite whole user-managed Lua files from the bundled template.
28. Treat `local D2WC_MANAGED = true` as executable marker state, not as removable documentation.

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

Relevant current documents:

1. [Backups](../user/backups.md)
2. [Backup Archives](backup-archives.md)
3. [Managed Config Workflow](managed-config-workflow.md)

### Stage 31: generated split profiles

Generated split-profile work remains future work and should be kept separate from Lua event handoff and prompt-entry work.

Initial requirements:

1. Generate common profiles such as `half_left` and `half_right` from current screen or monitor geometry.
2. Account for window borders and panel/work-area behavior only after the target desktop behavior is tested.
3. Preview generated values before writing them to `GEOM`.
4. Keep generated profiles editable as normal geometry profiles after creation.
5. Avoid rewriting unrelated user profiles.

Relevant current documents:

1. [UI Flow](ui-flow.md)
2. [Lua Configurables](lua-configurables.md)
3. [Left-Edge Correction Testing](left-edge-correction-testing.md)
