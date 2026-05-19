# Lua Configurables

The current `d2wc` execution layer is a `devilspie2` Lua script. The configurator should treat the script as a managed rules file and edit only the known user-customizable sections.

## Rule grammar

Rules use space-separated prefixed tokens.

Supported prefixes:

1. `d:<domain>` for a Qubes domain or Linux desktop grouping concept.
2. `c:<class>` for the application class.
3. `g:<geom_profile>` for a named geometry profile.
4. `le:<pos1|pos2>` for left-edge correction mode.

Token order should not matter. Matching is case-insensitive.

The current matching precedence is:

1. `domain.class`
2. `domain`
3. `class`

A rule with duplicate tokens of the same prefix is invalid and should be skipped rather than guessed.

## `EXCLUDE`

`EXCLUDE` tells `d2wc` to ignore matching windows.

The configurator should use this for windows that should not be moved, resized, pinned, or routed. Examples include app menus, splash windows, panels, transient helpers, or applications that behave badly when managed.

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

## `WORKSPACE_PLACEMENT`

`WORKSPACE_PLACEMENT` links a domain, class, or domain/class target to a named geometry profile.

The configurator should make this feel like: "When this window opens, use this saved size and position."

User-facing actions:

1. Apply a geometry profile to this exact domain/class combination.
2. Apply a geometry profile to this whole domain.
3. Apply a geometry profile to this application class everywhere.
4. Preview the exact rule before saving.
5. Warn when a referenced geometry profile does not exist.

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
2. Do not rewrite program logic during normal configuration.
3. Validate all generated rules before writing.
4. Keep generated rule order stable.
5. Back up the previous Lua file before saving.
6. Provide a preview/diff before applying changes.
