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
