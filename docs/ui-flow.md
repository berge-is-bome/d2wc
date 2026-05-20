# d2wc UI Flow

## Purpose

This document describes how the `d2wc` configurator should behave from the user's point of view.

The goal is to make window routing and placement feel like a guided desktop action instead of Lua editing. The Lua script remains the execution layer, but the configurator should become the normal way users capture, review, and save rules.

## UI design goals

The configurator should be small, practical, and predictable.

It should:

1. Show the selected window's identity clearly.
2. Show the selected window's current workspace and geometry.
3. Suggest the likely configuration action.
4. Preview the exact rule before saving.
5. Warn before overwriting or conflicting with existing rules.
6. Back up the managed Lua file before writing.
7. Avoid requiring the user to know Lua syntax.
8. Still allow advanced users to inspect and manually edit generated values.

It should not:

1. Become a large desktop environment control panel.
2. Rewrite unrelated Lua program logic.
3. Apply hidden permanent changes without a visible save action.
4. Assume that mouse buttons use a right-handed layout.
5. Require a permanently visible tray icon for normal background operation.

## Main user objects

The UI should expose these concepts in user language.

1. Window: the currently selected application window.
2. Domain: the Qubes domain when available, or a future non-Qubes grouping value.
3. Class: the application class used for matching.
4. Workspace route: the workspace where matching windows should open.
5. Geometry profile: a saved `{ x, y, w, h }` size and position.
6. Placement rule: a link between a window match and a geometry profile.
7. Pin rule: a rule that keeps matching windows visible on all workspaces.
8. Exclude rule: a rule that tells `d2wc` not to manage matching windows.
9. Left-edge correction: a compatibility setting for windows that should land at `x = 0` but do not.
10. Window border width: a configurable pixel value used when generating matching left/right split profiles.

## Entry point 1: command or keyboard shortcut

The stable manual entry point should be a command that opens the configurator.

This command can be assigned to a desktop keyboard shortcut by the user. That is likely the cleanest day-to-day workflow after the workspace has mostly been configured, because `d2wc` can keep running in the background without needing a permanently visible tray icon.

Example user flow:

1. User places or selects a window.
2. User presses their configured shortcut.
3. The configurator opens for the active window.
4. User captures geometry, creates a route, creates a placement rule, pins the window, or excludes it.
5. User saves or cancels.

The exact command name is not settled yet. Possible names:

1. `d2wc configure`
2. `d2wc-configure`
3. `d2wc --configure`

The command should also be usable from a terminal for debugging.

## Entry point 2: optional tray menu

A tray icon can still be useful during initial setup or troubleshooting, but it should not be required for normal operation.

The tray mode should be optional.

When enabled, the tray menu can include:

1. `Configure`
2. `Capture Active Window`
3. `Pause d2wc`
4. `Reload Rules`
5. `Open Lua Config`
6. `About`
7. `Quit`

### `Configure`

When the user chooses `Configure`, the configurator opens.

If there is an active normal application window, the configurator should load that window as the current target.

If there is no suitable active window, the configurator should open in a neutral state and offer:

1. Select active window.
2. Capture next clicked window.
3. Open existing rules.
4. Open settings.

### `Capture Active Window`

This action should immediately gather the active window's domain, class, title, workspace, screen, and geometry. It should then open the configurator with those values preloaded.

This is the fastest manual path for a user who has already placed a window where they want it.

## Entry point 3: direct post-resize configure

In this mode, `d2wc` opens the configurator directly after the user finishes resizing a window.

### Flow

1. The user starts resizing a normal application window.
2. `d2wc` records the original geometry.
3. The user releases the primary mouse button.
4. `d2wc` reads the final geometry.
5. If the geometry changed enough to count as a real resize, `d2wc` opens the configurator for that window.
6. The configurator shows the captured geometry and suggested save actions.

### Resize threshold

The daemon/helper should ignore tiny accidental changes.

A resize should count only when at least one meaningful value changed:

1. `w`
2. `h`
3. `x`
4. `y`

The exact threshold should be configurable later. The initial implementation can use a small pixel threshold to avoid noisy triggers.

### Avoiding automation loops

The direct post-resize flow must not trigger when `d2wc` itself moves or resizes a window.

The daemon/helper needs a short suppression window after applying rules so it can distinguish user-initiated resizing from automated placement.

## Entry point 4: post-resize choice menu

In this mode, `d2wc` does not open the full configurator immediately. It first shows a small menu fixed to the mouse pointer.

### Menu layout

The menu has two actions:

1. `Cancel`
2. `Configure`

The pointer should be centered on `Cancel` when the menu appears. This makes the safest action the easiest action.

`Configure` should be the second action. A deliberate movement or selection should be required before opening the configurator.

### Mouse button handling

The implementation must not assume that left click means primary action or that right click means secondary action.

The UI should use primary and secondary pointer actions internally where possible. If a toolkit exposes only physical button numbers, `d2wc` should make the behavior configurable and document the limitation.

### Menu dismissal

The menu should close without saving when:

1. The user selects `Cancel`.
2. The user presses Escape.
3. The user clicks outside the menu.
4. The menu times out, if a timeout setting is later added.

