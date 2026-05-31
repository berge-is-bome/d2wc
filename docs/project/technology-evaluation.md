# d2wc Technology Evaluation

## Purpose

This document evaluates practical implementation choices for the future `d2wc` configurator and daemon/helper.

The decision must serve the actual product shape described in the current design documents:

1. A small Linux desktop configurator.
2. A command/manual launch path suitable for assigning to a desktop keyboard shortcut.
3. An optional tray icon and tray menu for setup or troubleshooting.
4. A main configuration window.
5. Active-window capture.
6. Safe parsing and writing of the managed Lua sections.
7. Later post-resize detection.
8. Later pointer-anchored `Cancel` / `Configure` menu.
9. Packaging for common Linux distributions.
10. Good behavior on Qubes OS with XFCE, while remaining useful on other Linux desktops.
11. A development roadmap that can later support Qt/KDE-oriented users without rewriting the core logic.

## Evaluation criteria

The chosen stack should be judged against these criteria.

### Required

1. Open-source friendly licensing.
2. Available on Fedora and Debian-family systems.
3. Reasonable packaging path.
4. Can create a simple desktop window.
5. Can provide a command-line entry point for the configurator.
6. Can show menus and dialogs reliably.
7. Can call out to helper tools or libraries for window identity and geometry.
8. Can safely read, validate, preview, back up, and write text files.
9. Can be developed quickly enough to get a working Phase 1 configurator.
10. Fits Qubes OS with XFCE well as the first target environment.
11. Allows a future Qt/KDE front end without replacing the parser/writer core.

### Strongly preferred

1. Low dependency weight.
2. Mature Linux desktop behavior.
3. Good documentation.
4. Testable parser/writer code.
5. A clear split between UI code and core rule-management code.
6. No JavaScript or webview dependency unless it solves a real problem.
7. Optional tray support, provided it does not dominate the architecture.

### Not required for Phase 1

1. Wayland-first behavior.
2. Highly themed or flamboyant UI.
3. Live geometry updates while resizing.
4. Full daemon/window-event monitoring.
5. A Qt/KDE-specific UI.

## Initial platform assumption

The first implementation should target Linux/X11-style desktop behavior because the current Lua execution layer uses `devilspie2`, and the original working environment is Qubes OS with XFCE.

Wayland support should not drive the first implementation. If a future desktop environment prevents the same level of window inspection or movement, that should be documented as a compatibility limitation rather than allowed to block the first useful version.

## Candidate: Python + GTK/PyGObject

### Summary

Python with GTK/PyGObject is the preferred first UI candidate for the Phase 1 configurator.

This became the stronger choice after the tray icon was moved from required primary entry point to optional setup/troubleshooting behavior. The stable entry point is now a command that can be assigned to a keyboard shortcut, which removes the biggest reason to prefer Qt first.

For Qubes OS with XFCE, a GTK application is likely to fit the desktop better than a Qt application, and the UI requirements are modest enough that GTK should be able to handle the Phase 1 configurator cleanly.

### Strengths

1. GTK is natural on many Linux desktops and should fit Qubes/XFCE well.
2. PyGObject is a common Python path for GTK applications.
3. Python remains excellent for parser/writer logic.
4. The UI can be small and native-looking.
5. Distribution packaging is generally practical.
6. The command/keyboard-shortcut entry point does not depend on tray support.
7. The optional-tray decision avoids building the architecture around deprecated or desktop-specific tray behavior.

### Weaknesses

1. GTK's old tray/status-icon path is not a good foundation for a permanently visible tray icon.
2. A modern tray/status-notifier implementation may require extra libraries or desktop-specific handling if optional tray mode is added later.
3. GTK 3 versus GTK 4 needs a deliberate choice.
4. Pointer-anchored menu behavior still needs testing.
5. KDE users may prefer a Qt-native UI in a later version.

### Assessment

Recommended as the first Phase 1 UI candidate.

The first proof should start with Python + GTK/PyGObject unless a practical test on the target Qubes/XFCE environment exposes a blocker.

## Candidate: Python + Qt for Python/PySide6

### Summary

Python with PySide6 remains a strong fallback candidate for the configurator UI and possibly the helper process.

The earlier assumption that the tray icon was a required primary entry point made PySide6 look like the obvious default. With the tray now optional and the command/keyboard-shortcut path promoted to the stable entry point, PySide6 is no longer the first default.

Qt should still be on the development roadmap because many Linux users run KDE Plasma or other Qt-friendly environments. If `d2wc` becomes useful outside Qubes/XFCE, a Qt front end may offer a better desktop fit for KDE users.

### Strengths

1. Python is fast for prototyping and simple file manipulation.
2. Parser, validator, backup, and writer logic can be cleanly unit tested.
3. Qt has a mature tray abstraction if optional tray mode is implemented.
4. Qt can position popup windows and small dialogs more easily than many minimal toolkit options.
5. PySide6 avoids PyQt's GPL/commercial-only licensing problem for this project direction.
6. A single Python application can initially contain both the UI and helper behavior.
7. Qt is the natural long-term UI path for KDE-oriented users.

### Weaknesses

1. Qt is heavier than a minimal GTK utility.
2. Desktop integration may feel less native in the first target environment.
3. Packaging must ensure the correct PySide6 dependency is available on target distributions.
4. Optional tray behavior still depends on the user's desktop environment exposing a tray or StatusNotifier-compatible area.

