# Repository Layout

This repository is intended to hold both the current `devilspie2` Lua rules script and the future configurator application.

## Current layout

```text
README.md
LICENSE
docs/
  product-development-brief.md
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
  configurator/
    ...
  daemon/
    ...
```

The split should only happen when the implementation language and packaging approach are chosen.

## Suggested next files

The next useful files after the initial structure are:

1. `docs/ui-flow.md` for screen-by-screen UI behavior.
2. `docs/technology-evaluation.md` for GUI toolkit and language comparison.
3. `docs/event-monitoring.md` for daemon/window-event behavior.
4. `docs/left-edge-correction-testing.md` for repeatable geometry tests.
5. `docs/packaging.md` for Fedora/Debian packaging notes.
6. `examples/` for example Lua configurations once the script is stable.

## Branching convention

Use short topic branches for repo changes. Examples:

1. `init-project-structure`
2. `docs-ui-flow`
3. `configurator-prototype`
4. `left-edge-correction-tests`

## Documentation style

Documentation should be detailed enough to guide development, but it should not pretend design questions are settled before they are tested.

When a behavior is confirmed, write it as part of the product design.

When a behavior still needs testing, mark it as a research item or development task.
