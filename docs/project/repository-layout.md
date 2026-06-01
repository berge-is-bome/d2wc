# Repository Layout

This repository holds the managed Devilspie2 Lua runtime templates, the Python configurator core, the GTK configurator and prompt UI, the Qubes/dom0 installation helper, tests, user documentation, and project documentation.

The README is intended to describe what `d2wc` is from a public user point of view. User-facing documentation belongs in `docs/user/`. Technical status, development workflow, implementation notes, and repository structure belong in `docs/project/`.

## Current layout

```text
README.md
LICENSE
pyproject.toml
install-qubes.sh
docs/
  user/
    README.md
    backups.md
    bundled-templates.md
    configurator-options.md
    install-qubes.md
    lua-configurables.md
  project/
    backup-archives.md
    configurator-notification-settings.md
    d2wc-design-history.md
    development-status.md
    event-monitoring.md
    implementation-plan.md
    installation-workflow.md
    left-edge-correction-testing.md
    lua-configurables.md
    lua-event-handoff.md
    managed-config-workflow.md
    mvp-scope.md
    packaging.md
    product-development-brief.md
    repository-layout.md
    runtime-architecture.md
    technology-evaluation.md
    ui-flow.md
src/
  d2wc.lua
  d2wc-1080.lua
  d2wc/
    __init__.py
    __main__.py
    cli.py
    event_data.py
    event_inventory.py
    event_inventory_capture.py
    event_preview.py
    managed_config_file.py
    prompt.py
    test_config.py
    test_config_actions.py
    core/
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
      transient_apply.py
      user_paths.py
      validation.py
    desktop/
      active_window.py
    ui/
      grid_rows.py
      gtk_app.py
      managed_actions.py
tests/
  test_transient_apply.py
```

## Document index

### User documentation

1. [User Documentation](../user/README.md) is the user-facing documentation landing page.
2. [Install/Update for Qubes](../user/install-qubes.md) describes the Qubes dom0 source-archive install/update flow.
3. [Bundled Templates](../user/bundled-templates.md) explains why the installer offers 1080 and 2160 default templates.
4. [Lua Configurables](../user/lua-configurables.md) explains the window behavior users can configure through `d2wc`.
5. [Configurator Options](../user/configurator-options.md) explains Behavior and Notifications settings in the configurator.
6. [Backups](../user/backups.md) explains where automatic backup archives are stored and what restore support exists now.

### Project documentation

1. [Backup Archives](backup-archives.md) describes backup archive behavior for guarded writes.
2. [Configurator Notification Settings](configurator-notification-settings.md) records notification settings behavior and related UI notes.
3. [d2wc Design History Notes](d2wc-design-history.md) records design context recovered from the archived pre-repository Lua script history.
4. [Development Status](development-status.md) tracks the current implementation baseline, recent milestones, latest verification, public beta scope, and active working notes.
5. [Event Monitoring](event-monitoring.md) describes resize detection, pointer menus, suppression, and future desktop event behavior.
6. [Implementation Plan](implementation-plan.md) tracks completed stages and future roadmap work.
7. [Installation Workflow](installation-workflow.md) documents current installer behavior and future installer principles.
8. [Left-Edge Correction Testing](left-edge-correction-testing.md) defines repeatable tests for `set_window_geometry()`, `set_window_position()`, and `set_window_position2()`.
9. [Lua Configurables](lua-configurables.md) explains the internal managed Lua rule grammar and rule-section behavior.
10. [Lua Event Handoff](lua-event-handoff.md) documents automatic window-event launching, prompt mode, recursion suppression, process locks, and managed Lua runtime migrations.
11. [Managed Config Workflow](managed-config-workflow.md) documents active managed-file ownership, path selection, File Open, Save As, settings file, Devilspie2 symlink safety, and transient apply behavior.
12. [MVP Scope](mvp-scope.md) separates the safe manual configurator from future automation work.
13. [Packaging](packaging.md) describes packaging direction and current packaging roadmap.
14. [Product Development Brief](product-development-brief.md) describes the product direction and intended user outcomes.
15. [Repository Layout](repository-layout.md) describes this repository structure.
16. [Runtime Architecture](runtime-architecture.md) describes runtime boundaries between Devilspie2, the managed Lua runtime, the Python command, and future helper responsibilities.
17. [Technology Evaluation](technology-evaluation.md) records implementation technology choices and tradeoffs.
18. [UI Flow](ui-flow.md) describes the configurator screens, entry points, prompt behavior, settings views, and user-facing workflows.

### Removed or superseded project documents

1. `docs/project/event-data-ui-direction.md` was removed after its useful content was folded into focused project documents.
2. `docs/project/testing.md` was removed after verification and testing notes were folded into the current status and implementation documents.
3. `docs/project/lua-design-history.md` was renamed to [d2wc Design History Notes](d2wc-design-history.md).

## Directory purposes

### `docs/user/`

User-facing documentation for installing, launching, configuring, and understanding `d2wc`.

These documents should be practical and task-oriented.

### `docs/project/`

Project planning, product design, UI behavior, architecture, packaging, development status, implementation workflow, and development notes.

These documents may describe implementation details, development history, and technical direction.

### `src/`

Source code.

The current structure keeps the bundled Devilspie2 Lua runtime templates and the Python package together under `src/`:

```text
src/
  d2wc.lua
  d2wc-1080.lua
  d2wc/
    core/
      ...
    desktop/
      ...
    ui/
      ...
```

The Lua runtime remains the active Devilspie2 rules layer. The Python package provides the configurator, prompt entry point, parser, validator, renderer, guarded edit commands, safe-save behavior, known-window inventory helpers, installer/runtime path helpers, transient apply helper, and GTK UI.

Core logic should stay separate from GTK-specific UI code so later front ends can reuse the same parser, validator, renderer, settings, split-profile, backup, save, user-path, transient-apply, and edit-operation logic.

### `tests/`

Python tests for the configurator core, CLI behavior, safe-save behavior, known-window inventory behavior, managed user paths, prompt/configurator behavior, transient apply behavior, and UI helper logic.

Tests must continue to avoid modifying a user's real configuration files.

## Branching convention

Use short topic branches for repo changes. Examples:

1. `documentation-update`
2. `installer-managed-config-workflow`
3. `lua-event-handoff`
4. `gtk-ui-improvement-post-lua-handoff`
5. `configurator-known-window-inventory`
6. `left-edge-correction-tests`

## Documentation style

Public-facing documents, especially the README and files under `docs/user/`, should explain what `d2wc` is and what the user can do with it.

Technical details should live in focused documents under `docs/project/`.

Use inline Markdown links for documentation references:

```text
[Document Title](document-name.md)
```

When a behavior is confirmed, write it as current behavior.

When a behavior still needs testing, mark it as a research item, future stage, or development task.
