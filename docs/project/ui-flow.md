# d2wc UI Flow

## Purpose

This document describes how the `d2wc` configurator behaves from the user's point of view.

The goal is to make window routing and placement feel like a guided desktop action instead of Lua editing. The Lua script remains the execution layer, but the configurator is the normal way users manage rules.

## UI design goals

The configurator should be small, practical, and predictable.

It should:

1. Show the active managed file clearly.
2. Expose the six supported managed rule sections in user language.
3. Let users add, modify, delete, apply, or undo row-level edits before applying.
4. Use known windows to populate Machine/Application choices where possible.
5. Warn before invalid or unsafe writes.
6. Back up the managed Lua file before writing.
7. Avoid requiring the user to know Lua syntax.
8. Still allow advanced users to inspect and manually edit generated values.

It should not:

1. Become a large desktop environment control panel.
2. Rewrite unrelated Lua program logic.
3. Apply hidden permanent changes without a visible save action.
4. Assume that mouse buttons use a right-handed layout.
5. Require a permanently visible tray icon for normal background operation.
6. Become a generic editor for arbitrary Devilspie2 scripts.

## Main user objects

The UI exposes these concepts in user language.

1. Machine: the Qubes domain when available, or `All` for no domain-specific match.
2. Application: the application class when available, or `All` for no class-specific match.
3. Workspace route: the workspace where matching windows should open.
4. Geometry profile: a saved `{ x, y, w, h }` size and position.
5. Placement rule: a link between a window match and a geometry profile.
6. Pin rule: a rule that keeps matching windows visible on all workspaces.
7. Exclude rule: a rule that tells `d2wc` not to manage matching windows.
8. Left-edge correction: a compatibility setting for windows that should land at `x = 0` but do not.

## Entry point 1: command or keyboard shortcut

The stable manual entry point is the installed command that opens the configurator:

```bash
d2wc
```

This command can be assigned to a desktop keyboard shortcut by the user. That is a clean day-to-day workflow after the workspace has mostly been configured.

The explicit configurator subcommand also remains supported:

```bash
d2wc configure
```

The command is also usable from a terminal for debugging.

## Entry point 2: Lua event handoff

The active managed Lua file can open the configurator automatically when Devilspie2 sees a new normal application window.

The handoff is controlled by this setting in the active managed Lua file:

```lua
local D2WC_EVENT_HANDOFF_ENABLED = true
```

Set it to `false` to disable automatic launching:

```lua
local D2WC_EVENT_HANDOFF_ENABLED = false
```

The configurator exposes this as:

```text
Menu -> Configure -> Window events -> Automatically open d2wc for unconfigured windows
```

### Handoff behavior

The Lua script:

1. filters to `WINDOW_TYPE_NORMAL`,
2. extracts the current domain and class,
3. checks whether the current window already matches a managed target rule,
4. suppresses launch if the current window is already configured,
5. suppresses launch if the current window is the configurator itself,
6. launches bare `d2wc` when automatic launch is enabled and the window is unconfigured.

The configurator's own GTK/X11 class is:

```text
d2wc-configurator
```

That value is used only to prevent recursive configurator launches.

For the full implementation details, see [Lua Event Handoff](lua-event-handoff.md).

## Entry point 3: optional tray menu

A tray icon can still be useful during initial setup or troubleshooting, but it should not be required for normal operation.

The tray mode remains optional future work.

When enabled, the tray menu can include:

1. `Configure`
2. `Capture Active Window`
3. `Pause d2wc`
4. `Reload Rules`
5. `Open Lua Config`
6. `About`
7. `Quit`

## Main configurator window

The current configurator is organized around workflows rather than a large target-inspection form.

It currently includes:

1. Workflow selector for all six managed sections:
   1. `Exclude`
   2. `Pin`
   3. `Workspace routes`
   4. `Window geometry`
   5. `Workspace placement`
   6. `Left edge correction`
