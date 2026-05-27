# d2wc Left-Edge Correction Testing

## Purpose

This document defines a repeatable test plan for `LEFT_EDGE_CORRECTION`.

The current Lua script uses `set_window_geometry(x, y, w, h)` to place and size windows. On some systems, a window intended to land at `x = 0` may end up a few pixels away from the left edge. The script therefore supports optional correction modes using `set_window_position(x, y)` or `set_window_position2(x, y)` after geometry is applied.

The goal of this test plan is to decide whether the correction logic should remain as-is, be simplified, or be hidden behind configurator-driven testing.

## Confirmed observation

Manual testing has shown that when a window intended to land at `x = 0` ends up a few pixels away from the left edge, the incorrect position is visible through `get_window_geometry()`.

That means `d2wc` does not need to rely only on visual inspection. It can apply geometry, read the actual resulting geometry, detect that the actual `x` differs from the requested `x`, and then apply an optional correction mode.

This makes left-edge correction a testable runtime behavior:

1. Request geometry with `x = 0`.
2. Apply `set_window_geometry(x, y, w, h)`.
3. Read actual geometry with `get_window_geometry()`.
4. If actual `x != requested x`, try `set_window_position(x, y)` or `set_window_position2(x, y)`.
5. Read actual geometry again.
6. Save the correction mode only if the final geometry is correct.

## Current behavior

The current model is:

1. Resolve a matching `WORKSPACE_PLACEMENT` rule.
2. Resolve that rule to a named `GEOM` profile.
3. Apply the profile with `set_window_geometry(g.x, g.y, g.w, g.h)`.
4. If `g.x == 0`, check for a matching `LEFT_EDGE_CORRECTION` rule.
5. If the correction mode is `le:pos1`, call `set_window_position(g.x, g.y)`.
6. If the correction mode is `le:pos2`, call `set_window_position2(g.x, g.y)`.

Current correction modes:

1. `le:pos1`
2. `le:pos2`

## Test objective

The test should answer these questions:

1. Does `set_window_geometry()` place each tested window exactly at `x = 0`?
2. Can `get_window_geometry()` reliably detect the offset when placement is wrong?
3. If normal placement is wrong, does `set_window_position()` correct it?
4. If not, does `set_window_position2()` correct it?
5. Do either correction functions change the final width or height unexpectedly?
6. Does behavior differ by application class?
7. Does behavior differ by Qubes domain?
8. Does behavior differ on non-Qubes Linux desktops?
9. Does behavior differ by desktop environment or window manager?
10. Does behavior differ by monitor layout or panel placement?
11. Can the configurator safely detect and save the working correction mode?

## Test environments

Start with the known target environment:

1. Qubes OS.
2. XFCE.
3. The user's normal monitor layout.
4. Current `devilspie2` package from the distribution.

Later test environments:

1. Fedora with XFCE.
2. Fedora with KDE Plasma.
3. Debian-family system with XFCE.
4. Non-Qubes Linux desktop where `devilspie2` works.
5. Multi-monitor layout.
6. Single-monitor layout.
7. Panel on top, bottom, left, or right where relevant.

## Test windows

Use a mix of applications because window managers may treat them differently.

Suggested first set:

1. Terminal window.
2. File manager.
3. Browser.
4. PDF viewer.
5. Text editor.
6. Qubes Manager or a Qubes dom0 tool where relevant.
7. A problematic window that previously needed correction.

Each test should record:

1. Application name.
2. Class.
3. Domain, if available.
4. Window title.
5. Workspace.
6. Screen or monitor.
7. Requested geometry.
8. Actual geometry after placement.
9. Correction mode used.
10. Final geometry after correction.

## Test geometry profiles

The most important profiles are the ones with `x = 0`.

Minimum test profiles:

```lua
left_full = { x = 0, y = 0, w = 1200, h = 900 }
```

```lua
half_left = { x = 0, y = 0, w = 1920, h = 1080 }
```

```lua
left_offset_y = { x = 0, y = 100, w = 1200, h = 900 }
```

A control profile should also be tested:

```lua
not_left_edge = { x = 100, y = 100, w = 1200, h = 900 }
```

The control profile confirms that correction is not being applied when `x` is not zero.

## Manual test procedure

For each test window and geometry profile:

1. Start with no `LEFT_EDGE_CORRECTION` rule for the target.
2. Apply the geometry using the Lua script.
3. Record the actual geometry using `get_window_geometry()` or the configurator's capture function.
4. Compare requested `x` to actual `x`.
5. If actual `x == 0`, mark the test as no correction needed.
6. If actual `x != 0`, test `le:pos1`.
7. Record actual geometry after `set_window_position(x, y)`.
8. If `le:pos1` does not correct the issue, test `le:pos2`.
9. Record actual geometry after `set_window_position2(x, y)`.
10. Mark the best correction mode.

## Automatic detection model

Because `get_window_geometry()` can reveal the post-placement offset, `d2wc` can eventually perform a placement verification step.

Recommended model:

1. Apply `set_window_geometry(g.x, g.y, g.w, g.h)`.
2. Wait briefly for the window manager to settle.
3. Read actual geometry with `get_window_geometry()`.
4. Compare requested `x` and `y` to actual `x` and `y`.
5. If actual position matches requested position, do nothing else.
6. If actual position does not match and the target is eligible for correction, apply the configured correction mode.
7. Read actual geometry again.
8. Log whether the correction worked.

