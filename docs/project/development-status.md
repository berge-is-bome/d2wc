# d2wc Development Status

Development status tracks the current implementation baseline, recent milestones, latest verification, public beta scope, and active working notes.

Detailed behavior belongs in the focused user and project documents linked below. Keep this file as the working status index, not as a duplicate specification for implemented features.

## Current implementation baseline

`d2wc` is at its intended first public beta baseline for the Qubes OS and Devilspie2 workflow.

Current public target:

1. Qubes OS with XFCE.
2. Devilspie2 window rules.
3. User-managed `d2wc` Lua files, not arbitrary pre-existing Devilspie2 Lua scripts.
4. Source-archive install/update flow for dom0.
5. GTK configurator as the normal user path for managing rules.
6. Optional automatic configurator launch for unconfigured normal windows through Lua event handoff.
7. Optional prompt button handoff for users who prefer a confirm-before-configure workflow.

Broader X11/Linux desktop use remains part of the project direction, but should be treated as experimental until tested deliberately.

## Latest confirmed verification

Latest verification was reported as:

```bash
python3 -m d2wc validate --config src/d2wc.lua
python3 -m pytest
```

Result:

```text
296 passed
```

After documentation restructuring and any local commits, run the normal verification path again:

```bash
python3 -m d2wc validate --config src/d2wc.lua
python3 -m pytest
```

## Canonical behavior documents

Current implemented behavior is documented in the focused files below.

User-facing documentation:

1. [Install/Update for Qubes](../user/install-qubes.md) documents the Qubes dom0 install/update flow.
2. [Lua Configurables](../user/lua-configurables.md) documents what users can configure.
3. [Backups](../user/backups.md) documents where users can find backup archives.

Project documentation:

1. [UI Flow](ui-flow.md) documents the current user-facing configurator behavior.
2. [Managed Config Workflow](managed-config-workflow.md) documents the installed path model, managed-file ownership, File Open, Save As, settings file, and symlink safety.
3. [Lua Configurables](lua-configurables.md) documents the internal managed Lua rule grammar and rule-section behavior.
4. [Lua Event Handoff](lua-event-handoff.md) documents automatic window-event launching, prompt mode, recursion suppression, process locks, and managed Lua runtime migrations.
5. [Backup Archives](backup-archives.md) documents backup archive creation and safe-save ordering.
6. [Product Development Brief](product-development-brief.md) documents the product direction and intended user outcomes.

## Recent public-release milestones

### PR #30: `Prepare documentation for public release`

Completed work:

1. Reworked the README as a public-facing description of what `d2wc` is.
2. Split documentation into user-facing documentation under `docs/user/` and project documentation under `docs/project/`.
3. Replaced old Qubes installation notes with [Install/Update for Qubes](../user/install-qubes.md).

### PR #31: `Rework Qubes installer and managed config workflow`

Completed work:

1. Removed the hardcoded source VM from `install-qubes.sh`.
2. Added positional source-VM, `zenity`, and command-line prompt installer paths.
3. Moved user-owned managed Lua files under `~/.config/d2wc/lua/`.
4. Moved the extracted local installation source under `~/.local/share/d2wc/source/`.
5. Kept `~/.config/devilspie2/d2wc.lua` as the Devilspie2-facing integration symlink.
6. Added configurator File Open and Save As support for `d2wc` managed Lua files.
7. Preserved unrelated Devilspie2 scripts and unrelated symlinks.

### PR #32: `Rework Qubes installer and managed-config XDG integration`

Completed work:

1. Preserved the active managed file through safe symlink handling.
2. Kept bare `d2wc` as the normal installed configurator launch command.
3. Kept `d2wc configure` as the explicit supported configurator subcommand.

### PR #34: `Add Lua event handoff workflow`

Completed work:

1. Added Lua event handoff from `src/d2wc.lua` to `d2wc`.
2. Added `D2WC_EVENT_HANDOFF_ENABLED` as the per-managed-file handoff toggle.
3. Added configurator recursion suppression through the stable GTK/X11 class `d2wc-configurator`.
4. Added automatic launch suppression for windows that already match managed target rules.
5. Added targeted managed Lua runtime migration during installer updates.

## Recent post-handoff GTK and runtime work

Completed work after the Lua event handoff baseline:

1. Replaced the separate Configure dialog with an in-window settings view.
2. Added `Behavior` and `Notifications` settings pages.
3. Moved automatic handoff controls under `Menu -> Configure -> Behavior`.
4. Added `D2WC_EVENT_HANDOFF_ENTRY_POINT` with `configurator` and `prompt` modes.
5. Added the `d2wc prompt` entry point.
6. Added the Cancel/Configure prompt button for unconfigured window events.
7. Positioned the prompt near the bottom-right corner of the event window using geometry passed from Devilspie2.
8. Added prompt recursion suppression with the GTK/X11 class `d2wc-action-prompt`.
9. Added single-instance locks for configurator and prompt processes.
10. Replaced the comment-based managed marker with `local D2WC_MANAGED = true`.
11. Updated installer, migration, snapshot, and test paths to require the new marker.
12. Simplified the default managed Lua header to version-only project identification.
13. Adopted the `0.1.13` managed Lua template structure.
14. Removed the old two-point GTK font-size override.
15. Changed normal `d2wc` and `d2wc configure` launches so the built-in event fixture is opt-in only.
16. Normalized the missing-marker load error to `could not load config file: missing D2WC_MANAGED marker`.
17. Changed missing-marker load failures to use a toast instead of the main error view.
18. Updated tests for the new marker and opt-in event-fixture behavior.

## Important current notes

1. The configurator does not currently auto-reload when the managed Lua file changes on disk. Users who edit a managed Lua file externally should reopen the configurator or reopen the file before continuing UI edits.
2. Normal `d2wc` and `d2wc configure` launches do not inject the built-in example event fixture unless `--event-fixture` is explicitly requested.
3. Managed Lua files require executable marker state:

   ```lua
   local D2WC_MANAGED = true
   ```

4. `~/.config/devilspie2/d2wc.lua` is the Devilspie2-facing integration symlink. The user-owned managed Lua files live under `~/.config/d2wc/lua/`.
5. File Open and Save As are only for `d2wc` managed Lua files that pass the managed-file validation rules.
6. Backup archives are created as part of guarded writes. User-facing restore commands and GTK restore UI are not implemented yet.

## Active documentation restructuring notes

The documentation set is being reworked into a coherent structure:

1. User documents explain what users can do and configure.
2. Project documents explain implementation behavior, internal workflow, historical decisions, and future work.
3. Information already covered in a focused document should be replaced with a concise summary and an internal link.
4. Avoid starting documents with wording like `This document...` when the purpose can be stated directly.

## Next development/documentation checks

1. Keep the source-checkout verification path green.
2. Keep documentation links aligned after moving user-facing material under `docs/user/`.
3. Continue reducing duplicated current-behavior descriptions in older planning documents.
4. Preserve historical development notes while moving implemented behavior into focused reference documents.
