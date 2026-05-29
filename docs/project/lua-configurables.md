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
Menu -> Configure -> Window events
```

Existing user values are preserved by installer runtime migrations. If a user has set the value to `false`, an update must not change it back to `true`.

### `D2WC_CONFIGURATOR_CLASS`

```lua
local D2WC_CONFIGURATOR_CLASS = "d2wc-configurator"
```

This setting identifies the configurator's own GTK/X11 class.

The Lua handoff uses it to avoid launching another configurator when the current window is the configurator itself.

In this context, class means the X11/WM class value derived from `get_class_instance_name()`, not a Python class.

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