For Phase 1, this can be exposed as a configurator test action. For later versions, it may become part of normal runtime behavior.

## Automated test harness idea

A later helper script can automate most of the test.

Possible flow:

1. Launch or select a test window.
2. Apply a test geometry.
3. Wait briefly for the window manager to settle.
4. Read actual geometry.
5. Apply `pos1` correction.
6. Read actual geometry.
7. Reset and apply test geometry again.
8. Apply `pos2` correction.
9. Read actual geometry.
10. Print a summary.

The script should not permanently modify the user's normal Lua rules. It should run against a temporary test copy or a dedicated test section.

## Pass and fail criteria

### No correction needed

Pass condition:

```text
requested x = 0
actual x = 0
```

No `LEFT_EDGE_CORRECTION` rule should be generated.

### Correction mode works

Pass condition:

```text
requested x = 0
actual x after normal geometry != 0
actual x after correction = 0
```

The configurator may offer to save the working correction mode.

### Correction mode unsafe

Fail condition:

```text
actual x is corrected, but width, height, or y changes unexpectedly
```

The configurator should not save that correction automatically.

### No correction works

Fail condition:

```text
normal placement fails
pos1 fails
pos2 fails
```

The configurator should report that no tested correction mode worked for that window.

## Configurator behavior

The configurator should expose left-edge correction only when relevant.

Relevant cases:

1. The selected geometry profile has `x = 0`.
2. The user runs a left-edge placement test.
3. `get_window_geometry()` shows that the actual window lands away from the requested `x`.
4. The user opens advanced or troubleshooting options.

Normal users should not need to understand this feature during ordinary setup.

Recommended UI behavior:

1. Show `Test left-edge placement` only for profiles where `x = 0`.
2. Run normal placement first.
3. Read actual geometry with `get_window_geometry()`.
4. If normal placement is correct, report that no correction is needed.
5. If normal placement is incorrect, offer `Try correction mode 1` and `Try correction mode 2`.
6. Read actual geometry after each correction attempt.
7. Preview the resulting `LEFT_EDGE_CORRECTION` rule before saving.
8. Save only the mode that actually worked.

## Rule generation

If a correction mode is saved, the generated rule should follow the same prefixed grammar as the Lua script.

Examples:

```lua
"d:dom0 c:qubes-qube-manager le:pos1"
```

```lua
"d:personal c:okular le:pos2"
```

Default scope should match the placement rule scope where practical.

If the placement rule is domain/class-specific, the correction rule should normally be domain/class-specific too.

## Simplification research

The original question is whether `LEFT_EDGE_CORRECTION` can be avoided or simplified.

Possible outcomes:

1. Keep the current model unchanged.
2. Always call `set_window_position(x, y)` after `set_window_geometry()` when `x = 0`.
3. Always call `set_window_position2(x, y)` after `set_window_geometry()` when `x = 0`.
4. Use one correction function globally if it works everywhere tested.
5. Keep per-target correction because behavior differs by application, domain, desktop, or window manager.
6. Hide the setting in the UI but keep it in the Lua configuration for compatibility.
7. Let `d2wc` detect the offset with `get_window_geometry()` and apply a saved correction mode only when the offset is actually present.

The safe default is to keep per-target correction until testing proves a simpler rule is reliable.

## Multi-monitor considerations

Left-edge correction must be tested carefully on multi-monitor layouts.

A monitor can have an `x` origin that is not zero. For example, a monitor to the right of the primary monitor may start at a positive `x`, while a monitor to the left may start at a negative `x`.

The correction feature should mean left edge of the target monitor or requested geometry, not always global desktop `x = 0`.

Open question:

1. Should the correction trigger only when `g.x == 0`, or should it trigger when the requested `x` equals the selected monitor's left edge?

The first implementation can keep the current `g.x == 0` behavior. Multi-monitor improvement can follow after monitor-aware geometry generation is designed.

## Logging

Test logs should include:

1. Date and time.
2. Desktop environment.
3. Window manager.
4. Qubes or non-Qubes environment.
5. Application class.
6. Domain, if available.
7. Requested geometry.
8. Actual geometry after normal placement.
9. Actual geometry after `pos1`.
10. Actual geometry after `pos2`.
11. Delta between requested and actual position.
12. Final recommendation.

## Development sequence

Recommended sequence:

1. Preserve current `LEFT_EDGE_CORRECTION` behavior.
2. Add manual configurator support for viewing existing correction rules.
3. Add a test action for profiles with `x = 0`.
4. Use `get_window_geometry()` to detect whether normal placement landed correctly.
5. Add logging for normal, `pos1`, and `pos2` placement results.
6. Save the working mode only after user confirmation.
7. Revisit simplification after multiple test environments are recorded.

## Open questions

1. Which windows currently need correction on Qubes/XFCE?
2. Does one correction function work consistently across all tested windows?
3. Does either correction function cause size changes?
4. Does correction need to be per-domain, per-class, or both?
5. How should monitor-aware left edges be represented?
6. Should the Lua script eventually attempt correction automatically and log the result?
7. Should the configurator maintain a separate test-results file for troubleshooting?
8. Should correction be attempted only when `get_window_geometry()` proves that normal placement failed?
