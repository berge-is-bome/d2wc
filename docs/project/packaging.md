# d2wc Packaging

## Purpose

This document describes the packaging and installation direction for `d2wc`.

The first priority is to support the environments where `d2wc` is most likely to be used first:

1. Qubes OS dom0.
2. Fedora-family systems.
3. Debian-family systems later.
4. Other Linux distributions after the architecture is stable.

The packaging plan should remain conservative until the first public release path is proven.

## Current project state

The repository currently contains:

1. The active Devilspie2 Lua rules template.
2. A Python package with the `d2wc` command entry point.
3. Parser, validator, renderer, safe-save, backup, and guarded edit logic for the managed Lua sections.
4. A GTK configurator for the managed config.
5. Known-window inventory parsing, capture, stream, and GTK dropdown integration.
6. Qubes/dom0 source-archive install and update support.
7. User-facing documentation under `docs/user/` and project documentation under `docs/project/`.

The current public-release installation path is documented in [Install/Update for Qubes](../user/install-qubes.md).

Distribution packages are still future work.

## Current Qubes/dom0 source-archive installation model

The current source-archive workflow is documented in [Install/Update for Qubes](../user/install-qubes.md).

The workflow uses:

1. A networked source VM to clone the repository and create `/tmp/d2wc.tgz`.
2. dom0 to copy the installer from the source VM.
3. The dom0 installer to copy and validate `/tmp/d2wc.tgz` from the selected source VM.
4. The dom0 installer to extract, install, create or preserve the managed config, and configure the user command path.

Before replacing the extracted source tree in `~/.local/share/d2wc/source`, the installer copies and validates `/tmp/d2wc.tgz` from the selected source VM.

Current user-path layout:

```text
~/.cache/d2wc/
~/.local/share/d2wc/source/
~/.config/d2wc/lua/
~/.config/devilspie2/d2wc.lua
```

`~/.cache/d2wc/` stores the copied source archive cache.

`~/.local/share/d2wc/source/` stores the extracted local installation source used by the dom0 installer.

`~/.config/d2wc/lua/` stores user-owned `d2wc` managed Lua files.

`~/.config/devilspie2/d2wc.lua` is the Devilspie2-facing symlink only and points to the active file under `~/.config/d2wc/lua/`. Unrelated Devilspie2 scripts and symlinks are not overwritten.

## Managed config workflow

The managed config workflow is documented in [Managed Config Workflow](managed-config-workflow.md).

In summary:

1. `d2wc` owns managed Lua files under `~/.config/d2wc/lua/`.
2. Devilspie2 continues to load the active managed file through `~/.config/devilspie2/d2wc.lua`.
3. The Devilspie2-facing path is an integration symlink, not the primary config store.
4. The configurator should open and save only `d2wc` managed Lua files.
5. The configurator should not become a generic Devilspie2 Lua editor.

## Packaging phases

### Phase 0: source checkout

Complete.

A user or developer can clone the repository and run the Lua script or Python package from source.

### Phase 1: developer install

Complete for the current development workflow.

Supported behavior:

1. Install the Python package in editable mode from the repository root.
2. Run the CLI and GTK configurator from the repository checkout.
3. Use the dedicated test-config workflow for isolated UI testing.
4. Avoid modifying unrelated user configuration.

### Phase 2: Qubes/dom0 source-archive install

Complete for the current public-release target.

Supported behavior:

1. Prepare a source archive in a networked source VM.
2. Copy and run the installer in dom0.
3. Install or update the user-site Python package without dom0 network access.
4. Store the copied archive under `~/.cache/d2wc/`.
5. Store extracted source under `~/.local/share/d2wc/source/`.
6. Store managed Lua files under `~/.config/d2wc/lua/`.
7. Activate Devilspie2 through `~/.config/devilspie2/d2wc.lua` when safe.
8. Keep unrelated Devilspie2 scripts untouched.
9. Launch the installed `d2wc` command.

### Phase 3: local package

Future work.

For Fedora-family systems, this likely means an RPM.

For Debian-family systems, this eventually means a `.deb` package.

The package should install:

1. Configurator command.
2. Python modules.
3. Managed Lua script template.
4. Desktop file, if useful.
5. Icons, if added.
6. Documentation.
7. Optional helper service files, if needed later.

### Phase 4: distribution-quality package

Future work.

This includes:

1. Clean file layout.
2. Versioned releases.
3. Changelog.
4. License metadata.
5. Dependency metadata.
6. Testable build process.
7. Reproducible source archive.
8. Clear uninstall behavior.