No rule should be written from this menu. The menu only decides whether to open the configurator.

## Main configurator window

The main configurator window should be organized around one selected target window.

### Header area

The header should show:

1. Window title.
2. Domain, if available.
3. Class.
4. Current workspace.
5. Current screen or monitor.
6. Current geometry as `{ x, y, w, h }`.

For non-Qubes systems, the domain field may be empty or replaced by a future grouping concept. The UI should not make Qubes-specific fields mandatory for non-Qubes use.

### Suggested actions area

The configurator should show the most likely actions first:

1. Save current geometry as a profile.
2. Route this window to the current workspace.
3. Apply an existing geometry profile.
4. Pin this window.
5. Exclude this window.
6. Test left-edge correction, when relevant.

The UI should favor the most specific safe rule first: domain/class where domain is available, then class-wide or domain-wide rules as deliberate alternatives.

### Rule preview area

Before saving, the configurator should show the exact rule that will be written.

Examples:

```lua
"d:personal c:okular g:half_left"
```

```lua
[2] = { "d:work c:krusader", }
```

```lua
"d:dom0 c:qubes-qube-manager le:pos1"
```

The preview should also show the target section:

1. `EXCLUDE`
2. `PIN`
3. `WORKSPACE_ROUTES`
4. `GEOM`
5. `WORKSPACE_PLACEMENT`
6. `LEFT_EDGE_CORRECTION`

### Existing matching rules area

The configurator should list existing rules that already affect the selected window.

It should show:

1. Exact domain/class matches.
2. Domain-wide matches.
3. Class-wide matches.
4. The winning rule after precedence is applied.
5. Rules that are valid but shadowed by a more specific rule.
6. Rules that appear invalid or reference missing geometry profiles.

This is important because the user needs to know whether a new rule will change behavior or be ignored by a more specific existing rule.

### Save controls

The save area should include:

1. `Preview Changes`
2. `Save`
3. `Test Without Saving`
4. `Cancel`

`Preview Changes` should show a small diff-like view of what will change in the managed Lua sections.

`Save` should write the updated config only after validation passes.

`Test Without Saving` should apply the candidate geometry to the current window, but it must not write a permanent rule.

## Flow: save current geometry as a profile

This is the core capture workflow.

### User story

The user resizes or moves a window until it is exactly where they want it, then saves that geometry as a named reusable profile.

### Flow

1. User opens the configurator for the selected window.
2. Configurator shows current geometry.
3. User chooses `Save current geometry as profile`.
4. Configurator suggests a profile name.
5. User confirms or edits the profile name.
6. Configurator previews the new or updated `GEOM` entry.
7. User saves.

### Profile name suggestions

The configurator may suggest names based on:

1. Application class.
2. Domain and class.
3. Screen position, such as `half_left`, `half_right`, or `centered_mid`.
4. Existing naming patterns in the Lua file.

Generated names must be editable before saving.

### Existing profile handling

If the profile name already exists, the configurator should ask whether to:

1. Update the existing profile.
2. Create a new profile with a different name.
3. Cancel.

Before updating a profile, the configurator should show which placement rules currently use it.

## Flow: apply geometry profile to a window

### User story

The user wants matching windows to open at a saved size and position.

### Flow

1. User opens the configurator for a selected window.
2. User chooses `Apply geometry profile`.
3. Configurator lists existing geometry profiles.
4. User selects a profile.
5. Configurator asks the match scope:
   1. This domain and class.
   2. This class everywhere.
   3. This domain generally.
6. Configurator previews the `WORKSPACE_PLACEMENT` rule.
7. User saves.

### Default scope

When a domain is available, the default should be the exact domain/class scope.

When no domain is available, the default should be class-wide.

## Flow: route window to workspace

### User story

The user wants matching windows to open on a specific workspace.

### Flow

1. User opens the configurator for the selected window.
2. Configurator shows the current workspace.
3. User chooses `Route to this workspace` or selects another workspace.
4. Configurator asks the match scope:
   1. This domain and class.
   2. This class everywhere.
   3. This domain generally.
5. Configurator previews the `WORKSPACE_ROUTES` change.
6. User saves.

### Duplicate workspace key protection

The configurator must prevent duplicate Lua table keys such as two separate `[1]` entries.

When adding a route to an existing workspace, it should append to that workspace's existing list rather than creating another list with the same key.

## Flow: pin a window

### User story

The user wants matching windows to appear on all workspaces.

### Flow

1. User opens the configurator for the selected window.
2. User chooses `Pin`.
3. Configurator asks the match scope:
   1. This domain and class.
   2. This class everywhere.
   3. This domain generally.
4. Configurator previews the `PIN` rule.
5. User saves.

### UI note

The UI should explain that pinning is applied after workspace routing because workspace assignment can clear the sticky state.

## Flow: exclude a window

### User story

The user wants `d2wc` to stop managing a window or class of windows.

### Flow

1. User opens the configurator for the selected window.
2. User chooses `Exclude`.
3. Configurator asks the match scope:
   1. This domain and class.
   2. This class everywhere.
   3. This domain generally.
