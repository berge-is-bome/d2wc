# d2wc Runtime Architecture

## Purpose

This document describes how the runtime pieces of `d2wc` should fit together.

The UI flow describes what the user sees. This document describes what must exist behind that UI so `d2wc` can observe windows, capture geometry, update the Lua configuration safely, and keep `devilspie2` running with the intended rules.

## Architecture summary

`d2wc` should be designed as three cooperating parts:

1. The `devilspie2` Lua rules script.
2. The configurator UI.
3. A daemon/helper process, when event monitoring or tray behavior requires logic outside the Lua script.

The current repository starts with the Lua script as the only execution layer. The first implementation goal is to add a safe manual configurator. Post-resize automation and pointer-anchored menus should build on top of that foundation.

## Responsibilities

### `devilspie2`

`devilspie2` remains the window-rule engine.

It should continue to:

1. Receive window events from the desktop/window-manager environment.
2. Run the Lua script for matching windows.
3. Provide window information through built-in functions such as `get_window_type()`, `get_window_geometry()`, `get_screen_geometry()`, `get_class_instance_name()`, and `get_window_property()`.
4. Apply workspace routing, pinning, and geometry changes using `devilspie2` functions.

`devilspie2` should not be responsible for presenting a user-facing configuration UI.

### Lua rules script

The Lua script remains the active rules file.

It should continue to:

1. Filter out non-normal windows.
2. Read the window domain where `_QUBES_VMNAME` is available.
3. Treat an empty `_QUBES_VMNAME` value as `dom0`.
4. Read and normalize the application class.
5. Apply `EXCLUDE` before later automation.
6. Apply `WORKSPACE_ROUTES`.
7. Apply `PIN` after workspace assignment.
8. Resolve `WORKSPACE_PLACEMENT` into a named `GEOM` profile.
9. Apply geometry.
10. Apply `LEFT_EDGE_CORRECTION` when needed.

The configurator should edit the Lua script's managed configuration sections, not its program logic.

Managed sections:

1. `EXCLUDE`
2. `PIN`
3. `WORKSPACE_ROUTES`
4. `GEOM`
5. `WORKSPACE_PLACEMENT`
6. `LEFT_EDGE_CORRECTION`

### Configurator UI

The configurator UI is the normal user-facing editing tool.

It should:

1. Load the current managed Lua configuration.
2. Read the selected or active window identity.
3. Show current domain, class, workspace, screen, and geometry.
4. Let the user create or update rules without writing Lua manually.
5. Preview generated rules before saving.
6. Validate generated rules before saving.
7. Back up the previous Lua file before saving.
8. Write deterministic Lua for the managed sections.
9. Request a clean reload or restart after saving.

The configurator should not silently rewrite unrelated parts of the Lua script.

### Daemon/helper process

A daemon/helper may be required for behavior that is awkward or impossible inside `devilspie2` Lua alone.

The daemon/helper may own:

1. System tray icon.
2. Tray menu actions.
3. Active-window capture.
4. Post-resize detection.
5. Pointer-anchored `Cancel` / `Configure` menu.
6. Suppression of resize events caused by `d2wc` itself.
7. Relaunching or reloading `devilspie2` after configuration changes.
8. Debug logging.

The exact daemon implementation depends on the technology choice. The architecture should allow the daemon/helper and configurator to be the same process at first, then split later if needed.

## Phase 1 runtime

Phase 1 should avoid unnecessary event-monitoring complexity.

Required runtime pieces:

1. Current `devilspie2` Lua script.
2. Manual configurator UI.
3. A tray entry point, if the chosen toolkit supports it cleanly.
4. Config file reader/writer for the managed Lua sections.
5. Validation before save.
6. Backup before save.
7. Reload or restart path after save.

Phase 1 does not need to detect post-resize events yet. A user can manually place a window, open the configurator, capture the active window, and save the desired rule.

## Phase 2 runtime

Phase 2 adds desktop automation around the manual configurator.

Required runtime pieces:

1. Window resize start detection.
2. Window resize completion detection.
3. Pre-resize and post-resize geometry capture.
4. Resize threshold handling.
5. Suppression of resize events caused by automatic `d2wc` placement.
6. Post-resize setting:
   1. Disabled.
   2. Open configurator directly.
   3. Show pointer-anchored `Cancel` / `Configure` menu.
7. Configurator launch with the resized window preloaded.

Phase 2 should not change the underlying Lua grammar unless Phase 1 shows that the current managed sections are insufficient.

## Configuration file model

The initial storage model is the managed Lua script itself.

The configurator should treat the Lua file as a structured document with managed blocks rather than as arbitrary text.

The first implementation can parse the known block names:

1. `local EXCLUDE = { ... }`
2. `local PIN = { ... }`
3. `local WORKSPACE_ROUTES = { ... }`
4. `local GEOM = { ... }`
5. `local WORKSPACE_PLACEMENT = { ... }`
6. `local LEFT_EDGE_CORRECTION = { ... }`

The configurator should preserve program logic outside those blocks.

## Managed block writing

Managed blocks should be written in a deterministic style.

Required behavior:

1. Stable ordering where practical.
2. Valid Lua syntax.
3. Consistent indentation.
4. Clear comments where helpful.
5. No duplicate workspace keys.
6. No duplicate prefixes in generated rule strings.
7. No placement rule that references a missing geometry profile.
8. No left-edge correction rule with an invalid correction mode.

The configurator may preserve existing user comments where practical, but correctness and predictable output are more important than perfect comment preservation in the first implementation.

## Validation model

Validation should run before any file is written.

Validation should check:

