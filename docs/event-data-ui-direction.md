# Event-Data GTK UI Direction

## Purpose

This document records the current direction for the GTK configurator UI after the selected-window and Devilspie2 probe experiments.

The goal is to build the configurator UI around data captured by the existing Devilspie2 Lua event context, rather than blocking UI work on perfect target selection or live probing.

## Current decision

Do not block GTK UI work on perfect target selection.

The current UI direction is:

1. Devilspie2/Lua remains the window event source.
2. When a window event occurs, Lua captures the relevant identity and geometry data directly from Devilspie2 functions.
3. The user still gets the existing three configuration options.
4. If the user chooses the configurator, GTK opens with the identity and geometry data captured from the Lua event that triggered it.
5. Duplicate configurator launches are acceptable for now, for example one for a menu or launcher event and one for the actual application window event.
6. Later, `d2wc` should suppress automatically opening the configurator for windows that already have a profile, placement rule, route, pin, exclude, or other known handling rule.
7. After suppression is in place, the user can add the menu or launcher event once and then see the configurator only for the real application window event.

## Why this direction changed

The selected-window proof showed that `xwininfo -frame` can capture useful frame geometry from dom0, but it is not the correct long-term data source for `d2wc` rule generation.

The Devilspie2 probe research showed that `devilspie2 --debug` behaves in two phases:

1. Startup dump: it prints output for all currently known or processed windows.
2. Event stream: after startup, it stays quiet until a later window event appends more output.

That means capturing the first debug output is not target selection. Capturing the next event after startup is also unreliable because menus, launchers, and other intermediary UI windows can generate events before the intended application window.

The new direction accepts that early duplicate configurator launches are acceptable and solves the noise later through suppression of already-known windows.

## Event-provided data model

Start with these Devilspie2 functions as the event data source:

```lua
get_class_instance_name()
get_window_property( '_QUBES_VMNAME' )
get_screen_geometry()
get_window_geometry()
```

Keep the exact known-working Qubes property call form:

```lua
get_window_property( '_QUBES_VMNAME' )
```

`debug_print` is useful for temporary proofs, because Python can read stdout from `devilspie2 --debug`. In application logic, Lua can call the functions directly and pass the resulting values to the configurator command through the chosen event handoff mechanism.

## Manual reference probe

The broader manual debug probe used during design discussion was:

```lua
debug_print( "Domain: " .. get_window_property( '_QUBES_VMNAME' ) );
debug_print( "Application name: " .. get_application_name() );
debug_print( "Window name: " .. get_window_name() );
debug_print( "Window Type: " .. get_window_type() );
debug_print( "Class instance name: " .. get_class_instance_name() );
debug_print( "Window class: " .. get_window_class() );
x, y =  get_screen_geometry();
print( "Screen Geometry: x = " ..x.." y = "..y );
x, y, w, h = get_window_geometry();
print( "Window geometry:  x = " ..x.." y = "..y.." w = "..w.." h = "..h );
```

## Sample event output

Use standard VM names such as `work` and `personal` in documentation examples. These are standard Qubes OS VMs available during installation and keep the examples generic.

```text
Domain: work
Application name: work:org.example.App
Window name: Example
Window Type: WINDOW_TYPE_NORMAL
Class instance name: work:Example
Window class: work:org.example.App
Screen Geometry: x = 3840.0 y = 2160.0
Window geometry:  x = 474.0 y = 359.0 w = 3366.0 h = 1801.0
```

A second standard-VM example can use `personal`:

```text
Domain: personal
Application name: personal:org.example.App
Window name: Example
Window Type: WINDOW_TYPE_NORMAL
Class instance name: personal:Example
Window class: personal:org.example.App
Screen Geometry: x = 3840.0 y = 2160.0
Window geometry:  x = 0.0 y = 46.0 w = 2122.0 h = 1578.0
```

## Important event notes

1. `devilspie2 --debug` prints an initial startup dump for all currently known or processed windows.
2. After startup, `devilspie2 --debug` behaves like an append-only event stream.
3. Capturing the first debug output is not target selection.
4. Capturing the next event after startup is unreliable because menus and launchers can generate intermediary events.
5. The current `d2wc.lua` already filters non-normal windows with `WINDOW_TYPE_NORMAL`.
6. The remaining practical issue is which normal event to act on.
7. For now, accept duplicate configurator openings and rely on later suppression for windows that already have a profile or handling rule.

## Known future grammar issue

Some useful Devilspie2 values contain spaces.

Example:

```text
Window class: personal:Example App
```

The current `d2wc.lua` prefixed grammar splits rules on whitespace, so a token such as `c:Example App` cannot be represented safely yet. This should be handled in a later grammar update before rule editing supports values containing spaces.

## Immediate UI proof scope

The next UI proof should be small:

1. Accept representative event data from a Python fixture or command arguments.
2. Open GTK with clear sections for identity and geometry.
3. Display the captured event values.
4. Perform no config writes.
5. Perform no automatic rule generation.
6. Avoid live target-selection experiments in this branch.
7. Later UI stages can wire displayed event data into the already-tested `GEOM` and `WORKSPACE_PLACEMENT` core edit operations first.

## Relationship to PR #16 and Issue #17

PR #16 is an open draft research PR. It should not be merged as-is.

Issue #17 tracks the extracted UI direction and event-data model.

This document is the repository-local version of that direction so future work does not depend on conversation history or PR comments.