2. One top `Add` row per workflow.
3. Configured rows below the top `Add` row.
4. Row-level `Action` selector for `Add`, `Modify`, and `Delete`.
5. Split fields instead of raw Lua strings.
6. Searchable Machine/Application and related selectors.
7. Row-level `Apply`.
8. Row-level unsaved-edit detection.
9. Dirty-row `Undo` / `Apply` split controls.
10. Compact success toasts.
11. Blocking dialogs for errors and validation failures.
12. Per-workflow help through `Menu -> Help` and `F1`.
13. File Open and Save As for managed Lua files.
14. Window title showing the active managed file.

## Configure dialog

`Menu -> Configure` opens a grouped settings dialog.

Current sections:

1. `Window events`
2. `Notifications`

`Window events` contains:

```text
Automatically open d2wc for unconfigured windows
```

That checkbox updates `D2WC_EVENT_HANDOFF_ENABLED` in the active managed Lua file through the safe-save path.

`Notifications` contains:

1. Toast timeout seconds.
2. Toast opacity.

Toast settings are stored in:

```text
~/.config/d2wc/settings.json
```

## File Open

`File Open` lets the user choose another `d2wc` managed Lua file.

Behavior:

1. Defaults to `~/.config/d2wc/lua/`.
2. Loads only valid managed Lua files.
3. Updates the active managed file in the configurator.
4. Updates the window title.
5. Updates `~/.config/devilspie2/d2wc.lua` when it is safe to do so.

## Save As

`Save As` lets the user save the current managed Lua file under another safe managed filename.

Behavior:

1. Defaults to `~/.config/d2wc/lua/`.
2. Requires a safe `.lua` filename.
3. Reloads the saved file as the active managed file.
4. Updates the window title.
5. Updates `~/.config/devilspie2/d2wc.lua` when it is safe to do so.
6. Shows success with a toast notification.

## Known-window suggestions

The configurator starts an inventory monitor when it opens.

The monitor:

1. uses a temporary read-only Devilspie2 probe script,
2. gathers normal window domain/class observations,
3. uses startup output to populate initial values,
4. uses later output to add newly seen values,
5. avoids visible duplicate targets,
6. stops and terminates its temporary Devilspie2 process when the configurator closes.

Known-window values populate Machine/Application dropdowns for the top `Add` row.

## Flow: add or modify a target rule

Typical user flow:

1. User opens `d2wc`, or Lua event handoff opens it for an unconfigured normal window.
2. User chooses the relevant workflow.
3. User selects Machine, Application, and section-specific values.
4. User chooses `Add`, `Modify`, or `Delete`.
5. User reviews row state.
6. User applies the row.
7. `d2wc` validates the managed Lua file, creates a backup, and replaces the active managed file safely.
8. The UI refreshes with the updated configured rows.

## Flow: route window to workspace

User-facing intent:

```text
When this window opens, send it to workspace N.
```

The workflow writes to `WORKSPACE_ROUTES`.

The configurator must avoid duplicate Lua table keys such as two separate `[1]` entries. When adding a route to an existing workspace, it appends to that workspace's existing list rather than creating another list with the same key.

## Flow: apply geometry profile to a window

User-facing intent:

```text
When this window opens, use this saved size and position.
```

The workflow writes to `WORKSPACE_PLACEMENT` and references a profile from `GEOM`.

## Flow: create or modify a geometry profile

User-facing intent:

```text
Save this reusable window size and position.
```

The workflow writes to `GEOM`.

`GEOM` profiles do not target windows by themselves, so `GEOM` alone does not suppress Lua event handoff.

## Flow: pin a window

User-facing intent:

```text
Keep matching windows visible on all workspaces.
```

The workflow writes to `PIN`.

## Flow: exclude a window

User-facing intent:

```text
Do not manage matching windows.
```

The workflow writes to `EXCLUDE`.

Excluded windows skip workspace routing, pinning, geometry, left-edge correction, and automatic configurator launching.

## Flow: left-edge correction

User-facing intent:

```text
Use this compatibility correction when a window should land at x = 0 but does not.
```

The workflow writes to `LEFT_EDGE_CORRECTION`.

## Future post-resize flows

Direct post-resize configuration and post-resize choice menus remain future work.

Those future flows must not trigger when `d2wc` itself moves or resizes a window, and they must not apply hidden permanent changes without a visible save action.