## First distribution package target

The first distribution package target should be Fedora RPM.

Reasons:

1. Qubes templates commonly use Fedora.
2. The development environment is Fedora/Qubes-oriented.
3. RPM packaging will force the project to define paths, commands, dependencies, and file ownership clearly.

Debian packaging should follow after the basic app layout is stable.

## Current installed command

The current Python package provides this console entry point:

```bash
d2wc
```

The current behavior is:

1. `d2wc` opens the GTK configurator.
2. `d2wc configure` also opens the GTK configurator.
3. Other CLI subcommands remain available behind the same `d2wc` command.

The single `d2wc` command remains the preferred direction.

## Desktop integration

The package may later install a desktop launcher for the configurator.

A desktop file can allow:

1. Launching the configurator from the application menu.
2. Assigning the command to a keyboard shortcut through the desktop environment.
3. Showing a name and icon in desktop search.

The stable entry point should remain command-based so the user can bind it to a shortcut.

Optional tray behavior should not be required for packaging.

## Runtime ownership

The package should avoid interfering with unrelated `devilspie2` configurations.

The current Qubes/dom0 installer updates only the managed integration symlink when safe:

```text
~/.config/devilspie2/d2wc.lua
```

It does not remove, replace, or rewrite unrelated Lua scripts or symlinks in `~/.config/devilspie2/`.

The longer-term model is that `d2wc` should own the Devilspie2 instance that runs the managed `d2wc` Lua script.

Packaging should therefore avoid installing files in a way that silently takes over a user's existing Devilspie2 setup.

Preferred packaged behavior:

1. Install a default script/template.
2. Let the user initialize a managed config.
3. Start only the managed `d2wc` runtime.
4. Reload or restart only that managed runtime.

## File layout direction

Exact distribution package paths should be finalized later, but the project should aim for standard Linux layout.

Possible installed layout:

```text
/usr/bin/d2wc
/usr/share/d2wc/d2wc.lua
/usr/share/applications/d2wc-configurator.desktop
/usr/share/doc/d2wc/
```

Possible user layout for distribution packages:

```text
~/.config/d2wc/lua/
~/.config/d2wc/config.toml
~/.local/state/d2wc/backups/
~/.local/state/d2wc/logs/
```

The current Qubes/dom0 source-archive flow deliberately uses `~/.config/d2wc/lua/` as the managed config home and `~/.config/devilspie2/d2wc.lua` as the Devilspie2 integration symlink.

## Lua script installation model

The packaged Lua script should be treated as a template.

First-run behavior should likely be:

1. Check for the user-managed default file.
2. If missing, copy the packaged template to `~/.config/d2wc/lua/d2wc.lua`.
3. Use the user copy as the managed active script.
4. Activate Devilspie2 through the integration symlink when safe.
5. Leave the packaged template unchanged.

This allows package updates to ship a new template without overwriting the user's active rules.

## Configuration migration

Later versions may need to update the Lua script logic while preserving user-managed rules.

Potential migration model:

1. Separate program logic from user data where possible.
2. Keep managed sections parseable and stable.
3. Before migration, back up the user's current Lua file.
4. Apply new program logic while preserving managed blocks.
5. Validate the resulting file.
6. Report migration results clearly.

This is a reason to keep the managed block format deterministic.

## Python packaging direction

The first implementation uses Python.

The project should keep core logic separate from UI code:

1. Parser/writer/validator core.
2. Window identity helper code.
3. Known-window inventory helpers.
4. GTK UI front end.
5. Future Qt UI front end.
6. CLI entry point.

This allows the package to expose both GUI and command-line behavior without duplicating logic.

## Dependency policy

Dependencies should remain modest.

Expected early dependencies:

1. Python 3.
2. PyGObject/GTK for the first UI.
3. `devilspie2`.
4. X11 helper tools or libraries as needed for active-window capture or workspace inspection.

Optional or later dependencies:

1. PySide6 for a Qt/KDE front end.
2. Additional StatusNotifier/AppIndicator support if optional tray mode is added.
3. Test tooling.
4. Packaging/build tooling.

Avoid adding a web stack for the first implementation.

## Fedora RPM direction

The Fedora RPM should eventually define:

1. Package name.
2. Version.
3. License.
4. Source archive.
5. Python build/install steps.
6. Runtime dependencies.
7. Installed files.
8. Desktop file validation.
