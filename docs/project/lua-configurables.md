# Lua Configurables

The current `d2wc` execution layer is a `devilspie2` Lua script. The configurator treats the script as a managed rules file and edits only the known user-customizable sections and supported managed runtime settings.

The current practical target is Qubes OS with XFCE. Broader non-Qubes behavior is a later goal and should be tested deliberately before the documentation promises full non-Qubes parity.

## Managed runtime settings

The managed Lua file includes runtime settings outside the six rule sections.

### `D2WC_EVENT_HANDOFF_ENABLED`

```lua
local D2WC_EVENT_HANDOFF_ENABLED = true
```

This setting controls whether Devilspie2 window events can open the `d2wc` configurator automatically.

When enabled, the Lua script can launch bare `d2wc` when a new normal application window appears and no existing managed target rule already covers that window.

Set it to `false` to disable automatic launching:

```lua
local D2WC_EVENT_HANDOFF_ENABLED = false
```

The configurator exposes this setting at:

```text
Menu -> Configure -> Behavior
```

Existing user values are preserved by installer runtime migrations. If a user has set the value to `false`, an update must not change it back to `true`.

### `D2WC_CONFIGURATOR_CLASS`

```lua
local D2WC_CONFIGURATOR_CLASS = "d2wc-configurator"
```

This setting identifies the configurator's own GTK/X11 class.

The Lua handoff uses it to avoid launching another configurator when the current window is the configurator itself.

In this context, class means the X11/WM class value derived from `get_class_instance_name()`, not a Python class.

## Rule grammar

Rules use space-separated prefixed tokens.

Supported prefixes:

1. `d:<domain>` for a Qubes domain.
2. `c:<class>` for the application class.
3. `g:<geom_profile>` for a named geometry profile.
4. `le:<pos1|pos2>` for left-edge correction mode.

Token order should not matter. Matching is case-insensitive.

The current target precedence is:

1. `domain.class`
2. `domain`
3. `class`

A rule with duplicate tokens of the same prefix is invalid and should be skipped rather than guessed.

Legacy dot-token rules such as `personal.okular`, `krusader.wide`, or `personal.okular.half_left` are historical only. Current managed edits should use the prefixed grammar.

## Qubes domain behavior

In Qubes, `_QUBES_VMNAME` identifies the source domain.

Current behavior:

1. If `_QUBES_VMNAME` is an empty string, the Lua script treats the window as `dom0`.
2. If `_QUBES_VMNAME` is non-empty, the Lua script uses that value as the domain.
3. The detected domain is lowercased before matching.
4. If `_QUBES_VMNAME` is nil or unavailable, domain-based workspace assignment is skipped.

The nil case is mainly relevant to future non-Qubes testing. It should not distract from the current Qubes-first target.

## Class matching scope

The Lua script has two related ideas:

1. Target precedence: `domain.class -> domain -> class`.
2. Class pattern matching inside placement rules.

`WORKSPACE_PLACEMENT` currently has ranked class matching for application classes:

1. Exact full-string match, for example `org.gnome.meld`.
2. Exact dotted-segment match, for example `meld` matching `org.gnome.meld`.
3. Wildcard prefix on the full class string, for example `org.gnome.*`.
4. Wildcard prefix on a dotted segment, for example `mel*` matching `org.gnome.meld`.

Do not assume that the same dotted/wildcard matching applies to every managed section. `EXCLUDE`, `PIN`, `WORKSPACE_ROUTES`, and `LEFT_EDGE_CORRECTION` currently use direct target lookups for rule execution.

