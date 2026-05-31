# d2wc Design History Notes

## Purpose

Design context recovered from the archived pre-repository `d2wc.lua` history and the current `src/d2wc.lua` script is recorded here.

The purpose is not to preserve every intermediate implementation detail. The purpose is to keep the reasoning behind the current Lua configuration model available in the repository, so future work does not depend on finding an old ChatGPT conversation or reconstructing intent from memory.

The original practical target for `d2wc` is Qubes OS with XFCE and `devilspie2`. Broader non-Qubes support remains a later goal. Any notes about non-Qubes behavior in this document should therefore be treated as future design context, not as a current implementation target.

## Source of these notes

These notes were prepared after preserving pre-repository `d2wc.lua` versions in Git history.

The archived sequence starts at the oldest preserved script and progresses through the version that matches the repository baseline. It can be inspected with:

```bash
git log --oneline --reverse archive/d2wc-lua-pre-repo-history -- src/d2wc.lua
```

The repository also contains the active script at:

```text
src/d2wc.lua
```

The important historical versions are:

1. `0.1.4`
2. `0.1.5`
3. `0.1.6`
4. `0.1.7`
5. `0.1.8`
6. `0.1.9`
7. `0.1.10`
8. `0.1.11.2` through `0.1.11.7`
9. `0.1.12.1`
10. `0.1.12.2`
11. repository baseline `0.1.12.3`

The commit labels and script header versions are not perfectly identical in every preserved step. For example, one archived commit label mentions `0.1.11.1` while the script header moved to `0.1.11.2`. Treat the script headers and diffs as the more useful technical record.

## Current architectural direction

The current design is:

1. Keep `devilspie2` as the runtime engine.
2. Keep `src/d2wc.lua` as the active execution layer.
3. Let Python tooling parse, validate, render, and safely edit known managed Lua sections.
4. Keep user-editable Lua data separate from program logic as far as practical.
5. Avoid asking the user to hand-edit Lua for ordinary configuration tasks.
6. Keep writes guarded, previewed, validated, and backed up.

The current managed Lua sections are:

1. `EXCLUDE`
2. `PIN`
3. `WORKSPACE_ROUTES`
4. `GEOM`
5. `WORKSPACE_PLACEMENT`
6. `LEFT_EDGE_CORRECTION`

## Why `EXCLUDE` exists

`EXCLUDE` was introduced early after real desktop testing showed that not every normal-looking window should be touched by automation.

The original motivating example was `qubes-app-menu`. If a window should not be routed, resized, pinned, or corrected, exclusion is the safest answer. The script should behave as if `d2wc` is not managing that window.

Design intent:

1. Exclusion is a hard stop.
2. Exclusion should happen before routing, pinning, geometry placement, and correction.
3. Exclusion is appropriate for app menus, panels, transient helpers, splash-like windows, or application windows that behave badly when managed.

Current implementation note:

The active Lua script applies exclusion after it has detected a domain and class. In the Qubes target scenario, an empty `_QUBES_VMNAME` means `dom0`, so dom0 windows are still handled through the normal domain path. If `_QUBES_VMNAME` is nil or unavailable, broader non-Qubes behavior should be revisited later.

## Why `PIN` is applied after workspace routing

Pinning makes a window sticky, which means visible on all workspaces.

Historical testing showed that workspace assignment clears the sticky flag. Therefore, the script must route the window first and then pin it.

Design rule:

```text
workspace routing before pinning
```

Do not reorder this casually. If pinning happens before `set_window_workspace()`, the window may stop being sticky after the workspace move.

## Why `WORKSPACE_ROUTES` exists

The oldest preserved versions used a hard-coded domain to workspace map. That was useful for a personal script but not suitable for a configurator.

`WORKSPACE_ROUTES` replaced the hard-coded map with user-managed route rules.

The section exists to answer this user-facing question:

```text
When this kind of window opens, which workspace should it go to?
```

Important constraints:

1. Lua table keys are unique.
2. If a workspace key is repeated, Lua keeps the later value and effectively overwrites the earlier one.
3. The configurator must therefore append to the existing workspace row instead of creating another row with the same workspace key.
4. Route rows should stay ordered by workspace number for readability.
5. Broader and narrower routes may coexist, for example `d:personal` and `d:personal c:navigator`.

## Why `GEOM` exists as a separate section

The oldest preserved rule model allowed geometry to be specified directly inside class rules, either by profile name or by an inline table such as `{ x = ..., y = ..., w = ..., h = ... }`.

The current model deliberately keeps geometry values in named `GEOM` profiles and links windows to those profiles through `WORKSPACE_PLACEMENT`.

Design intent:

1. Geometry values should have names.
2. Placement rules should refer to names, not duplicate geometry numbers.
3. The configurator can safely add, modify, delete, and validate profiles as first-class objects.
4. Deleting a profile must be rejected when a placement rule still references it.

Legacy inline geometry tables are historical only and are not part of the current managed grammar.

## Why `WORKSPACE_PLACEMENT` replaced older geometry rule formats

Several older formats were tried before the current placement grammar.

Historical examples included dot-separated rule strings such as:

```text
wide.krusader
personal.half_left.okular
personal.okular.half_left
```