4. Configurator previews the `EXCLUDE` rule.
5. User saves.

### Safety warning

The UI should explain that excluded windows will not be routed, pinned, resized, or corrected by `d2wc`.

This warning matters because `EXCLUDE` short-circuits later behavior.

## Flow: automated half-left and half-right

### User story

The user wants common split-screen profiles without manually typing pixel values.

### Flow

1. User opens settings or the configurator for a selected window.
2. User chooses `Generate half-left and half-right profiles`.
3. Configurator detects the current screen geometry.
4. Configurator reads the current `window_border_width` setting.
5. Configurator calculates left and right profiles that account for the configured border width.
6. Configurator previews the resulting `GEOM` entries.
7. User saves.

### Generated profile behavior

The first implementation can generate standard profiles:

1. `half_left`
2. `half_right`

When `half_left` and `half_right` are intended to sit beside each other and the two windows are the same size, `d2wc` should provide a `window_border_width` setting. The user should be able to enter the border width in pixels instead of manually nudging window widths until the two windows meet correctly.

The setting should be used when generating the width and position values for the split profiles. If the configured border width is too small or too large, the user can adjust one value and regenerate or preview both profiles.

Possible user-facing field names:

1. `window_border_width`
2. `Window border width`
3. `Border width in pixels`

The underlying setting should use a clear, consistent name. `window_border_width` is the preferred internal name.

Later versions may support monitor-specific names:

1. `monitor1_half_left`
2. `monitor1_half_right`
3. `monitor2_half_left`
4. `monitor2_half_right`

### Border width preview

The configurator should preview how `window_border_width` changes the generated split profiles.

The preview should show:

1. Screen or monitor geometry.
2. Current `window_border_width`.
3. Generated `half_left` geometry.
4. Generated `half_right` geometry.
5. Combined expected coverage.

The user should be able to change `window_border_width`, preview again, and save only after the generated values look correct.

### Open design question

The exact handling of panels, usable work area, window decorations, and border width still needs testing.

The UI should therefore present generated values as editable before saving.

## Flow: left-edge correction test

### User story

A window that should be placed at `x = 0` lands a few pixels away from the left edge.

### Flow

1. Configurator detects that the selected geometry profile has `x = 0`.
2. User chooses `Test left-edge correction`.
3. Configurator applies the geometry normally.
4. Configurator reads the resulting window geometry.
5. If the actual `x` is not `0`, the configurator offers correction tests.
6. User tests `pos1`.
7. User tests `pos2` if needed.
8. User saves the working correction mode to `LEFT_EDGE_CORRECTION`.

### Default behavior

The configurator should not force the user to think about left-edge correction unless the selected profile or test result makes it relevant.

## Flow: reload rules

After saving changes, `d2wc` needs to make the updated Lua rules active.

The first implementation should be conservative:

1. Save a backup copy of the previous Lua file.
2. Write the updated Lua file.
3. Validate the managed sections where possible.
4. Ask `devilspie2` or the launcher wrapper to reload or restart cleanly.
5. Show success or failure to the user.

The exact reload mechanism belongs in [Runtime Architecture](runtime-architecture.md).

## Conflict and validation behavior

Before saving, the configurator should check for:

1. Duplicate rules.
2. Duplicate workspace table keys.
3. Unknown geometry profiles.
4. Invalid tokens.
5. Duplicate prefixes inside one rule.
6. Placement rules without `g:`.
7. Left-edge correction rules without `le:`.
8. Rules with neither `d:` nor `c:` where at least one is required.

Validation should produce user-facing messages that explain what to fix without exposing unnecessary implementation detail.

## Settings screen

A small settings screen should eventually include:

1. Lua config path.
2. Backup location.
3. Manual configurator command.
4. Window border width in pixels for generated split profiles.
5. Optional tray icon:
   1. Disabled.
   2. Enabled during setup.
   3. Always enabled.
6. Post-resize behavior:
   1. Disabled.
   2. Open configurator directly.
   3. Show `Cancel` / `Configure` menu.
7. Resize threshold.
8. Suppression delay after automated placement.
9. Mouse action behavior, if the toolkit cannot reliably respect swapped buttons.
10. Debug logging.

## MVP UI scope

The first usable version should include:

1. Command-line/manual launch path for the configurator, suitable for assigning to a desktop keyboard shortcut.
2. Main configurator window for the active window.
3. Current window summary.
4. Geometry capture into `GEOM`.
5. Workspace route creation.
6. Placement rule creation.
7. Rule preview before save.
8. Backup before save.
9. Optional tray icon if the chosen toolkit makes it reliable without driving the architecture.

Post-resize automation, pointer-anchored menus, live geometry updates, and generated split-profile border tuning can follow after the basic configurator can safely read and write the Lua file.

## Development notes

The UI should be developed against the current Lua script, but the code should avoid depending on Qubes-only data being present.

When `_QUBES_VMNAME` is missing, the configurator should still support class-based matching and geometry capture.

When `_QUBES_VMNAME` is present and empty, the UI should display the domain as `dom0`, matching the current Lua script behavior.
