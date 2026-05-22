# Devilspie2 Window Probe Reference

## Purpose

This document records the Devilspie2 functions planned for `d2wc` window inspection before any rule-generation or rule-editing workflow is built.

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

## Current proof script

The current proof deliberately tests only one Devilspie2 function first:

```lua
local class_instance_name = get_class_instance_name()

debug_print("D2WC_CLASS_PROBE_BEGIN")
debug_print( "Class instance name: " .. safe(class_instance_name) );
debug_print("D2WC_CLASS_PROBE_END")
```

The Lua function is called directly into a local variable. `debug_print` is used only to get the value out of the Devilspie2 process and into the Python/GTK proof.

Expected proof output shape:

```text
Class instance name: thunderbird-personal:Mail
```

## Planned next probe functions

After `get_class_instance_name()` is proven end-to-end, add the remaining probe functions one at a time:

```lua
get_window_property( '_QUBES_VMNAME' )
get_screen_geometry()
get_window_geometry()
```

Keep the exact call form for the Qubes property:

```lua
get_window_property( '_QUBES_VMNAME' )
```

The spaces around `'_QUBES_VMNAME'` are intentionally documented here because this is the known working form used during manual testing.

## Full manual reference probe

The broader manual probe used during design discussion was:

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

Do not add all of these to the application proof at once. Keep the application path small and test one additional function at a time.

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

### `get_class_instance_name()`

Returns the class instance name. This is historically the closest match to the `c:` rule token used in `d2wc.lua`.

Examples:

```text
thunderbird-personal:Mail
```

```text
disp3979:Navigator
```

The current proof captures only this field.

### `get_window_property( '_QUBES_VMNAME' )`

Returns the Qubes VM name where available.

Observed behavior:

1. Non-empty value means the VM/domain name.
2. Empty value means a dom0 window.

This is useful for deciding whether a captured window belongs to dom0. The VM/domain name is also usually present as the first string before `:` in values such as `get_application_name()`, but `_QUBES_VMNAME` is still the clearer dom0 test.

### `get_screen_geometry()`

Returns the screen dimensions visible to Devilspie2.

Example:

```text
Screen Geometry: x = 3840.0 y = 2160.0
```

### `get_window_geometry()`

Returns the current window rectangle.

Example:

```text
Window geometry:  x = 474.0 y = 359.0 w = 3366.0 h = 1801.0
```

The uppercase `Geometry:` line should mean the x/y/w/h rectangle of the probed window. The lowercase `geometry` line should mean the width-by-height size string.

## Additional useful Devilspie2 functions

These are useful, but not part of the current proof path:

```lua
get_application_name()
get_window_name()
get_window_type()
get_window_class()
```

Some applications are easier to identify through `get_window_class()` or `get_application_name()` than through `get_class_instance_name()`.

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
2. Capture one event-reported `get_class_instance_name()` value.
3. Display that single value in GTK.
4. Avoid reading or writing the user's real config files.
5. Avoid rule editing or save workflows.

Rule generation, class-value selection, additional probe functions, space-handling in rule tokens, and persistent config writes are later stages.
