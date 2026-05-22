# Devilspie2 Window Probe Reference

## Purpose

This document records the Devilspie2 functions used by `d2wc` to inspect a window before any rule-generation or rule-editing workflow is built.

Devilspie2 is the source of truth for this project because the runtime Lua rules use Devilspie2 APIs directly. External tools such as `xwininfo` are useful for manual diagnostics, but the configurator should prefer Devilspie2 probe data where possible.

## Probe invocation

A manual probe can be tested from dom0 with a `debug.lua` file under:

```text
~/.config/devilspie2/debug.lua
```

Then run:

```bash
devilspie2 --debug
```

Devilspie2 prints probe output when a matching window is created or processed. Stop the debug run with `Ctrl+C`.

The `d2wc` proof branch uses a temporary Devilspie2 config directory instead of the user's real `~/.config/devilspie2/` directory. That keeps the proof read-only with respect to the user's existing Devilspie2 setup.

## Probe script

The important probe functions are:

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

Keep the exact call form for the Qubes property:

```lua
get_window_property( '_QUBES_VMNAME' )
```

The spaces around `'_QUBES_VMNAME'` are intentionally documented here because this is the known working form used during manual testing.

## Sample output

Example Thunderbird output:

```text
Domain: thunderbird-personal
Application name: thunderbird-personal:net.thunderbird.Thunderbird
Window name: Mozilla Thunderbird
Window Type: WINDOW_TYPE_NORMAL
Class instance name: thunderbird-personal:Mail
Window class: thunderbird-personal:net.thunderbird.Thunderbird
Screen Geometry: x = 3840.0 y = 2160.0
Window geometry:  x = 474.0 y = 359.0 w = 3366.0 h = 1801.0
```

Example Tor Browser output:

```text
Domain: disp3979
Application name: disp3979:Tor Browser
Window name: Tor Browser
Window Type: WINDOW_TYPE_NORMAL
Class instance name: disp3979:Navigator
Window class: disp3979:Tor Browser
Screen Geometry: x = 3840.0 y = 2160.0
Window geometry:  x = 0.0 y = 46.0 w = 2122.0 h = 1578.0
```

## Field notes

### `get_window_property( '_QUBES_VMNAME' )`

Returns the Qubes VM name where available.

Observed behavior:

1. Non-empty value means the VM/domain name.
2. Empty value means a dom0 window.

This is useful for deciding whether a captured window belongs to dom0. The VM/domain name is also usually present as the first string before `:` in values such as `get_application_name()`, but `_QUBES_VMNAME` is still the clearer dom0 test.

### `get_application_name()`

Returns an application identifier that may include the Qubes VM prefix.

Example:

```text
thunderbird-personal:net.thunderbird.Thunderbird
```

The first string before `:` is often the VM/domain. The value after `:` may be a dotted application identifier.

### `get_window_name()`

Returns the user-facing window title.

Example:

```text
Mozilla Thunderbird
```

### `get_window_type()`

Returns the Devilspie2 window type.

The current Lua runtime rules only act on:

```text
WINDOW_TYPE_NORMAL
```

The probe should keep the same filter so non-normal windows such as panels, menus, splash screens, and notifications do not drive rule generation.

### `get_class_instance_name()`

Returns the class instance name. This is historically the closest match to the `c:` rule token used in `d2wc.lua`.

Examples:

```text
thunderbird-personal:Mail
```

```text
disp3979:Navigator
```

The current Lua class matching logic lowercases class values and supports matching dotted segments. This is why values such as `net.thunderbird.Thunderbird` can be matched by shorter tokens such as `thunderbird`.

### `get_window_class()`

Returns the window class.

Examples:

```text
thunderbird-personal:net.thunderbird.Thunderbird
```

```text
disp3979:Tor Browser
```

Some applications are easier to identify through `get_window_class()` or `get_application_name()` than through `get_class_instance_name()`.

### `get_screen_geometry()`

Returns the screen dimensions visible to Devilspie2.

Example:

```text
Screen Geometry: x = 3840.0 y = 2160.0
```

In the current proof this maps to a size string such as:

```text
screen 3840x2160
```

### `get_window_geometry()`

Returns the current window rectangle.

Example:

```text
Window geometry:  x = 474.0 y = 359.0 w = 3366.0 h = 1801.0
```

In the proof display this maps to:

```text
Geometry: x=474 y=359 w=3366 h=1801
geometry 3366x1801
```

The uppercase `Geometry:` line is the x/y/w/h rectangle of the probed window. The lowercase `geometry` line is the width-by-height size string.

## Known future issue: spaces in class-like values

Some useful Devilspie2 values contain spaces.

Example:

```text
Window class: disp3979:Tor Browser
```

The current `d2wc.lua` prefixed grammar splits rules on whitespace, so a token such as `c:Tor Browser` cannot be represented safely yet. This should be handled in a later grammar update before rule editing supports values containing spaces.

## Current proof boundary

The current proof should:

1. Use Devilspie2 as the source of truth.
2. Capture one `WINDOW_TYPE_NORMAL` report.
3. Display the parsed probe fields in GTK.
4. Avoid reading or writing the user's real config files.
5. Avoid rule editing or save workflows.

Rule generation, class-value selection, space-handling in rule tokens, and persistent config writes are later stages.
