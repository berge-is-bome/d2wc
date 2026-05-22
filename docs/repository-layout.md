# Repository Layout

This repository is intended to hold both the current `devilspie2` Lua rules script and the future configurator application.

## Current layout

```text
README.md
LICENSE
docs/
  development-status.md
  product-development-brief.md
  ui-flow.md
  mvp-scope.md
  runtime-architecture.md
  technology-evaluation.md
  event-monitoring.md
  left-edge-correction-testing.md
  packaging.md
  implementation-plan.md
  testing.md
  lua-configurables.md
  lua-design-history.md
  repository-layout.md
src/
  d2wc.lua
  d2wc/
    __init__.py
    __main__.py
    cli.py
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
tests/
```

## Document index

1. [Development Status](development-status.md) records the active PR status, latest local verification, and next practical work.
2. [Product Development Brief](product-development-brief.md) describes the product direction and user outcomes.
3. [UI Flow](ui-flow.md) describes the configurator screens, entry points, generated split profiles, and user-facing workflows.
4. [MVP Scope](mvp-scope.md) separates the safe manual configurator from post-resize automation.
5. [Runtime Architecture](runtime-architecture.md) describes the Lua script, configurator, daemon/helper, runtime settings, save model, and reload model.
6. [Technology Evaluation](technology-evaluation.md) explains the Python, GTK-first, Qt-roadmap direction.
7. [Event Monitoring](event-monitoring.md) describes resize detection, pointer menus, suppression, and desktop event behavior.
8. [Left-Edge Correction Testing](left-edge-correction-testing.md) defines repeatable tests for `set_window_geometry()`, `set_window_position()`, and `set_window_position2()`.
9. [Packaging](packaging.md) describes Fedora-first RPM direction, later Debian packaging, and Qubes/dom0 offline installation routes.
10. [Implementation Plan](implementation-plan.md) turns the design into ordered development stages.
11. [Testing](testing.md) defines parser, renderer, settings, generated split-profile, UI proof, and packaging tests.
12. [Lua Configurables](lua-configurables.md) explains the managed Lua sections and rule grammar.
13. [Lua Design History Notes](lua-design-history.md) records design context recovered from the archived pre-repository Lua script history.
14. [Repository Layout](repository-layout.md) describes this repository structure.

## Directory purposes

### `docs/`

Project planning, product design, UI behavior, architecture, packaging, development status, and development notes.

The documentation should describe `d2wc` from the user's point of view first, then map that behavior back to implementation details.

### `src/`

Source code.

The current structure keeps the active Lua script and the Python configurator core proof together under `src/`:

```text
src/
  d2wc.lua
  d2wc/
    core/
      ...
```

The Lua script remains the active `devilspie2` runtime layer while the Python package grows around it.

Future UI code should stay separate from the core parser, validator, renderer, settings, split-profile, backup, and save logic. A likely later structure is:

```text
src/
  d2wc.lua
  d2wc/
    core/
      ...
    window/
      ...
    ui/
      gtk/
        ...
      qt/
        ...
```

The UI split should only happen when the implementation reaches the active-window capture and GTK proof stages.

### `tests/`

Python tests for the configurator core proof and future UI behavior.

The current test suite covers managed-block parsing, grammar validation, section validation, duplicate validation, shadow validation, rendering, backup path calculation, settings validation, split-profile generation, safe save behavior, and guarded CLI behavior.

Tests must continue to avoid modifying a user's real configuration files.

## Suggested next files

The next useful files after the current CLI/core proof are:

1. `tests/fixtures/` for additional valid and invalid Lua samples.
2. Manual desktop test logs when active-window capture and UI proof work begin.

## Branching convention

Use short topic branches for repo changes. Examples:

1. `init-project-structure`
2. `configurator-core-proof`
3. `configurator-save-proof`
4. `configurator-gtk-proof`
5. `left-edge-correction-tests`
6. `configurator-pin-exclude-proof`

## Documentation style

Documentation should be detailed enough to guide development, but it should not pretend design questions are settled before they are tested.

When a behavior is confirmed, write it as part of the product design.

When a behavior still needs testing, mark it as a research item or development task.
