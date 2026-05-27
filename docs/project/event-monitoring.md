# d2wc Event Monitoring

## Purpose

This document describes the event-monitoring behavior needed for `d2wc`, especially for post-resize workflows.

The event-monitoring design is Phase 2 work. Phase 1 should first deliver a safe manual configurator that can be opened by command or keyboard shortcut. Once the configurator can safely read, validate, preview, back up, and write the managed Lua sections, event monitoring can make the same workflow feel automatic.

## Relationship to the Lua script

The current Lua script already reacts when `devilspie2` receives a normal application window event.

The script should continue to apply rules:

1. Ignore non-normal windows.
2. Resolve domain and class.
3. Apply exclusions.
4. Route windows to workspaces.
5. Pin windows.
6. Apply geometry profiles.
7. Apply left-edge correction when needed.

Event monitoring does not replace the Lua script. It adds a user-facing capture workflow around user actions such as resizing or moving a window.

## Phase 1 versus Phase 2

### Phase 1

Phase 1 does not require resize monitoring.

The user can:

1. Place or resize a window manually.
2. Open the configurator by command or keyboard shortcut.
3. Capture the active window.
4. Save a geometry profile or rule.

This avoids building fragile event logic before the configurator can safely save the result.

### Phase 2

Phase 2 adds automatic entry into the configurator after a user-initiated resize.

The daemon/helper should detect that a user resized a window, capture the final geometry, then either open the configurator directly or show the pointer-anchored `Cancel` / `Configure` menu.

## Event-monitoring goals

The event-monitoring layer should detect:

1. Window resize start.
2. Window resize completion.
3. The affected window identity.
4. The pre-resize geometry.
5. The post-resize geometry.
6. Whether the resize was user-initiated or caused by `d2wc` itself.

It should avoid:

1. Triggering on every tiny geometry change.
2. Triggering when `d2wc` applies a saved geometry rule.
3. Triggering for menus, tooltips, splash windows, panels, notifications, or other non-normal windows.
4. Opening the configurator repeatedly for the same resize operation.
5. Depending on a permanently visible tray icon.

## Candidate event sources

The exact event source needs testing on the target desktop.

Likely candidates:

1. `devilspie2` window events, where available.
2. X11 tools or libraries that can observe active window and geometry changes.
3. Window-manager signals or behavior exposed by the desktop environment.
4. A lightweight polling fallback for active-window geometry during a resize experiment.

The first target is Qubes OS with XFCE. Event monitoring should be proven there before broadening the design.

## User-initiated resize detection

A resize should be treated as user-initiated only when the daemon/helper has enough evidence.

The basic model:

1. Capture the active normal application window.
2. Record its current geometry.
3. Observe that the geometry is changing.
4. Wait until the geometry stops changing for a short quiet period.
5. Compare the final geometry to the original geometry.
6. If the change is larger than the threshold, treat it as a completed user resize.

This model can be implemented as a proof task before committing to a more advanced event source.

## Resize threshold

The threshold prevents noisy or accidental triggers.

A resize event should be ignored if the difference between pre-resize and post-resize geometry is too small.

The threshold may consider:

1. `x` delta.
2. `y` delta.
3. `w` delta.
4. `h` delta.

The first implementation can use a simple pixel threshold. Later versions can make this configurable.

Example starting policy:

```text
Treat a change as meaningful if any of x, y, w, or h changes by at least 8 pixels.
```

The exact value should be tested.

## Quiet period

A quiet period helps decide when resizing has ended.

Example model:

1. Geometry changes are observed.
2. The daemon/helper waits until geometry has not changed for a short interval.
3. The final geometry is captured.
4. The post-resize behavior runs.

A starting value could be a few hundred milliseconds, but it should be treated as a test value, not a final design decision.

## Suppression after automated placement

When the Lua script applies a geometry profile, the window manager may emit geometry-change events.

The daemon/helper must not interpret those events as a user resize.

The runtime should maintain a suppression list or suppression window after `d2wc` applies placement.

Suppression may track:

1. Window identifier.
2. Time of automated placement.
3. Expected geometry.
4. Suppression expiry time.

If a geometry event occurs inside the suppression window and matches the expected automated placement, it should be ignored.

## Window identity requirements

For post-resize handling, the daemon/helper needs the same identity data the configurator needs:

1. Window title.
2. Window type.
3. Application class.
4. Class instance, if available.
5. Qubes domain from `_QUBES_VMNAME`, if available.
6. Workspace number.
7. Screen or monitor.
8. Current geometry.
9. Screen geometry.

The identity capture should still work in a reduced form when `_QUBES_VMNAME` is not available.

## Active-window capture

The first event-monitoring proof should include a reliable way to capture the active window.

This is needed for both:

1. Manual command/keyboard-shortcut entry.
2. Post-resize automation.

