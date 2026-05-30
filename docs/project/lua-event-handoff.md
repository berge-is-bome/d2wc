# Lua Event Handoff

## Purpose

This document describes the current Lua event handoff workflow used by `d2wc`.

The goal is to let the active Devilspie2 `d2wc.lua` script offer `d2wc` configuration automatically when a new normal application window appears and no existing managed rule already covers that window.

The handoff is optional and user-controlled from the active managed Lua file and from the GTK configurator.

## Runtime flow

The active Devilspie2 integration path is:

```text
~/.config/devilspie2/d2wc.lua
```

When managed by `d2wc`, that path is a symlink into:

```text
~/.config/d2wc/lua/
```

Devilspie2 runs the active Lua script for window events. The managed Lua script first filters to normal application windows:

```lua
local window_type = get_window_type()
if (window_type ~= "WINDOW_TYPE_NORMAL") then
  return
end
```

After the window type check, the script extracts the current Qubes domain and application class, builds the managed-rule lookup state, and decides whether the selected `d2wc` entry point should be launched.

The handoff call is:

```lua
launch_d2wc_event_handoff(cls, window_has_managed_rule(domain, cls), domain)
```

The handoff does not run when the window is already covered by a managed target rule.

## Managed Lua marker

Managed Lua files identify themselves with executable Lua state, not with a comment marker:

```lua
local D2WC_MANAGED = true
```

Files without that marker are not treated as `d2wc` managed Lua files.

The old comment marker is no longer used as the managed-file test.

## Handoff toggle

The handoff is controlled in each managed Lua file by:

```lua
local D2WC_EVENT_HANDOFF_ENABLED = true
```

Set it to `false` to disable automatic handoff:

```lua
local D2WC_EVENT_HANDOFF_ENABLED = false
```

The GTK configurator exposes this setting from:

```text
Menu -> Configure -> Behavior
```

The checkbox label is:

```text
Automatically open d2wc for unconfigured windows
```

Changing this setting updates the active managed Lua file through the same safe-save path used by other configurator writes. Existing comments and managed rules are preserved.

## Handoff entry point

The selected automatic entry point is controlled in each managed Lua file by:

```lua
local D2WC_EVENT_HANDOFF_ENTRY_POINT = "configurator" -- values: "configurator", "prompt"
```

Supported values:

1. `configurator`: open the full GTK configurator directly.
2. `prompt`: show the small Cancel/Configure prompt first.

The GTK configurator exposes this setting from:

```text
Menu -> Configure -> Behavior -> Entry point
```

The visible choices are:

1. `Open configurator directly`
2. `Show Cancel/Configure button first`

## Direct configurator entry point

When `D2WC_EVENT_HANDOFF_ENTRY_POINT` is `"configurator"`, the Lua handoff launches the installed command:

```lua
os.execute("d2wc >/dev/null 2>&1 &")
```

The normal installed command is still:

```bash
d2wc
```

The explicit configurator subcommand remains supported:

```bash
d2wc configure
```

## Prompt entry point

When `D2WC_EVENT_HANDOFF_ENTRY_POINT` is `"prompt"`, the Lua handoff launches:

```bash
d2wc prompt
```

The prompt displays a compact action window with:

1. `Cancel`
2. `Configure`

The pointer is positioned on `Cancel` so the safer action is the immediate click target.

Choosing `Configure` opens the normal GTK configurator. Choosing `Cancel` closes the prompt without opening the configurator.

The prompt publishes this GTK/X11 class:

```text
d2wc-action-prompt
```

The Lua handoff suppresses this class to avoid prompt recursion.

## Event geometry handoff

The Lua runtime captures the current event window geometry with Devilspie2:

```lua
local geometry_ok, x, y, w, h = pcall(get_window_geometry)
```

When geometry capture succeeds, prompt mode passes these command-line arguments to `d2wc prompt`:

```text
--window-x
--window-y
--window-width
--window-height
```

The prompt uses those values to place itself near the bottom-right corner of the window that triggered the event.

The geometry path avoids relying on `_NET_ACTIVE_WINDOW` or inferring the event window after launch.

## Recursion suppression

The configurator publishes a stable GTK/X11 window class:

```text
d2wc-configurator
```

The prompt publishes a stable GTK/X11 window class:

```text
d2wc-action-prompt
```

The Lua handoff checks the current window class against:

```lua
local D2WC_CONFIGURATOR_CLASS = "d2wc-configurator"
local D2WC_ACTION_PROMPT_CLASS = "d2wc-action-prompt"
```

If the current window is the configurator or the action prompt, Lua does not launch another `d2wc` entry point.

In this context, "class" means the X11/WM class value derived from `get_class_instance_name()`, not a Python class.

## Already-configured window suppression

The handoff suppresses automatic launch when the current window already matches a managed target rule.

The suppression check counts these managed sections as configured-window handling rules:

1. `EXCLUDE`
2. `PIN`
3. `WORKSPACE_ROUTES`
4. `WORKSPACE_PLACEMENT`
5. `LEFT_EDGE_CORRECTION`

`GEOM` alone is not counted because a geometry profile does not target a window by itself.

This means a new unconfigured normal window can open `d2wc`, while a window that already has a route, placement, pin, exclusion, or left-edge correction does not repeatedly open the configurator or prompt.

## Process instance locks

The Python entry points use process locks under:

```text
~/.config/d2wc/
```

Current lock files:

```text
~/.config/d2wc/configurator.lock
~/.config/d2wc/prompt.lock
```

Only one configurator instance and one prompt instance should be active at a time for a given user session.

## Managed Lua update behavior

Installer updates run targeted runtime migrations over marked managed Lua files under:

```text
~/.config/d2wc/lua/
```

A file must contain the managed marker:

```lua
local D2WC_MANAGED = true
```

Files without that marker are skipped by the migration helper and rejected when selected as the active managed file.

For marked managed files, the migration inserts only missing runtime snippets needed by the current managed Lua runtime. It does not rewrite the full template, normalize formatting, or replace user-authored comments.

The migration can add missing pieces such as:

1. latest header version comments,
2. `D2WC_MANAGED`,
3. `D2WC_EVENT_HANDOFF_ENABLED`,
4. `D2WC_EVENT_HANDOFF_ENTRY_POINT`,
5. `D2WC_CONFIGURATOR_CLASS`,
6. `D2WC_ACTION_PROMPT_CLASS`,
7. Lua event handoff helper code,
8. already-configured suppression helpers,
9. the handoff call.

Existing user values are preserved. For example, if a user has already set:

```lua
local D2WC_EVENT_HANDOFF_ENABLED = false
```

an installer update must not flip it back to `true`.

## Temporary Devilspie2 inventory monitor cleanup

The configurator starts a temporary Devilspie2 debug process for the known-window inventory monitor.

Those temporary processes use folders like:

```text
/tmp/d2wc-devilspie2-inventory-*
```

The inventory stream is stoppable. When the configurator closes or the editor is rebuilt, the monitor stop event is passed into the stream and the temporary Devilspie2 process is terminated.

Expected behavior after closing `d2wc`:

```bash
ps aux | grep 'devilspie2 --debug --folder /tmp/d2wc-devilspie2-inventory-' | grep -v grep
```

No stale inventory process should remain.

## Configure view layout

`Menu -> Configure` replaces the main editor area with an in-window settings view.

The settings view has a left navigation column with:

1. `Behavior`
2. `Notifications`

`Behavior` contains the automatic handoff toggle and the entry-point selector.

`Notifications` contains:

1. toast timeout seconds,
2. toast opacity.

The `Back` button returns to the managed rule editor.
