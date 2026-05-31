# Lua Configurables

`d2wc` stores its window rules in a managed Lua file. In normal use, you configure those rules through the GTK configurator instead of editing Lua by hand.

## Rule targets

Most rules are based on one or both of these fields:

1. Machine: the Qubes domain when available.
2. Application: the application class.

A rule can apply to:

1. one Machine and one Application,
2. all Applications from one Machine,
3. one Application from any Machine.

In the configurator, `All` means that the rule is not limited by that field.

## Exclude windows

Use `Exclude` when `d2wc` should leave a window alone.

Exclusions are useful for menus, helper windows, splash windows, notifications, panels, or any application that should not be moved, resized, pinned, or corrected.

Common choices:

1. Exclude one specific Machine/Application combination.
2. Exclude all windows from one Machine.
3. Exclude one Application everywhere.

## Pin windows

Use `Pin` when matching windows should stay visible on all workspaces.

This is useful for utility windows, notes, status windows, or other windows that should remain available while you move between workspaces.

Common choices:

1. Pin one specific Machine/Application combination.
2. Pin all windows from one Machine.
3. Pin one Application everywhere.

## Route windows to workspaces

Use `Workspace routes` to send matching windows to a workspace.

User-facing intent:

```text
When this window opens, send it to workspace N.
```

A route can target one Machine/Application combination, one Machine, or one Application everywhere.

## Create window geometry profiles

Use `Window geometry` to save reusable window size and position profiles.

A geometry profile stores:

1. `x`
2. `y`
3. `w`
4. `h`

User-facing intent:

```text
Save this reusable window size and position.
```

Geometry profiles do not choose which windows they affect. They become useful when a placement rule links a profile to a window target.

## Place windows with geometry profiles

Use `Workspace placement` to apply a saved geometry profile to matching windows.

User-facing intent:

```text
When this window opens, use this saved size and position.
```

A placement rule links a Machine, an Application, or a Machine/Application combination to a named geometry profile.

## Correct left-edge placement

Use `Left edge correction` only when a window should land on the left edge of the screen but does not.

Most users should not need to configure this during normal setup. It is a compatibility workflow for systems where the window manager places a window slightly away from the requested left edge.

## Behavior settings

The configurator also has behavior settings under:

```text
Menu -> Configure -> Behavior
```

These settings control whether `d2wc` opens automatically for unconfigured windows, and whether it opens the full configurator directly or shows the small Cancel/Configure prompt first.
