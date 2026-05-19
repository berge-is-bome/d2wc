# d2wc MVP Scope

## Purpose

This document separates the first usable implementation from the next usability milestone.

The post-resize behavior and pointer-anchored `Cancel` / `Configure` menu are part of the intended product. They should not be lost or treated as optional nice-to-have behavior. They are central to the long-term workflow.

They should, however, be implemented after the configurator can safely read, validate, preview, back up, and write the managed Lua configuration sections. Otherwise the post-resize trigger would open a configurator that cannot yet reliably save the user's choice.

## MVP Phase 1: safe manual configurator

Phase 1 should prove that `d2wc` can safely manage the current Lua script.

Required Phase 1 behavior:

1. Tray icon with `Configure`, `Reload Rules`, and `Quit`.
2. Main configurator window for the active window.
3. Current window summary:
   1. Window title.
   2. Domain, if available.
   3. Class.
   4. Current workspace.
   5. Current geometry.
4. Geometry capture into `GEOM`.
5. Workspace route creation into `WORKSPACE_ROUTES`.
6. Placement rule creation into `WORKSPACE_PLACEMENT`.
7. Rule preview before save.
8. Validation before save.
9. Backup before save.
10. Clean reload or restart path for the active `devilspie2` rules.

This phase gives the user a working configuration tool even before automatic resize-triggered entry is implemented.

## MVP Phase 2: post-resize configurator entry

Phase 2 should add the behavior that makes `d2wc` feel automated and desktop-native.

Required Phase 2 behavior:

1. Detect user-initiated window resize completion.
2. Ignore resize events caused by `d2wc` itself.
3. Record pre-resize and post-resize geometry.
4. Ignore tiny accidental geometry changes using a threshold.
5. Support post-resize behavior settings:
   1. Disabled.
   2. Open configurator directly.
   3. Show pointer-anchored `Cancel` / `Configure` menu.
6. Open the configurator with the resized window preloaded.
7. Show the captured post-resize geometry as the suggested geometry to save.

## Pointer-anchored `Cancel` / `Configure` menu

The pointer-anchored menu belongs in Phase 2.

It should appear after a resize completes when that behavior is selected in settings.

The menu should contain only:

1. `Cancel`
2. `Configure`

The pointer should be centered on `Cancel` when the menu opens. This makes cancellation the safest and easiest action.

No rule should be written from this menu. It only decides whether to open the configurator.

## Why this is not Phase 1

The post-resize behavior requires reliable event monitoring, resize detection, suppression of automation loops, and pointer/menu behavior that may differ by desktop environment or toolkit.

Those are important features, but they depend on the configurator already being able to save correct Lua changes safely.

The safest order is therefore:

1. Build the safe manual configurator.
2. Add post-resize detection.
3. Add the pointer-anchored menu.
4. Add live geometry updates while resizing.

## Later behavior

After Phase 2, later versions can add:

1. Live `{ x, y, w, h }` updates while the user resizes.
2. More advanced monitor-aware half-left and half-right generation.
3. Per-desktop-environment event-monitoring refinements.
4. More detailed conflict explanation in the UI.
