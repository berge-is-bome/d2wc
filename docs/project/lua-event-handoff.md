# Lua Event Handoff

## Purpose

This document describes the current Lua event handoff workflow used by `d2wc`.

The goal is to let the active Devilspie2 `d2wc.lua` script open the GTK configurator automatically when a new normal application window appears and no existing managed rule already covers that window.

## Current status

Lua event handoff is implemented on the `lua-event-handoff` branch.

Confirmed verification:

```bash
python3 -m d2wc validate --config src/d2wc.lua
python3 -m pytest
```

Result:

```text
295 passed
```

## Runtime flow

The active Devilspie2 integration path is:

```text
~/.config/devilspie2/d2wc.lua
```

When managed by `d2wc`, that path is a symlink into:

```text
~/.config/d2wc/lua/
```

Devilspie2 runs the active Lua script for window events. The `d2wc` managed Lua script first filters to normal application windows:

```lua
local window_type = get_window_type()
if (window_type ~= "WINDOW_TYPE_NORMAL") then
  return
end
```

After the window type check, the script extracts the current Qubes domain and application class, builds the managed-rule lookup state, and decides whether the configurator should be launched.

The Lua handoff launches the configurator with the bare installed command:

```lua
os.execute("d2wc >/dev/null 2>&1 &")
```

The handoff does not pass command-line event arguments in the current implementation.

## Handoff toggle

The handoff is controlled in each managed Lua file by:

```lua
local D2WC_EVENT_HANDOFF_ENABLED = true
```

Set it to `false` to disable automatic configurator launching:

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

## Configurator recursion suppression

The configurator publishes a stable GTK/X11 window class:

```text
d2wc-configurator
```

The Lua handoff checks the current window class against:

```lua
local D2WC_CONFIGURATOR_CLASS = "d2wc-configurator"
```

If the current window is the configurator itself, Lua does not launch another configurator instance. This prevents the configurator window from triggering recursive configurator launches.

In this context, "class" means the X11/WM class value derived from `get_class_instance_name()`, not a Python class.

## Already-configured window suppression

The handoff suppresses automatic configurator launch when the current window already matches a managed target rule.

The suppression check counts these managed sections as configured-window handling rules:

1. `EXCLUDE`
2. `PIN`
3. `WORKSPACE_ROUTES`
4. `WORKSPACE_PLACEMENT`
5. `LEFT_EDGE_CORRECTION`

`GEOM` alone is not counted because a geometry profile does not target a window by itself.

This means a new unconfigured normal window can open `d2wc`, while a window that already has a route, placement, pin, exclusion, or left-edge correction does not repeatedly open the configurator.

## Managed Lua update behavior

Installer updates run a targeted runtime migration over marked managed Lua files under:

```text
~/.config/d2wc/lua/
```

A file must contain the managed marker:

```text
d2wc managed
```

Files without that marker are skipped by the migration helper and rejected by the installer when selected as the active managed file.

For marked managed files, the migration inserts only missing runtime snippets needed by the current managed Lua runtime. It does not rewrite the full template, normalize formatting, or replace user-authored comments.

The migration can add missing pieces such as:

1. latest header version comments,
2. handoff settings,
3. the handoff helper,
4. already-configured suppression helpers,
5. the handoff call.

Existing user values are preserved. For example, if a user has already set:

```lua
local D2WC_EVENT_HANDOFF_ENABLED = false
```

an installer update must not flip it back to `true`.

## Temporary Devilspie2 inventory monitor cleanup

The configurator still starts a temporary Devilspie2 debug process for the known-window inventory monitor.

Those temporary processes use folders like:

```text
/tmp/d2wc-devilspie2-inventory-*
```

The inventory stream is now stoppable. When the configurator closes or the editor is rebuilt, the monitor stop event is passed into the stream and the temporary Devilspie2 process is terminated.

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

`Behavior` contains the automatic handoff toggle.

`Notifications` contains:

1. toast timeout seconds,
2. toast opacity.

The `Back to rules` button returns to the managed rule editor.
