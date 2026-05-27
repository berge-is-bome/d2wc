# Repository Layout

This repository holds the current `devilspie2` Lua rules script, the Python configurator core, the GTK configurator, Qubes/dom0 installation helpers, tests, and project documentation.

The README is intended to describe what `d2wc` is from a public user point of view. Technical status, development workflow, implementation notes, and repository structure belong in `docs/`.

## Current layout

```text
README.md
LICENSE
pyproject.toml
d2wc-installation.sh
docs/
  backup-archives.md
  configurator-notification-settings.md
  development-status.md
  event-data-ui-direction.md
  event-monitoring.md
  implementation-plan.md
  left-edge-correction-testing.md
  lua-configurables.md
  lua-design-history.md
  mvp-scope.md
  packaging.md
  product-development-brief.md
  qubes-dom0-installation.md
  repository-layout.md
  runtime-architecture.md
  technology-evaluation.md
  testing.md
  ui-flow.md
  user-installation-documentation-notes.md
src/
  d2wc.lua
  d2wc/
    __init__.py
    __main__.py
    cli.py
    event_data.py
    event_inventory.py
    event_inventory_capture.py
    event_preview.py
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
      validation.py
    desktop/
      active_window.py
    ui/
      grid_rows.py
      gtk_app.py
      managed_actions.py
tests/
```

## Document index

1. [Backup Archives](backup-archives.md) describes backup archive behavior for guarded writes.
2. [Configurator Notification Settings](configurator-notification-settings.md) records future Configure menu notification settings.
3. [Development Status](development-status.md) records the active branch, latest verified baseline, current GTK behavior, Qubes/dom0 install behavior, known-window inventory behavior, current safe capability, and next work.
4. [Event-Data GTK UI Direction](event-data-ui-direction.md) records the direction for using Devilspie2 event data in the GTK UI.
5. [Event Monitoring](event-monitoring.md) describes resize detection, pointer menus, suppression, and desktop event behavior.
6. [Implementation Plan](implementation-plan.md) turns the design into ordered development stages.
7. [Left-Edge Correction Testing](left-edge-correction-testing.md) defines repeatable tests for `set_window_geometry()`, `set_window_position()`, and `set_window_position2()`.
8. [Lua Configurables](lua-configurables.md) explains the managed Lua sections and rule grammar.
9. [Lua Design History Notes](lua-design-history.md) records design context recovered from the archived pre-repository Lua script history.
10. [MVP Scope](mvp-scope.md) separates the safe manual configurator from post-resize automation.
11. [Packaging](packaging.md) describes Fedora-first RPM direction, later Debian packaging, Qubes/dom0 offline installation routes, and current source-archive installation behavior.
12. [Product Development Brief](product-development-brief.md) describes the product direction and intended user outcomes.
13. [Qubes dom0 Installation](qubes-dom0-installation.md) describes the current Qubes dom0 source-archive install/update flow.
14. [Repository Layout](repository-layout.md) describes this repository structure.
15. [Runtime Architecture](runtime-architecture.md) describes the Lua script, configurator, helper process direction, runtime settings, save model, and reload model.
16. [Technology Evaluation](technology-evaluation.md) explains the Python, GTK-first, Qt-roadmap direction.
17. [Testing](testing.md) defines parser, renderer, settings, generated split-profile, UI proof, and packaging tests.
18. [UI Flow](ui-flow.md) describes the configurator screens, entry points, generated split profiles, and user-facing workflows.
19. [User Installation Documentation Notes](user-installation-documentation-notes.md) records the intended shape of future user-facing manual installation documentation.

## Directory purposes

### `docs/`

Project planning, product design, UI behavior, architecture, packaging, installation, development status, and development notes.

The documentation should describe `d2wc` from the user's point of view first, then map that behavior back to implementation details where a technical document calls for it.

### `src/`

Source code.

The current structure keeps the active Lua script and the Python package together under `src/`:

```text
src/
  d2wc.lua
  d2wc/
    core/
      ...
    desktop/
      ...
    ui/
      ...
```

The Lua script remains the active Devilspie2 rules layer while the Python package provides the configurator, parser, validator, renderer, guarded edit commands, safe-save behavior, known-window inventory helpers, and GTK UI.

Core logic should stay separate from GTK-specific UI code so later front ends can reuse the same parser, validator, renderer, settings, split-profile, backup, save, and edit-operation logic.

### `tests/`

Python tests for the configurator core, CLI behavior, safe-save behavior, known-window inventory behavior, and UI helper logic.

Tests must continue to avoid modifying a user's real configuration files.

## Branching convention

Use short topic branches for repo changes. Examples:

1. `documentation-update-public-release`
2. `configurator-core-proof`
3. `configurator-save-proof`
4. `configurator-gtk-proof`
5. `left-edge-correction-tests`
6. `configurator-known-window-inventory`

## Documentation style

Public-facing documents, especially the README, should explain what `d2wc` is and what the user can do with it.

Technical details should live in focused documents under `docs/`.

Use inline Markdown links for documentation references:

```text
[Document Title](document-name.md)
```

When a behavior is confirmed, write it as current behavior.

When a behavior still needs testing, mark it as a research item, future stage, or development task.
