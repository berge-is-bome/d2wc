# d2wc Packaging

## Purpose

This document describes the packaging direction for `d2wc`.

The first priority is to package `d2wc` cleanly for the environments where it is most likely to be used first:

1. Qubes OS app qubes and dom0-related workflows where appropriate.
2. Fedora-family systems.
3. Debian-family systems later.
4. Other Linux distributions after the architecture is stable.

The packaging plan should remain conservative until the first implementation stack is proven.

## Current project state

The repository currently contains:

1. The active `devilspie2` Lua rules script.
2. Development documentation.
3. No installable configurator application yet.

Packaging should therefore happen in phases.

## Packaging phases

### Phase 0: source checkout

Phase 0 is the current state.

A user or developer clones the repository and manually copies or runs the Lua script.

This is acceptable only while the project is still being designed.

### Phase 1: developer install

Phase 1 should support a developer install for the configurator prototype.

Expected behavior:

1. Install Python package dependencies.
2. Run the configurator from the repository checkout.
3. Use a test copy of the Lua file.
4. Avoid modifying the user's real desktop configuration unless explicitly requested.

This phase is for development and testing, not end users.

### Phase 2: local package

Phase 2 should produce a local package that can be installed on a test system.

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

### Phase 3: distribution-quality package

Phase 3 should refine the package for wider use.

This includes:

1. Clean file layout.
2. Versioned releases.
3. Changelog.
4. License metadata.
5. Dependency metadata.
6. Testable build process.
7. Reproducible source archive.
8. Clear uninstall behavior.

## First target packaging format

The first package target should be Fedora RPM.

Reasons:

1. Qubes templates commonly use Fedora.
2. The development environment is Fedora/Qubes-oriented.
3. RPM packaging will force the project to define paths, commands, dependencies, and file ownership clearly.

Debian packaging should follow after the basic app layout is stable.

## Expected installed commands

The command names are not final, but packaging should eventually provide clear commands.

Possible commands:

1. `d2wc`
2. `d2wc-configure`
3. `d2wc-run`
4. `d2wc-test-left-edge`

Recommended direction:

1. `d2wc configure` opens the configurator.
2. `d2wc run` starts or verifies the managed `devilspie2` runtime.
3. `d2wc reload` reloads or restarts the managed runtime.
4. `d2wc test-left-edge` runs a left-edge correction test harness when implemented.

A single `d2wc` command with subcommands is cleaner than many unrelated command names.

## Desktop integration

The package may install a desktop launcher for the configurator.

A desktop file can allow:

1. Launching the configurator from the application menu.
2. Assigning the command to a keyboard shortcut through the desktop environment.
3. Showing a name and icon in desktop search.

The stable entry point should remain command-based so the user can bind it to a shortcut.

Optional tray behavior should not be required for packaging.

## Runtime ownership

The package should avoid interfering with unrelated `devilspie2` configurations.

The long-term model is that `d2wc` owns the `devilspie2` instance that runs the managed `d2wc` Lua script.

Packaging should therefore avoid installing files in a way that silently takes over a user's existing `devilspie2` setup.

Preferred behavior:

1. Install a default script/template.
2. Let the user initialize a managed config.
3. Start only the managed `d2wc` runtime.
4. Reload or restart only that managed runtime.

## File layout direction

Exact paths should be finalized later, but the project should aim for standard Linux layout.

Possible installed layout:

```text
/usr/bin/d2wc
/usr/share/d2wc/d2wc.lua
/usr/share/applications/d2wc-configurator.desktop
/usr/share/doc/d2wc/
```

Possible user config layout:

```text
~/.config/d2wc/d2wc.lua
~/.config/d2wc/config.toml
~/.local/state/d2wc/backups/
~/.local/state/d2wc/logs/
```

The user's managed Lua file should live in user config, not be edited directly under `/usr/share`.

## Lua script installation model

The packaged Lua script should be treated as a template.

First-run behavior should likely be:

1. Check for `~/.config/d2wc/d2wc.lua`.
2. If missing, copy the packaged template there.
3. Use the user copy as the managed active script.
4. Leave the packaged template unchanged.

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

The first implementation is expected to use Python.

The project should keep core logic separate from UI code:

1. Parser/writer/validator core.
2. Window identity helper code.
3. GTK UI front end.
4. Future Qt UI front end.
5. CLI entry point.

This allows the package to expose both GUI and command-line behavior without duplicating logic.

## Dependency policy

Dependencies should remain modest.

Expected early dependencies:

1. Python 3.
2. PyGObject/GTK for the first UI proof.
3. `devilspie2`.
4. X11 helper tools or libraries as needed for active-window capture.

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
9. Basic smoke tests.

Possible package name:

```text
d2wc
```

The RPM should not assume it can configure Qubes dom0 automatically. Qubes-specific behavior may require careful documentation and possibly separate packaging decisions.

## Debian packaging direction

Debian packaging should follow after Fedora packaging is stable.

The Debian package should use the same source layout and command names where possible.

The project should avoid Fedora-only assumptions in the application code.

## Qubes considerations

Qubes needs special care.

Questions to answer later:

1. Where should `d2wc` run for Qubes workflows?
2. Which parts belong in dom0, if any?
3. Which parts can run in an app qube?
4. How should the managed Lua script be installed or copied?
5. What Qubes-specific dependencies are needed?
6. How should documentation warn users before modifying dom0 behavior?

The first implementation can target the user's known Qubes/XFCE workflow, but packaging should not blindly assume all Qubes users want the same install path.

## Development install

For early development, the repository should eventually support a simple developer workflow such as:

```bash
python -m d2wc configure
```

or:

```bash
./dev/run-configurator
```

The exact command depends on the final source layout.

The developer workflow should use test files by default to avoid damaging the user's active Lua configuration.

## Testing package behavior

Packaging tests should check:

1. The command exists after install.
2. The configurator can open.
3. The managed Lua template is installed.
4. First-run config initialization creates a user copy.
5. Backup directory can be created.
6. The package can be removed cleanly.
7. User config is not deleted on normal uninstall unless explicitly purged.

## Uninstall behavior

Uninstall should remove packaged files but preserve user configuration by default.

User data should remain under:

```text
~/.config/d2wc/
~/.local/state/d2wc/
```

A separate purge instruction can explain how to remove user configuration manually.

## Versioning

The project should use clear semantic-ish versioning once packaging begins.

The current Lua script version is `0.1.12.3`, but the repository package version may need a separate project version once the configurator exists.

Possible approach:

1. Keep Lua script version comments for now.
2. Introduce project package version when the Python application starts.
3. Document when script version and package version diverge.

## Open questions

1. Should the active user Lua file be copied from a package template or generated from structured config?
2. Should the package include a systemd user service later?
3. Should `d2wc run` manage the `devilspie2` process directly?
4. How should Qubes-specific installation differ from ordinary Linux installation?
5. Should GTK and future Qt front ends be separate packages or optional extras?
6. What is the cleanest Fedora RPM dependency set for PyGObject and GTK?
7. What is the cleanest Debian dependency set?
