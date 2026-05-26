# d2wc

Devilspie2 Workspace Configurator.

Created by André, with code developed in collaboration with ChatGPT and Codex.

`d2wc` is a desktop workspace and window placement configurator for Linux systems that use Devilspie2.

It helps keep application windows predictable: on the right workspace, at the right size and position, pinned where useful, or ignored when a window should not be managed.

The first public target is Qubes OS with XFCE. Broader X11/Linux use is part of the project direction, but should be treated as experimental until it has been tested on those desktops.

## What d2wc helps you do

### Route windows to workspaces

Send matching windows to the workspace where they belong.

A route can be broad, such as every window from a Qubes domain, or narrow, such as one application from one domain.

### Place windows with saved geometry profiles

Save reusable window size and position profiles, then apply those profiles to matching windows.

This is useful for layouts such as a file manager on the left, a browser on the right, a document viewer on a second workspace, or any other repeated desktop arrangement.

### Pin selected windows

Keep selected windows visible on all workspaces.

This is useful for small monitors, utility windows, notes, panels, or other windows that should stay available while moving between workspaces.

### Exclude windows from automation

Tell `d2wc` to leave selected windows alone.

This is useful for menus, splash windows, helper dialogs, panels, launchers, or applications that should not be moved, resized, routed, pinned, or corrected.

### Correct left-edge placement problems

Some desktop environments or window-manager combinations may not place a window exactly on the left edge when asked to do so.

`d2wc` includes a left-edge correction workflow for those cases.

## The configurator

`d2wc` includes a GTK configurator for managing the supported rule types.

The configurator provides these workflows:

1. Exclude
2. Pin
3. Workspace routes
4. Window geometry
5. Workspace placement
6. Left edge correction

Each workflow uses a focused grid with one top row for adding a new rule and configured rows below it for existing rules. Rows can be added, modified, deleted, applied, or undone before applying.

The configurator also offers per-workflow help from the `Menu` button or by pressing `F1`.

## Known window suggestions

The configurator can populate Machine and Application choices from windows that are already known while `d2wc` is open.

This makes new rules easier to create because common values can be selected from dropdowns instead of typed from memory.

## Installed user config

The installed configurator uses this managed Devilspie2 file by default:

```text
~/.config/devilspie2/d2wc.lua
```

Existing Devilspie2 scripts in the same directory are not replaced by the installer.

## Launching d2wc

After installation, launch the configurator with:

```bash
d2wc
```

The explicit configurator command is also available:

```bash
d2wc configure
```

## Qubes dom0 installation

For Qubes users, the repository includes a source-archive installation flow for dom0.

Use the installation guide here:

```text
docs/qubes-dom0-installation.md
```

## Documentation

Useful project documents:

1. `docs/qubes-dom0-installation.md` for the Qubes dom0 install and update flow.
2. `docs/lua-configurables.md` for the supported rule types and user-editable sections.
3. `docs/backup-archives.md` for backup behavior during guarded writes.
4. `docs/product-development-brief.md` for the product direction and intended user outcomes.
5. `docs/development-status.md` for current development status and verification notes.
6. `docs/repository-layout.md` for the repository structure and documentation index.

## Project status

`d2wc` is preparing for its first public release.

The current release focus is Qubes OS with XFCE, a GTK configurator, guarded writes to the managed config, and clear installation documentation.

## License

See `LICENSE`.
