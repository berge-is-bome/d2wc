# Repository Layout

This repository is intended to hold both the current `devilspie2` Lua rules script and the future configurator application.

## Current layout

```text
README.md
LICENSE
docs/
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
  repository-layout.md
src/
  d2wc.lua
```

## Document index

1. [Product Development Brief](product-development-brief.md) describes the product direction and user outcomes.
2. [UI Flow](ui-flow.md) describes the configurator screens, entry points, generated split profiles, and user-facing workflows.
3. [MVP Scope](mvp-scope.md) separates the safe manual configurator from post-resize automation.
4. [Runtime Architecture](runtime-architecture.md) describes the Lua script, configurator, daemon/helper, runtime settings, save model, and reload model.
5. [Technology Evaluation](technology-evaluation.md) explains the Python, GTK-first, Qt-roadmap direction.
6. [Event Monitoring](event-monitoring.md) describes resize detection, pointer menus, suppression, and desktop event behavior.
7. [Left-Edge Correction Testing](left-edge-correction-testing.md) defines repeatable tests for `set_window_geometry()`, `set_window_position()`, and `set_window_position2()`.
8. [Packaging](packaging.md) describes Fedora-first RPM direction, later Debian packaging, and Qubes/dom0 offline installation routes.
9. [Implementation Plan](implementation-plan.md) turns the design into ordered development stages.
10. [Testing](testing.md) defines parser, renderer, settings, generated split-profile, UI proof, and packaging tests.
11. [Lua Configurables](lua-configurables.md) explains the managed Lua sections and rule grammar.
12. [Repository Layout](repository-layout.md) describes this repository structure.

## Directory purposes

### `docs/`

Project planning, product design, UI behavior, architecture, packaging, and development notes.

The documentation should describe `d2wc` from the user's point of view first, then map that behavior back to implementation details.

### `src/`

Source code.

At the start of the project this contains the current `devilspie2` Lua script. As the configurator is developed, this directory may split into more specific subdirectories, for example:

```text
src/
  devilspie2/
    d2wc.lua
  d2wc/
    core/
      ...
    ui/
      gtk/
        ...
      qt/
        ...
```

The split should only happen when the implementation language and packaging approach are chosen.

## Suggested next files

The next useful files after the initial structure are:

1. `examples/` for example Lua configurations once the script is stable.
2. `docs/developer-notes.md` for implementation discoveries that do not belong in product docs.

## Branching convention

Use short topic branches for repo changes. Examples:

1. `init-project-structure`
2. `configurator-core-proof`
3. `configurator-gtk-proof`
4. `left-edge-correction-tests`

## Documentation style

Documentation should be detailed enough to guide development, but it should not pretend design questions are settled before they are tested.

When a behavior is confirmed, write it as part of the product design.

When a behavior still needs testing, mark it as a research item or development task.