The Lua event handoff suppression logic uses the same practical target idea: a window is considered already configured when it matches a managed target rule in one of the handling sections listed under [Automatic handoff suppression](#automatic-handoff-suppression).

## Automatic handoff suppression

When `D2WC_EVENT_HANDOFF_ENABLED` is true, the Lua runtime checks whether the current normal window is already handled before launching the configurator.

The following sections count as managed target rules for handoff suppression:

1. `EXCLUDE`
2. `PIN`
3. `WORKSPACE_ROUTES`
4. `WORKSPACE_PLACEMENT`
5. `LEFT_EDGE_CORRECTION`

`GEOM` alone does not count because geometry profiles do not target windows by themselves.

## `EXCLUDE`

`EXCLUDE` tells `d2wc` to ignore matching domains/windows.

The configurator should use this for windows that should not be moved, resized, pinned, routed, corrected, or used to open the configurator repeatedly.

User-facing actions:

1. Exclude this exact domain/class combination.
2. Exclude this whole domain.
3. Exclude this application class everywhere.
4. Show existing exclusions that already match the selected window.

## `PIN`

`PIN` marks matching windows as visible on all workspaces.

The Lua script applies pinning after workspace assignment because assigning a workspace removes the sticky flag.

User-facing actions:

1. Pin this exact domain/class combination.
2. Pin all windows from this domain.
3. Pin this application class everywhere.
4. Remove or disable an existing pin rule.

## `WORKSPACE_ROUTES`

`WORKSPACE_ROUTES` maps matching windows to a workspace number.

The configurator should make this feel like: "When this window opens, send it to workspace N."

User-facing actions:

1. Route this exact domain/class combination to the selected workspace.
2. Route this domain to the selected workspace.
3. Route this class to the selected workspace.
4. Detect duplicate or conflicting routes before writing.

The Lua script notes that only one list per workspace key is allowed. If duplicate Lua table keys are used, later keys overwrite earlier keys. The configurator must prevent that situation.

## `GEOM`

`GEOM` contains named geometry profiles.

Each profile stores:

1. `x`
2. `y`
3. `w`
4. `h`

The configurator should let users create profiles by capturing the selected window's current geometry. It should also generate common profiles such as `half_left` and `half_right` from the current screen layout.

User-facing actions:

1. Capture current geometry as a named profile.
2. Update an existing profile from the current window.
3. Create or refresh generated profiles such as `half_left` and `half_right`.
4. Show which placement rules depend on a profile before renaming or deleting it.

Geometry values live in `GEOM` profiles. Historical inline geometry tables inside rule entries are not part of the current managed grammar.

## `WORKSPACE_PLACEMENT`

`WORKSPACE_PLACEMENT` links a domain, class, or domain/class target to a named geometry profile.

The configurator should make this feel like: "When this window opens, use this saved size and position."

User-facing actions:

1. Apply a geometry profile to this exact domain/class combination.
2. Apply a geometry profile to this whole domain.
3. Apply a geometry profile to this application class everywhere.
4. Preview the exact rule before saving.
5. Warn when a referenced geometry profile does not exist.

`WORKSPACE_PLACEMENT` is the section where advanced dotted/wildcard class matching currently matters.

## `LEFT_EDGE_CORRECTION`

`LEFT_EDGE_CORRECTION` handles systems where `set_window_geometry()` does not place windows exactly at `x = 0`.

Supported correction modes:

1. `le:pos1` uses `set_window_position(x, y)`.
2. `le:pos2` uses `set_window_position2(x, y)`.

The configurator should not hide this completely, but it should not make ordinary users think about it unless needed. The best UI is probably a compatibility or troubleshooting section that appears when a captured window is expected to be at the left edge but is not actually placed there.

User-facing actions:

1. Test left-edge placement.
2. Try correction mode `pos1`.
3. Try correction mode `pos2`.
4. Save the working correction mode for the selected target.

## Configurator write rules

The configurator should write deterministic, readable Lua.

Required behavior:

1. Preserve user comments where practical.
2. Do not rewrite program logic during normal rule configuration.
3. Allow targeted runtime setting changes that are explicitly exposed in the configurator, such as `D2WC_EVENT_HANDOFF_ENABLED`.
4. Validate all generated rules before writing.
5. Keep generated rule order stable.
6. Back up the previous Lua file before saving.
7. Provide a preview before applying rule changes.

For historical context behind these sections and the current grammar, see [Lua Design History Notes](lua-design-history.md).