These forms were compact but ambiguous. Domain names, class names, and profile names can all contain characters that make positional parsing fragile. Dotted application classes such as `org.gnome.meld` made that ambiguity worse.

The current `WORKSPACE_PLACEMENT` grammar uses explicit prefixes:

```text
d:<domain> c:<class> g:<geom_profile>
```

This gives the configurator stable fields to parse and render.

Design intent:

1. Token order does not matter.
2. Each prefix may appear at most once in a rule.
3. A placement rule must include `g:`.
4. A placement rule must include at least one of `d:` or `c:`.
5. A placement rule must not include `le:`.
6. Legacy dot-token syntax is not supported by the current parser.

## Why mandatory prefixes were chosen

An intermediate version accepted bare tokens such as `personal`, `okular`, and `personal.okular`, with optional `d:` and `c:` disambiguation.

That was still too ambiguous. A bare token can be a domain or a class. A dotted token can be a domain/class pair, but classes themselves may also contain dots.

The current mandatory prefix model avoids guessing:

```text
d:personal
c:okular
d:personal c:okular
c:okular g:half_right
d:personal c:okular g:half_left
```

This should remain the only supported syntax for managed rule edits.

## Class matching semantics

The current Lua script has two related but different ideas:

1. Target precedence.
2. Class pattern matching.

Target precedence is the broad rule-scope order:

```text
domain.class -> domain -> class
```

Class pattern matching is more detailed. The active script includes ranked class matching for `WORKSPACE_PLACEMENT`:

1. Exact full-string match, for example `org.gnome.meld`.
2. Exact dotted-segment match, for example `meld` matching `org.gnome.meld`.
3. Wildcard prefix on the full class string, for example `org.gnome.*`.
4. Wildcard prefix on a dotted segment, for example `mel*` matching `org.gnome.meld`.

Important current limitation:

The advanced dotted/wildcard class matching is currently part of geometry placement resolution. Other sections, such as `EXCLUDE`, `PIN`, `WORKSPACE_ROUTES`, and `LEFT_EDGE_CORRECTION`, currently use direct lookup behavior. Do not document dotted/wildcard matching as universal unless the Lua runtime is updated and tested to make it universal.

## Qubes-first domain behavior

The current practical target is Qubes OS.

In Qubes:

1. `_QUBES_VMNAME == ""` means `dom0`.
2. A non-empty `_QUBES_VMNAME` is the qube/domain name.
3. The script lowercases the detected domain before matching.

This is the current primary behavior and should not be treated as a problem.

For later non-Qubes support, `_QUBES_VMNAME` may be nil or unavailable. In that case the current script skips domain-based workspace assignment, while global class-based geometry placement can still apply. Broader class-only behavior for non-Qubes systems should be revisited only when non-Qubes testing becomes an active target.

## Why `LEFT_EDGE_CORRECTION` exists

Manual testing showed that `set_window_geometry(x, y, w, h)` can fail to place a window exactly at `x = 0` on some systems. The window may land a few pixels away from the left edge.

The historical model started as a global correction mode. It later became a per-target correction table, and then moved to the current prefixed grammar:

```text
d:<domain> c:<class> le:pos1
d:<domain> c:<class> le:pos2
```

Correction modes:

1. `le:pos1` means call `set_window_position(x, y)` after geometry is applied.
2. `le:pos2` means call `set_window_position2(x, y)` after geometry is applied.

Current design intent:

1. Correction is only relevant when the selected geometry has `x = 0`.
2. Correction should be target-specific until testing proves a simpler global rule is safe.
3. The configurator should expose correction as a troubleshooting or compatibility workflow, not as a normal first-run concept.
4. `get_window_geometry()` can be used in future test actions to detect whether correction is actually needed.

## Version-history observations worth retaining

The deep dive exposed these useful lessons:

1. The script evolved from a personal Qubes/XFCE script into a managed configuration target.
2. User-customization sections and program logic were separated before the Python parser was created.
3. `-- add more here` markers became important as stable insertion points for both humans and renderers.
4. Readability matters: route rows, geometry profiles, comments, and blank separators are part of the user experience.
5. Token-order-independent parsing was a natural result of the prefixed grammar.
6. The configurator should continue treating the Lua file as a user-facing artifact, not as disposable generated code.

## Deferred design questions

Do not let these questions block the current Qubes-first work. They are recorded for later review.

1. Should dotted/wildcard class matching eventually apply to all sections, or only to `WORKSPACE_PLACEMENT`?
2. Should class-only `EXCLUDE` and `PIN` rules work when `_QUBES_VMNAME` is nil on non-Qubes systems?
3. Should class-only `WORKSPACE_ROUTES` work on non-Qubes systems?
4. Should `LEFT_EDGE_CORRECTION` support class-only rules without a domain on non-Qubes systems?
5. Should non-Qubes systems get an explicit domain-like grouping concept, or should they remain class-only?
6. Should legacy dot-token syntax ever be migrated automatically, or should it remain historical only?

Current answer for now:

```text
Qubes first. Preserve the current prefixed grammar. Document the history. Revisit non-Qubes behavior when non-Qubes testing starts.
```
