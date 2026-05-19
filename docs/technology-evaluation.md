# d2wc Technology Evaluation

## Purpose

This document evaluates practical implementation choices for the future `d2wc` configurator and daemon/helper.

The decision must serve the actual product shape described in the current design documents:

1. A small Linux desktop configurator.
2. A tray icon and tray menu.
3. A main configuration window.
4. Active-window capture.
5. Safe parsing and writing of the managed Lua sections.
6. Later post-resize detection.
7. Later pointer-anchored `Cancel` / `Configure` menu.
8. Packaging for common Linux distributions.
9. Good behavior on Qubes OS with XFCE, while remaining useful on other Linux desktops.

## Evaluation criteria

The chosen stack should be judged against these criteria.

### Required

1. Open-source friendly licensing.
2. Available on Fedora and Debian-family systems.
3. Reasonable packaging path.
4. Can create a simple desktop window.
5. Can provide a tray icon or equivalent control point.
6. Can show menus and dialogs reliably.
7. Can call out to helper tools or libraries for window identity and geometry.
8. Can safely read, validate, preview, back up, and write text files.
9. Can be developed quickly enough to get a working Phase 1 configurator.

### Strongly preferred

1. Low dependency weight.
2. Mature Linux desktop behavior.
3. Good documentation.
4. Testable parser/writer code.
5. A clear split between UI code and core rule-management code.
6. No JavaScript or webview dependency unless it solves a real problem.

### Not required for Phase 1

1. Cross-platform Windows or macOS support.
2. Wayland-first behavior.
3. Highly themed or flamboyant UI.
4. Live geometry updates while resizing.
5. Full daemon/window-event monitoring.

## Initial platform assumption

The first implementation should target Linux/X11-style desktop behavior because the current Lua execution layer uses `devilspie2`, and the original working environment is Qubes OS with XFCE.

Wayland support should not drive the first implementation. If a future desktop environment prevents the same level of window inspection or movement, that should be documented as a compatibility limitation rather than allowed to block the first useful version.

## Candidate: Python + Qt for Python/PySide6

### Summary

Python with PySide6 is the strongest first candidate for the configurator UI and possibly the helper process.

### Strengths

1. Python is fast for prototyping and simple file manipulation.
2. Parser, validator, backup, and writer logic can be cleanly unit tested.
3. Qt has a documented `QSystemTrayIcon` API for tray icons, context menus, visibility, and tray availability checks.
4. Qt can position popup windows and small dialogs more easily than many minimal toolkit options.
5. PySide6 avoids PyQt's GPL/commercial-only licensing problem for this project direction.
6. A single Python application can initially contain both the UI and helper behavior.

### Weaknesses

1. Qt is heavier than a minimal GTK utility.
2. Desktop integration may feel less native on GNOME-style desktops than a GTK application.
3. Packaging must ensure the correct PySide6 dependency is available on target distributions.
4. Tray behavior still depends on the user's desktop environment exposing a tray or StatusNotifier-compatible area.

### Assessment

This is the recommended Phase 1 default unless testing on the actual target system shows a blocker.

The tray requirement is important enough that Qt's mature tray abstraction outweighs the extra dependency weight.

## Candidate: Python + GTK/PyGObject

### Summary

Python with GTK/PyGObject is a strong Linux-native UI option, but the tray icon requirement makes it less attractive as the default.

### Strengths

1. GTK is natural on many Linux desktops.
2. PyGObject is a common Python path for GTK applications.
3. Python remains excellent for parser/writer logic.
4. The UI can be small and native-looking.
5. Distribution packaging is generally practical.

### Weaknesses

1. GTK's old `GtkStatusIcon` tray API is deprecated.
2. A modern tray/status-notifier implementation may require extra libraries or desktop-specific handling.
3. The tray icon is not a side feature for `d2wc`; it is one of the primary entry points.
4. GTK 3 versus GTK 4 choices could complicate long-term direction.

### Assessment

This remains a good fallback if the tray design changes or if testing proves a reliable StatusNotifier/AppIndicator path that does not add too much complexity.

It is not the first recommendation because the tray requirement is central.

## Candidate: C or C++ with GTK or Qt

### Summary

C or C++ would produce a traditional native Linux desktop application, but would slow down early development.

### Strengths

1. Mature native toolkit access.
2. Strong packaging story for compiled applications.
3. Direct access to lower-level desktop libraries if needed.
4. Good long-term performance.

### Weaknesses

1. More code for the same Phase 1 result.
2. Slower iteration while product behavior is still being discovered.
3. More careful memory/resource handling.
4. Higher friction for parser/writer tests compared with Python.

### Assessment

Not recommended for the first implementation.

The early project needs fast iteration and precise behavior discovery more than it needs compiled-language performance.

## Candidate: Rust with GTK, Iced, or Slint

### Summary

Rust is attractive for a long-term robust application, but it is not the best first step for this project.

### Strengths

