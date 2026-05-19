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

The configurator should be reachable in three ways.

1. System tray menu. The user clicks the tray icon with either mouse button and chooses `Configure`.
2. Direct post-resize flow. The user resizes a window, releases the primary mouse button, and `d2wc` opens the configurator directly for that window.
3. Post-resize choice menu. The user resizes a window, releases the primary mouse button, and `d2wc` opens a small pointer-anchored menu with `Cancel` and `Configure`.

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

The generated values should account for:

1. Screen width and height.
2. Panel or reserved desktop areas where discoverable.
3. Multi-monitor layouts.
4. Window manager decoration differences where they affect actual placement.
5. Any required left-edge correction.

The user should still be able to override the derived values.

## Left-edge correction research item

The current Lua script supports `LEFT_EDGE_CORRECTION` because `set_window_geometry()` may place a window a few pixels away from `x = 0` on some systems.

The development task is to test whether the logic can be simplified by using `set_window_position()` or `set_window_position2()` consistently after setting geometry, or only when the resulting window geometry is wrong.

The safe design is to keep `LEFT_EDGE_CORRECTION` for now. It is a compatibility feature and should remain configurable until testing proves it can be replaced.

## Technology direction

The configurator should be portable across common Linux distributions where practical.

The implementation language and GUI toolkit are not decided yet. The first technical decision should compare lightweight, distribution-friendly options with a bias toward open-source tooling, simple packaging, and low runtime friction.

Likely evaluation criteria:

1. Can it provide a system tray icon reliably?
2. Can it observe window resize events or cooperate with a daemon that does?
3. Can it read and write the Lua configuration safely?
4. Can it run on Qubes OS and ordinary Linux desktops?
5. Can it be packaged cleanly for Fedora and Debian-family systems?
6. Can it avoid a heavy dependency stack?

## Development document status

This document is intentionally a working brief. It should evolve into a more exact development specification as UI decisions, daemon mechanics, and storage format decisions are made.
