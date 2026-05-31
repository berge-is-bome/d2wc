# User Documentation

Start here:

1. [Install/Update for Qubes](install-qubes.md) explains how to install or update `d2wc` in Qubes dom0.
2. [Lua Configurables](lua-configurables.md) explains the window behavior users can configure through `d2wc`.
3. [Backups](backups.md) explains where automatic backup archives are stored and what restore support exists now.

## Configurator screenshots

The screenshots below follow the configurator workflow selector order.

### Exclude

Creates rules for windows that `d2wc` should leave alone.

![Exclude workflow](images/d2wc-configurator-exclude.png)

### Pin

Creates rules for windows that should appear on every workspace.

![Pin workflow](images/d2wc-configurator-pin.png)

### Workspace routes

Creates rules that send matching windows to a chosen workspace.

![Workspace routes workflow](images/d2wc-configurator-workspace-routes.png)

### Window geometry

Creates and edits named position and size profiles.

![Window geometry workflow](images/d2wc-configurator-window-geometry.png)

### Workspace placement

Creates rules that apply a geometry profile to matching windows.

![Workspace placement workflow](images/d2wc-configurator-workspace-placement.png)

### Left edge correction

Creates rules for windows that need left-edge placement adjustment.

![Left edge correction workflow](images/d2wc-configurator-left-edge-correction.png)

Project and implementation notes live separately under [`docs/project/`](../project/).
