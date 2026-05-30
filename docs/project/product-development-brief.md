# d2wc Product Development Brief

## Purpose

`d2wc` is a desktop workspace and window placement configurator for Linux systems using `devilspie2` as the window rules engine.

The project started from a Qubes OS workflow, where windows need to be placed predictably by qube/domain, application class, workspace, and geometry. The project is now being generalized so the same idea can be useful on other Linux desktops where `devilspie2` can observe and control windows.

The central goal is to let a user configure window behavior without hand-editing Lua. The Lua script remains the execution layer, but the configurator should become the normal way a user captures, reviews, and updates rules.

## User outcome

A user should be able to arrange their desktop once, then tell `d2wc` to remember that behavior.

Typical examples:

1. Always open a file manager on workspace 1 with a wide geometry.
2. Always open a PDF viewer on the right half of the screen.
3. Always open a specific application from a specific domain on the left half of the screen.
4. Pin selected windows so they are visible on all workspaces.
5. Exclude menus, splash windows, panels, or troublesome applications from automation.
6. Capture a resized window and convert that geometry into a reusable profile.
7. Generate matching `half_left` and `half_right` profiles from screen geometry and a configured window border width.

## Operating model

`d2wc` has two parts:

1. A `devilspie2` Lua script that applies rules when windows appear.
2. A configurator application that edits the user-customizable sections of that Lua script.

The configurator should not rewrite arbitrary Lua logic. It should edit only the known configuration blocks:

1. `EXCLUDE`
2. `PIN`
3. `WORKSPACE_ROUTES`
4. `WORKSPACE_PLACEMENT`
5. `LEFT_EDGE_CORRECTION`
6. Geometry profiles in `GEOM`, because placement rules depend on named profiles.

## Configurator entry points

The stable entry point should be a command that can be assigned to a desktop keyboard shortcut.

The configurator should be reachable in these ways:

1. Command or keyboard shortcut. The user focuses or places a window, presses the configured shortcut, and `d2wc` opens the configurator for the active window.
2. Automatic window-event handoff. Devilspie2 sees a new unconfigured normal window and opens the selected `d2wc` entry point.
3. Prompt handoff. Devilspie2 sees a new unconfigured normal window and opens a small prompt with `Cancel` and `Configure`.
4. Direct post-resize flow. The user resizes a window, releases the primary mouse button, and `d2wc` opens the configurator directly for that window.
5. Post-resize choice menu. The user resizes a window, releases the primary mouse button, and `d2wc` opens a small pointer-anchored menu with `Cancel` and `Configure`.

The pointer-anchored menu should center the pointer on `Cancel` by default. This protects the user from accidentally configuring a window after every resize. `Configure` should be the second action in the menu.

Mouse button handling must not assume a right-handed mouse layout. Some users swap primary and secondary buttons, so the UI logic should talk in terms of primary and secondary actions where possible rather than hard-coding left and right button assumptions.

## Daemon behavior

`d2wc` can run as a daemon or background helper. The daemon watches for relevant window events, especially:

1. New normal application windows.
2. Window resize start.
3. Window resize end.
4. Current window geometry changes.

The daemon should use `devilspie2` and the window system where appropriate. The current Lua script already uses `devilspie2` functions such as `get_window_geometry()`, `get_screen_geometry()`, and `set_window_geometry()` as the natural integration surface.

A nice-to-have feature is live geometry display in the configurator while the user resizes a window. This means the configurator would show `{ x, y, w, h }` updating as the resize happens.

## UI principles

The UI should be minimal, practical, and fast.

It should not try to be a large desktop environment control panel. It should be a focused rule editor that guides the user through the smallest amount of input needed.

The main configurator window should likely have these areas:

1. Current window summary: domain, class, title, workspace, and current geometry.
2. Suggested action: save workspace route, save geometry, pin, exclude, or apply half-left/half-right.
3. Rule preview: the exact rule that will be written.
4. Existing matching rules: any current rule that already affects this window.
5. Apply controls: save, cancel, edit manually, or test without saving.

## Automated half-left and half-right behavior

The `half_left` and `half_right` profiles should become mostly automated.

The configurator should derive these from the active screen instead of expecting the user to manually enter pixel values. On a simple single-monitor layout, `half_left` should represent the left half of the usable screen area and `half_right` should represent the right half.

When two equal-size windows are placed side by side using `half_left` and `half_right`, window borders can cause the apparent combined width to be wrong. `d2wc` should therefore provide a configurable `window_border_width` value. The user can adjust that one pixel value, preview the regenerated split profiles, and avoid manually nudging the width and x-position values.

The generated values should account for:

1. Screen width and height.
2. Panel or reserved desktop areas where discoverable.
3. Multi-monitor layouts.
4. Window manager decoration differences where they affect actual placement.
5. Configured `window_border_width`.
6. Any required left-edge correction.

The user should still be able to override the derived values.

## Left-edge correction research item

The current Lua script supports `LEFT_EDGE_CORRECTION` because `set_window_geometry()` may place a window a few pixels away from `x = 0` on some systems.

Manual testing has shown that this incorrect position is visible through `get_window_geometry()`. That means `d2wc` can detect the offset after applying geometry and then test or apply `set_window_position()` or `set_window_position2()` only when needed.

The safe design is to keep `LEFT_EDGE_CORRECTION` for now. It is a compatibility feature and should remain configurable until testing proves it can be replaced.

## Technology direction

The first implementation should use Python, with GTK/PyGObject as the first UI proof target for Qubes/XFCE. The core parser, writer, validator, and rule model should remain independent from GTK so a future Qt front end can support KDE-oriented users.

Evaluation criteria:

1. Can it open the configurator from a command or keyboard shortcut?
2. Can it observe window resize events or cooperate with a daemon that does?
3. Can it read and write the Lua configuration safely?
4. Can it run on Qubes OS and ordinary Linux desktops?
5. Can it be packaged cleanly for Fedora and Debian-family systems?
6. Can it avoid a heavy dependency stack?
7. Can the non-UI core be reused by a future Qt/KDE front end?

## Related documents

1. [UI Flow](ui-flow.md)
2. [Runtime Architecture](runtime-architecture.md)
3. [Technology Evaluation](technology-evaluation.md)
4. [Implementation Plan](implementation-plan.md)
5. [Testing](testing.md)

## Development document status

This document is intentionally a working brief. It should evolve into a more exact development specification as UI decisions, daemon mechanics, and storage format decisions are made.
