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

## Directory purposes

### `docs/`

Project planning, product design, UI behavior, and development notes.

The documentation should describe `d2wc` from the user's point of view first, then map that behavior back to implementation details.

### `src/`

Source code.

At the start of the project this should contain the current `devilspie2` Lua script. As the configurator is developed, this directory may split into more specific subdirectories, for example:

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