1. Strong correctness and type safety.
2. Good long-term maintainability when the architecture is stable.
3. Good packaging potential.
4. Useful for low-level helper behavior if needed later.

### Weaknesses

1. Slower first prototype compared with Python.
2. GUI ecosystem choices require more up-front commitment.
3. Tray and desktop integration still need specific testing.
4. The current biggest risk is product/runtime behavior, not memory safety.

### Assessment

Keep Rust as a possible future rewrite or helper language, not as the first configurator implementation.

## Candidate: Go with GTK bindings

### Summary

Go is simple to deploy for many command-line tools, but GUI binding maturity and desktop integration make it a weaker fit here.

### Strengths

1. Simple compiled binary story.
2. Good for daemons and helper processes.
3. Straightforward file and process management.

### Weaknesses

1. Linux GUI bindings are less standard than Python + Qt or Python + GTK.
2. Tray/menu behavior still needs binding-specific validation.
3. More risk around desktop integration.
4. Less natural for building a polished Linux configuration UI.

### Assessment

Not recommended for the first UI.

Go could be reconsidered for a small helper daemon only if the UI and daemon are split later.

## Candidate: Webview or browser-based UI

### Summary

A webview UI should not be the first implementation.

### Strengths

1. Easy to create forms and previews.
2. Could make a visually flexible interface.
3. Web UI skills are common.

### Weaknesses

1. Adds a web stack for a small desktop utility.
2. Increases dependency and packaging complexity.
3. Does not naturally solve tray icon behavior.
4. Does not naturally solve window identity or resize monitoring.
5. Conflicts with the project's preference for a minimal native utility.

### Assessment

Do not use a webview for Phase 1.

It adds more surface area than it removes.

## Candidate: Shell scripts plus dialogs

### Summary

Shell scripts with tools such as Zenity, YAD, or KDialog could prototype a few workflows, but should not become the product architecture.

### Strengths

1. Very fast for throwaway experiments.
2. Good for testing window geometry commands.
3. Easy to inspect.

### Weaknesses

1. Poor long-term UI structure.
2. Harder to build a reliable rule preview and conflict UI.
3. Harder to maintain as behavior grows.
4. Tray and post-resize behavior become messy quickly.

### Assessment

Useful for experiments, not recommended for the configurator.

Shell scripts may still be useful for isolated test harnesses, especially left-edge correction testing.

## Recommended Phase 1 stack

The recommended Phase 1 stack is:

1. Python 3.
2. PySide6 / Qt for Python for the UI.
3. A pure-Python core package for parsing, validating, rendering, backing up, and saving managed Lua sections.
4. A small application entry point that starts the UI and, where available, the tray icon.
5. Subprocess calls or small helper modules for desktop/window inspection during early testing.

This gives the project a practical path to a working manual configurator without prematurely solving every daemon and post-resize problem.

## Proposed Phase 1 internal structure

When implementation starts, the source tree can evolve toward:

```text
src/
  d2wc.lua
  d2wc/
    __init__.py
    app.py
    config_model.py
    lua_blocks.py
    validation.py
    backup.py
    window_info.py
    ui/
      main_window.py
      tray.py
```

The important design point is that Lua parsing and rule validation must not be buried inside UI widgets.

The core logic should be testable without starting the GUI.

## Phase 1 proof tasks

Before committing fully to PySide6, build tiny proof tasks:

1. Open a main window.
2. Create a tray icon with a context menu.
3. Detect whether the system tray is available.
4. Capture or receive active-window identity through the chosen method.
5. Read the current `src/d2wc.lua` managed sections.
6. Render those sections back without changing semantics.
7. Save a backup and updated file in a test directory.

If these pass on the target Qubes/XFCE environment, PySide6 should become the accepted Phase 1 stack.

## Phase 2 technology questions

Post-resize behavior still needs separate testing.

Open questions:

1. Which event source best identifies user-initiated resize completion on the target desktop?
2. Can that event source distinguish user resize from `d2wc` geometry application?
3. Can pointer-anchored menu placement be implemented consistently?
4. How does swapped mouse-button behavior appear to the chosen toolkit?
5. How does the behavior differ across XFCE, KDE, GNOME, and other desktops?

These questions should be handled in `docs/event-monitoring.md` after the Phase 1 stack is chosen.

## Current recommendation

Use Python + PySide6 for the first prototype.

Do not start with GTK unless tray behavior is deliberately moved out of scope or a clean StatusNotifier/AppIndicator path is chosen and tested.

Do not start with Rust, Go, C, or C++ unless Python + PySide6 fails a practical proof task on the target system.

Do not use a webview for the first implementation.

## Review checkpoint

Before writing real application code, confirm these points:

1. PySide6 is acceptable as a project dependency.
2. The first implementation may target X11/Qubes/XFCE behavior first.
3. Wayland support can be treated as later compatibility work.
4. Phase 1 may include tray behavior, but post-resize automation remains Phase 2.
5. The parser/writer core must be separated from the UI.