### Assessment

Recommended as the fallback Phase 1 UI candidate if GTK/PyGObject fails a practical proof task.

Recommended as a later roadmap item for KDE and non-Qubes desktop support, provided the core parser/writer logic remains UI-toolkit independent.

PySide6 becomes especially attractive again if optional tray mode or pointer-anchored popup behavior proves much easier in Qt than GTK.

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
3. Tray and desktop integration still need specific testing if optional tray mode is implemented.
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

1. Linux GUI bindings are less standard than Python + GTK or Python + Qt.
2. Optional tray/menu behavior still needs binding-specific validation.
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
3. Does not naturally solve window identity or resize monitoring.
4. Conflicts with the project's preference for a minimal native utility.

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
4. Post-resize behavior becomes messy quickly.

### Assessment

Useful for experiments, not recommended for the configurator.

Shell scripts may still be useful for isolated test harnesses, especially left-edge correction testing.

## Toolkit roadmap

The UI should be kept separate from the core rule-management logic.

The long-term roadmap should allow multiple front ends to share the same backend:

1. Core parser/writer/validator package.
2. GTK front end for the first Qubes/XFCE-centered implementation.
3. Qt front end or Qt mode later for KDE-oriented users and distributions where Qt integration is preferred.
4. Optional CLI or diagnostic commands for testing and support.

This does not mean the project should build two full GUIs immediately. It means the first implementation should avoid coupling business logic to GTK widgets so that a later Qt front end can reuse the same core.

## Recommended Phase 1 stack

The recommended Phase 1 direction is:

1. Python 3.
2. GTK/PyGObject as the first UI proof target.
3. PySide6 as the fallback proof target if GTK exposes a practical blocker.
4. PySide6 or another Qt path as a later roadmap item for KDE-oriented users.
5. A pure-Python core package for parsing, validating, rendering, backing up, and saving managed Lua sections.
6. A command-line application entry point that starts the configurator.
7. Optional tray support only if the chosen toolkit handles it cleanly.
8. Subprocess calls or small helper modules for desktop/window inspection during early testing.

This gives the project a practical path to a working manual configurator without prematurely solving every daemon, tray, and post-resize problem.

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
      gtk/
        main_window.py
      qt/
        README.md
      shortcut_entry.md
      tray.py
```

The important design point is that Lua parsing and rule validation must not be buried inside UI widgets.

The core logic should be testable without starting the GUI.

The `ui/qt/` path should not be implemented until there is a real need, but leaving room for it helps avoid a GTK-only architecture.

## Phase 1 proof tasks

Before committing fully to GTK/PyGObject, build tiny proof tasks:

1. Open a main window from a command.
2. Confirm the command can be assigned to a desktop keyboard shortcut.
3. Capture or receive active-window identity through the chosen method.
4. Read the current `src/d2wc.lua` managed sections.
5. Render those sections back without changing semantics.
6. Save a backup and updated file in a test directory.
7. Optional: create a tray icon with a context menu.
8. Optional: detect whether the system tray is available.

If these pass on the target Qubes/XFCE environment, GTK/PyGObject should become the accepted Phase 1 stack.

If GTK fails a practical proof task, repeat the same proof tasks with PySide6.

## Phase 2 technology questions

Post-resize behavior still needs separate testing.

Open questions:

1. Which event source best identifies user-initiated resize completion on the target desktop?
2. Can that event source distinguish user resize from `d2wc` geometry application?
3. Can pointer-anchored menu placement be implemented consistently?
4. How does swapped mouse-button behavior appear to the chosen toolkit?
5. How does the behavior differ across XFCE, KDE, GNOME, and other desktops?
6. What parts of the UI need toolkit-specific implementations versus shared core behavior?

These questions should be handled in [Event Monitoring](event-monitoring.md) after the Phase 1 command/manual configurator path is clear.

## Current recommendation

Use Python for the first prototype.

Use GTK/PyGObject as the first UI proof target because the first target environment is Qubes/XFCE and the tray icon is optional.

Keep PySide6 as the fallback UI proof target if GTK/PyGObject fails a practical test.

Keep Qt on the development roadmap for KDE-oriented users and broader non-Qubes Linux support.

Do not choose a toolkit primarily because of a tray icon. The stable entry point should be a command that the user can bind to a keyboard shortcut.

Do not start with Rust, Go, C, or C++ unless Python fails a practical proof task on the target system.

Do not use a webview for the first implementation.

## Related documents

1. [Runtime Architecture](runtime-architecture.md)
2. [Event Monitoring](event-monitoring.md)
3. [Implementation Plan](implementation-plan.md)
4. [Testing](testing.md)
5. [Packaging](packaging.md)

## Review checkpoint

Before writing real application code, confirm these points:

1. Python is acceptable as the first implementation language.
2. GTK/PyGObject should be tested first for the UI toolkit.
3. PySide6 remains the fallback toolkit if GTK exposes a blocker.
4. Qt remains on the roadmap for KDE-oriented users.
5. The first implementation may target X11/Qubes/XFCE behavior first.
6. Wayland support can be treated as later compatibility work.
7. Phase 1 uses a command/keyboard-shortcut entry point.
8. Tray behavior is optional and should not drive the architecture.
9. Post-resize automation remains Phase 2.
10. The parser/writer core must be separated from the UI.
