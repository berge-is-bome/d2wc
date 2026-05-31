# d2wc Packaging

Packaging direction for `d2wc` should stay conservative until the first public release path is proven.

The first packaging priorities are:

1. Qubes OS dom0 source-archive install/update flow.
2. Fedora-family systems.
3. Debian-family systems later.
4. Other Linux distributions after the architecture is stable.

Current install and managed-config behavior is documented elsewhere:

1. [Install/Update for Qubes](../user/install-qubes.md) documents the user-facing Qubes install/update flow.
2. [Installation Workflow](installation-workflow.md) documents current installer behavior and future installer principles.
3. [Managed Config Workflow](managed-config-workflow.md) documents managed-file ownership, active-file selection, File Open, Save As, and Devilspie2 symlink safety.

Distribution packages are still future work.

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

The current Qubes/dom0 source-archive installer supports user-site installation without dom0 network access. Current behavior is documented in [Installation Workflow](installation-workflow.md).

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
~/.config/d2wc/settings.json
~/.local/state/d2wc/backups/
~/.local/state/d2wc/logs/
```

The current Qubes/dom0 source-archive flow deliberately uses `~/.config/d2wc/lua/` as the managed config home, `~/.config/d2wc/settings.json` as the UI settings file, and `~/.config/devilspie2/d2wc.lua` as the Devilspie2 integration symlink.

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