Manual entry can be simpler. When the user presses the shortcut, `d2wc` captures the active window at that moment and opens the configurator.

Post-resize entry is more complex because the active window may change, focus may move, or a menu may appear after the resize.

## Post-resize behavior setting

The user should be able to choose one of three post-resize behaviors:

1. Disabled.
2. Open configurator directly.
3. Show pointer-anchored `Cancel` / `Configure` menu.

Default recommendation for early testing:

1. Disabled by default.
2. User explicitly enables direct configure or pointer menu.

This avoids surprising the user while event detection is still being proven.

## Direct configure behavior

When enabled, direct configure should work like this:

1. User resizes a normal application window.
2. `d2wc` detects resize completion.
3. `d2wc` captures the final geometry.
4. `d2wc` opens the configurator for that window.
5. The configurator suggests saving the captured geometry.

Direct configure is the fastest path, but it may be intrusive if triggered too often.

## Pointer-anchored menu behavior

When enabled, the pointer menu should work like this:

1. User resizes a normal application window.
2. `d2wc` detects resize completion.
3. `d2wc` captures the final geometry.
4. `d2wc` shows a small menu fixed to the pointer.
5. The pointer is centered on `Cancel`.
6. User chooses `Cancel` or `Configure`.
7. If `Configure` is chosen, the configurator opens with the captured window preloaded.

The menu must not save any rule. It only decides whether to open the configurator.

## Mouse-button swapping

Some users swap their mouse buttons.

The event-monitoring design should avoid hard-coding assumptions such as:

1. Left button means primary action.
2. Right button means secondary action.

Where possible, use toolkit or desktop abstractions for primary and secondary actions.

If the underlying APIs expose only physical button numbers, `d2wc` should make the behavior configurable and document the limitation.

## Pointer anchoring

The pointer-anchored menu should be tested separately from resize detection.

Proof tasks:

1. Display a two-action menu at the current pointer location.
2. Center the pointer on `Cancel`.
3. Confirm that `Cancel` can be selected without moving the pointer.
4. Confirm that `Configure` requires deliberate selection.
5. Confirm behavior with swapped mouse buttons.
6. Confirm behavior on Qubes/XFCE.

The menu may be toolkit-specific. GTK should be tested first because it is the first UI proof target. Qt should remain on the roadmap for KDE-oriented users.

## Toolkit impact

The core event-monitoring logic should not be tied directly to GTK or Qt widgets.

Recommended split:

1. A core event-monitoring module that detects windows and geometry changes.
2. A UI-specific adapter that displays the configurator or pointer menu.
3. Shared data structures for captured window identity and geometry.

This split supports the current roadmap:

1. GTK/PyGObject first for Qubes/XFCE.
2. Qt later for KDE-oriented users.
3. Shared parser/writer/validator logic across both.

## Live geometry updates

Live geometry display is a later feature.

The idea is that while the user resizes a window, the configurator or a small overlay could show:

```text
{ x = 0, y = 0, w = 1920, h = 2115 }
```

This is not required for Phase 2. It should follow after basic resize completion detection works reliably.

## Failure cases

The event-monitoring layer should handle these cases without breaking normal window management:

1. No active window found.
2. Active window is not a normal application window.
3. Window disappears during resize.
4. Window identity changes or cannot be read.
5. Geometry cannot be read.
6. User changes focus before the quiet period completes.
7. `d2wc` cannot show the pointer menu.
8. `d2wc` cannot open the configurator.
9. Resize event is ambiguous.

When uncertain, `d2wc` should do nothing rather than open the configurator incorrectly.

## Debug logging

Event monitoring should be easy to debug.

Useful debug fields:

1. Window identifier.
2. Window title.
3. Domain.
4. Class.
5. Pre-resize geometry.
6. Post-resize geometry.
7. Delta values.
8. Whether threshold passed.
9. Whether suppression was active.
10. Which post-resize behavior was selected.
11. Whether the configurator or pointer menu opened.

## Initial proof sequence

The recommended proof sequence is:

1. Capture active window identity from a command.
2. Capture active window geometry from a command.
3. Open the configurator from a keyboard shortcut.
4. Monitor geometry changes for the active window in a test harness.
5. Detect resize completion using a quiet period.
6. Apply a resize threshold.
7. Log the final captured geometry without opening the configurator.
8. Open the configurator after resize completion.
9. Add the pointer-anchored `Cancel` / `Configure` menu.
10. Add suppression for automated placements.

## Open questions

The following items need testing:

1. Best X11 event source for Qubes/XFCE.
2. Whether `devilspie2` alone exposes enough event detail for resize completion.
3. Whether active-window polling is good enough as an interim implementation.
4. Best way to identify the same window across events.
5. Best suppression duration after automated placement.
6. Best resize threshold.
7. Best pointer-menu implementation in GTK.
8. Equivalent pointer-menu strategy for a future Qt/KDE front end.