1. Rule token grammar.
2. Required prefixes for each managed section.
3. Duplicate rules.
4. Duplicate workspace keys.
5. Unknown geometry profile references.
6. Invalid geometry values.
7. Invalid left-edge correction modes.
8. Workspace numbers outside the available workspace range, when that range is known.

The configurator should explain validation failures in user language.

Example:

```text
This placement rule uses geometry profile `wide_right`, but no `wide_right` profile exists in GEOM.
```

## Backup model

Before writing a modified Lua file, the configurator must create a backup.

The backup should include:

1. Original file name.
2. Timestamp.
3. A clear suffix such as `.bak`.

Example backup name:

```text
d2wc.lua.2026-05-20-011530.bak
```

The backup directory can initially be the same directory as the Lua file. A later settings option can allow a dedicated backup directory.

## Save model

A safe save should use this order:

1. Parse current Lua file.
2. Apply pending user changes in memory.
3. Validate the resulting managed blocks.
4. Render updated Lua content.
5. Create a backup of the current file.
6. Write the new Lua file to a temporary file in the same directory.
7. Replace the old Lua file with the new file.
8. Reload or restart `devilspie2`.
9. Report success or failure to the user.

Writing to a temporary file first reduces the chance of leaving a truncated config if the process fails during save.

## Reload and restart model

The exact reload mechanism still needs testing.

Possible approaches:

1. Ask the user to run `devilspie2` through a `d2wc` launcher wrapper.
2. Have the helper process manage the `devilspie2` process lifecycle.
3. Send a signal if `devilspie2` supports an appropriate reload behavior in the target environment.
4. Stop and restart `devilspie2` after a successful save.

The first reliable implementation may use a conservative restart if it can identify only the `d2wc`-managed `devilspie2` process.

The implementation must avoid killing unrelated `devilspie2` processes that the user may be running for other rules.

## Process ownership

The cleanest long-term model is that `d2wc` owns the `devilspie2` instance that runs the managed script.

That means:

1. The user starts `d2wc`.
2. `d2wc` starts or verifies its managed `devilspie2` instance.
3. The managed `devilspie2` instance runs the `d2wc` Lua script.
4. The configurator writes the managed Lua script.
5. `d2wc` reloads or restarts only its own managed `devilspie2` instance.

This avoids guessing which random `devilspie2` process belongs to `d2wc`.

## Window identity model

The configurator needs enough information to build safe rules.

For each selected window, it should try to collect:

1. Window title.
2. Window type.
3. Application class.
4. Class instance, if available.
5. Qubes domain from `_QUBES_VMNAME`, if available.
6. Workspace number.
7. Screen or monitor.
8. Current geometry.
9. Screen geometry.

On Qubes, `_QUBES_VMNAME` is the domain source.

On non-Qubes systems, this value may be unavailable. In that case, class-based rules and geometry capture should still work.

## Geometry model

The runtime should treat geometry as four integer values:

1. `x`
2. `y`
3. `w`
4. `h`

The configurator should show these values to the user, but it should not force ordinary users to type them manually.

The common path should be:

1. User places a window.
2. `d2wc` captures the geometry.
3. User names or confirms a geometry profile.
4. `d2wc` writes the `GEOM` profile.
5. User links the profile to a placement rule.

## Left-edge correction model

`LEFT_EDGE_CORRECTION` remains part of the runtime design for now.

The configurator should only expose it when relevant:

1. The target geometry has `x = 0`.
2. A test shows the actual window does not land at `x = 0`.
3. The user opens troubleshooting or advanced placement options.

The correction test should try:

1. Normal geometry placement.
2. `set_window_position(x, y)` after geometry.
3. `set_window_position2(x, y)` after geometry.

The working result can be saved as either `le:pos1` or `le:pos2`.

## Event suppression model

When `d2wc` applies a geometry rule, the window manager may emit movement or resize events.

The daemon/helper must not interpret those as user-initiated resizes.

The runtime should maintain a short suppression window after automated placement.

The exact duration needs testing. It should be configurable later.

## Failure handling

The UI should report failures clearly.

Important failure cases:

1. Lua file cannot be read.
2. Lua file cannot be parsed into managed blocks.
3. Validation fails.
4. Backup cannot be created.
5. New Lua file cannot be written.
6. Reload or restart fails.
7. Window identity cannot be captured.
8. The selected window is not a normal application window.

A save failure should leave the previous Lua file intact whenever possible.

## Logging

The runtime should support debug logging.

Logs should help diagnose:

1. Window identity capture.
2. Rule matching.
3. Geometry capture.
4. Resize detection.
5. Suppression behavior.
6. File write operations.
7. Reload or restart operations.

The log location should be configurable later. The initial implementation can log to standard output when run from a terminal.

## Open design questions

The following decisions still need testing or technology evaluation:

1. Best implementation language and GUI toolkit.
2. Best tray icon approach across desktops.
3. Best way to observe resize completion.
4. Best way to anchor a menu at the pointer.
5. Best way to reload or restart only the managed `devilspie2` instance.
6. Whether the Lua script should eventually be generated from a separate data file instead of edited directly.
7. Whether `LEFT_EDGE_CORRECTION` can be simplified by always applying one position function after geometry.

## Initial development sequence

The recommended implementation sequence is:

1. Keep the current Lua script working.
2. Build a parser/writer for the managed Lua blocks.
3. Build validation for generated rules.
4. Build a manual configurator window.
5. Add backup and save behavior.
6. Add a reload or restart path.
7. Add tray entry.
8. Add post-resize detection.
9. Add the pointer-anchored `Cancel` / `Configure` menu.
10. Add live geometry display while resizing.
