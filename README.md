# d2wc

Devilspie2 Workspace Configurator.

`d2wc` is intended to make Linux window placement easier to configure by combining a `devilspie2` Lua rules script with a small configurator UI. The current implementation is the Lua rules engine. The next development step is the configurator that can observe windows, capture geometry, and write safe user-facing changes back into the Lua configuration sections.

## Current status

The repository now starts from the current `d2wc` Lua script version `0.1.12.3`.

The active Lua script supports:

1. Excluding domains, classes, or domain/class combinations from automation.
2. Pinning selected windows so they appear on all workspaces.
3. Routing windows to workspaces by domain, class, or domain/class match.
4. Applying named geometry profiles to matching windows.
5. Applying optional left-edge correction for windows that do not land exactly at `x = 0` when `set_window_geometry()` is used.

## Repository layout

```text
docs/
  product-development-brief.md    In-depth product and UI direction.
  lua-configurables.md            User-facing explanation of the Lua configuration sections.
  repository-layout.md            Repository structure and development conventions.
src/
  d2wc.lua                        Current devilspie2 Lua rules script.
```

## Development direction

The first production goal is not a flamboyant desktop tool. The goal is a minimal configurator that hides as much manual rule-writing as possible while still allowing the user to review and edit the result before it is written to the Lua script.

Planned entry points:

1. Open `Configure` from the system tray menu.
2. Go straight to `Configure` after a user resizes a window and releases the primary mouse button.
3. Show a small pointer-anchored menu after resize with `Cancel` and `Configure`.

The configurator should eventually update the Lua sections `EXCLUDE`, `PIN`, `WORKSPACE_ROUTES`, `WORKSPACE_PLACEMENT`, and `LEFT_EDGE_CORRECTION` without requiring the user to edit Lua manually.
