# d2wc Testing

## Purpose

This document defines the testing strategy for `d2wc`.

The testing goal is simple: the configurator must never damage a user's working Lua rules file. Parser, validator, renderer, backup logic, CLI editing operations, and future UI behavior must therefore be tested before the configurator is allowed to write to a real user configuration.

## Current confirmed verification

The latest confirmed source-checkout verification is recorded in [Development Status](development-status.md).

Latest reported automated verification after PR #12:

```text
197 pytest tests passed.
```

Latest reported manual desktop verification after PR #15:

```text
The selected-window geometry proof worked from dom0.
No config files were read or written.
```

Install `python3-pip` with your package manager, then install the project in editable mode from the repository root:

```bash
python -m pip install -e .
```

For renderer-related work, use this standard verification sequence:

```bash
python -m d2wc validate --config src/d2wc.lua
python -m d2wc render --config src/d2wc.lua --stdout > /tmp/d2wc-rendered.lua
python -m d2wc validate --config /tmp/d2wc-rendered.lua
python -m pytest
```

This proves that:

1. The committed `src/d2wc.lua` validates.
2. The renderer can produce a real output file.
3. The rendered output validates as managed Lua config.
4. The full Python test suite passes.

For non-renderer-only changes, a shorter validation plus pytest run may be enough, but renderer changes should keep the four-command sequence above.

## Testing principles

The project should follow these principles:

1. Test core logic before UI behavior.
2. Test with temporary files before touching user config.
3. Prefer dry-run output before save behavior.
4. Back up before every real write.
5. Treat the current `src/d2wc.lua` as the first real parser fixture.
6. Keep parser/writer/validator tests independent from GTK.
7. Keep Qubes/XFCE behavior as the first desktop integration target.
8. Keep future Qt/KDE support possible by not tying core tests to GTK.
9. Test generated geometry before writing it to `GEOM`.
10. Re-validate rendered Lua output after renderer changes.
11. Preserve comments, blank lines, and marker-tail behavior when editing managed rule-list sections.
12. Keep UI proofs read-only until preview and confirmation paths are tested.
13. Keep automated GTK-entry tests independent from a live desktop session where practical.
14. Build event-data UI tests from representative Devilspie2/Lua data fixtures before wiring real event handoff.

## Event-data UI tests

The next UI branch should test the GTK screen around representative event data, not around live target selection.

Automated tests should verify:

1. A Python event-data fixture can be formatted for the GTK UI.
2. Identity fields are displayed in a stable order.
3. Geometry fields are displayed in a stable order.
4. Missing fields render as `unknown` or another explicit placeholder.
5. The UI path remains read-only.
6. The `configure` entry point still routes to the GTK launcher without requiring a live desktop session in automated tests.

Representative fixture fields should include values corresponding to:

```lua
get_class_instance_name()
get_window_property( '_QUBES_VMNAME' )
get_screen_geometry()
get_window_geometry()
```

Manual tests should verify:

1. `python -m d2wc configure` opens the GTK event-data UI on Qubes/XFCE.
2. `d2wc configure` opens the same UI after editable install refresh.
3. The window displays representative identity and geometry data.
4. The window closes cleanly.
5. No config files are read or written.

Live target-selection experiments are out of scope for the next UI branch.

## Existing test levels

### Unit tests

Unit tests should cover pure logic.

Examples:

1. Rule token parsing.
2. Match-scope handling.
3. Geometry profile validation.
4. Left-edge correction mode validation.
5. Workspace route validation.
6. Managed-block detection.
7. Rendering deterministic Lua for one block.
8. Runtime setting validation.
9. Split-profile generation from screen geometry and `window_border_width`.
10. Rule-list add, modify, and delete operations.
11. Comment preservation and marker-tail behavior.
12. Event-data formatting for GTK display.

These tests should not require a running desktop session.

### Integration tests

Integration tests should cover file-level behavior.

Examples:

1. Parse the full current `src/d2wc.lua`.
2. Render managed blocks back to Lua.
3. Write to a temporary file.
4. Validate the rendered temporary file.
5. Create backups in a temporary directory.
6. Verify invalid Lua configuration samples produce useful errors.
7. Generate `half_left` and `half_right` profiles into a temporary config.
8. Run guarded CLI edit commands against copied temporary configs.
9. Verify that `python -m d2wc configure` routes to the GTK launcher without requiring a live GTK session in automated tests.

These tests should not modify the user's real `~/.config/d2wc/` files.

### Desktop proof tests

Desktop proof tests should cover Qubes/XFCE behavior.

Examples:

1. Launch the GTK configurator from a command.
2. Assign the command to a keyboard shortcut.
3. Display representative event-provided domain/class data.
4. Display representative event-provided screen geometry.
5. Display representative event-provided window geometry.
6. Confirm no config files are read or written.

These tests may require manual confirmation at first.

## Test data

The first real fixture is:

```text
src/d2wc.lua
```

Additional fixtures should be added later under a test directory, for example:

```text
tests/fixtures/
  d2wc-current.lua
  d2wc-minimal.lua
  d2wc-invalid-duplicate-prefix.lua
  d2wc-invalid-missing-geom.lua
  d2wc-invalid-duplicate-workspace-key.lua
```

The current script should be copied into fixtures when tests are created, rather than tests mutating `src/d2wc.lua` directly.

## Dry-run and guarded-write tests

The tool should support dry-run or preview behavior before real writes.

Existing guarded behavior includes:

1. `save` preview by default.
2. `save --write` for real safe-save writes.
3. `GEOM` edit commands preview by default and write only with `--write`.
4. `WORKSPACE_PLACEMENT` edit commands preview by default and write only with `--write`.
5. `WORKSPACE_ROUTES` edit commands preview by default and write only with `--write`.
6. `PIN` edit commands preview by default and write only with `--write`.
7. `EXCLUDE` edit commands preview by default and write only with `--write`.
8. `LEFT_EDGE_CORRECTION` edit commands preview by default and write only with `--write`.
9. GTK and desktop proof windows are read-only until a tested preview and confirmation path exists.

Future UI workflows must preserve the same safety model: preview first, save only after explicit confirmation, and route writes through the tested safe-save helper.

## Backup and write tests

Backup/write tests must use temporary directories.

Required tests:

1. Backup is created before write.
2. Backup name includes timestamp or unique suffix.
3. New content is written to a temporary file first.
4. Target file is replaced only after successful write.
5. Failed validation prevents any write.
6. Failed write leaves previous file intact where possible.
7. Generated split profiles are not written if `window_border_width` validation fails.
8. Rule-list edit failures leave the original file unchanged.

No backup/write test should target the user's actual config directory.

## GTK proof tests

The first GTK/PyGObject launch proof is merged. Ongoing GTK tests should ensure the configurator entry point remains stable.

Automated tests should verify:

1. `python -m d2wc configure` routes to the GTK launcher.
2. Missing GTK/PyGObject produces a clear error and non-zero exit code.
3. Other CLI commands still delegate to the existing CLI parser.
4. Automated tests do not require a live desktop session.

Required manual proof tests:

1. `python -m d2wc configure` opens a GTK window.
2. `d2wc configure` opens the same GTK window after editable install.
3. Window opens on Qubes/XFCE.
4. Window can be closed cleanly.
5. Command can be assigned to a keyboard shortcut.
6. No real user config is modified.

## Devilspie2 event-data notes

The next UI proof should use fixtures or command arguments for event data. Do not attempt to solve live target selection in that branch.

Known behavior from PR #16 research:

1. `devilspie2 --debug` prints an initial startup dump for all currently known or processed windows.
2. After startup, it behaves like an append-only event stream.
3. Capturing the first debug output is not target selection.
4. Capturing the next event after startup is unreliable because menus and launchers can generate intermediary events.
5. Lua can call the needed Devilspie2 functions directly.
6. `debug_print` is useful only when a proof needs to pass data to Python through stdout.

## Left-edge correction tests

Left-edge tests should use the method described in [Left-Edge Correction Testing](left-edge-correction-testing.md).

Required proof:

1. Apply requested geometry with `x = 0`.
2. Read actual geometry.
3. Detect actual `x != requested x` if the offset occurs.
4. Apply `set_window_position(x, y)`.
5. Read actual geometry again.
6. Apply `set_window_position2(x, y)` if needed.
7. Read actual geometry again.
8. Save no permanent rule unless the user confirms.

## Event-monitoring tests

Event monitoring is Phase 2 and should not block Phase 1.

When Phase 2 starts, first tests should only log events.

Required proof:

1. Detect geometry changes for active window.
2. Detect quiet period after resizing stops.
3. Apply threshold.
4. Log final geometry.
5. Do not open configurator yet.
6. Do not save rules.

## Packaging tests

Packaging tests should start after the source-checkout workflow works.

Required first checks:

1. Source checkout can run the CLI.
2. Source checkout can run tests.
3. Local RPM installs command and files.
4. Local RPM install does not require network access once dependencies are present.
5. User config is not overwritten on upgrade.
6. User config is preserved on uninstall.

Qubes/dom0 packaging tests must assume no network access inside dom0.

## Safety gates

The following gates must pass before the configurator can write to a real user config:

1. Parser reads current script.
2. Validator accepts current script.
3. Renderer round-trip preserves the model.
4. Rendered output validates.
5. Backup/write tests pass in temporary directories.
6. Dry-run preview works.
7. `window_border_width` validation passes before generated split profiles are written.
8. Generated split profiles are previewed before save.
9. User explicitly selects a real config file or initializes one.
10. Backup location is writable.
11. Save preview is shown.
12. For UI workflows, the preview and confirmation path must be tested before any real config write is enabled.

## Suggested test tooling

The likely test stack is:

1. `pytest` for Python tests.
2. Temporary directories through pytest fixtures.
3. Plain fixture files under `tests/fixtures/`.
4. Manual test notes for desktop behavior.

## Manual test log format

Manual desktop tests should record enough detail to reproduce failures.

Suggested fields:

1. Date.
2. Distribution.
3. Qubes or non-Qubes.
4. Desktop environment.
5. Window manager.
6. Application.
7. Domain, if available.
8. Class.
9. Command run.
10. Expected result.
11. Actual result.
12. Notes.

## Continuous integration

The current GitHub Actions test workflow should continue to run the Python test suite. Later CI expansion can include additional fixture validation and render round-trip checks.

Desktop behavior will remain manual until a suitable test environment is designed.

## Related documents

1. [Development Status](development-status.md)
2. [Event-Data GTK UI Direction](event-data-ui-direction.md)
3. [UI Flow](ui-flow.md)
4. [Runtime Architecture](runtime-architecture.md)
5. [Implementation Plan](implementation-plan.md)
6. [Left-Edge Correction Testing](left-edge-correction-testing.md)
7. [Lua Design History Notes](lua-design-history.md)

## Immediate test priorities

The current core proof has already covered parser, grammar, validation, renderer, settings, split-profile, backup path, safe save, CLI, duplicate-validation, shadow-validation, and add/modify/delete operations for all six managed Lua sections.

The next immediate test priorities are:

1. Keep the full source-checkout verification path green.
2. Keep the automated GTK entrypoint routing test green without requiring a live desktop session.
3. Add event-data formatting tests for the next GTK UI proof.
4. Manually verify `python -m d2wc configure` opens and closes the event-data UI on Qubes/XFCE.
5. Confirm that the event-data UI proof performs no real config writes.
6. Keep rule-editing UI writes deferred until preview and confirmation paths are implemented.

No UI save workflow should be built before the read-only event-data UI proof is working.

## Installer decision-flow manual checks

Use these shell-level scenarios to validate installer branching in dom0:

1. Update path keeps existing managed default without prompting.
   - Preconditions: `~/.config/d2wc/lua/d2wc.lua` exists and is a valid managed file, package already installed.
   - Run: `./install-qubes.sh <source-vm>`.
   - Expectation: no alternate filename prompt; managed file remains active.

2. First install migrates legacy managed regular file before templating.
   - Preconditions: no existing package install, `~/.config/devilspie2/d2wc.lua` is a valid managed regular file.
   - Run: `./install-qubes.sh <source-vm>`.
   - Expectation: legacy file is copied into `~/.config/d2wc/lua/` exactly once (prompting for alternate name only on collision), `~/.config/devilspie2/d2wc.lua` is not migrated a second time, and final `~/.config/devilspie2/d2wc.lua` becomes a symlink to migrated file.

3. Unmanaged legacy regular file remains untouched.
   - Preconditions: `~/.config/devilspie2/d2wc.lua` exists but is not valid d2wc-managed Lua.
   - Run: `./install-qubes.sh <source-vm>`.
   - Expectation: warning is printed; existing file is not replaced.

4. Existing safe symlink remains update-safe.
   - Preconditions: `~/.config/devilspie2/d2wc.lua` symlink points inside `~/.config/d2wc/lua/`.
   - Run: `./install-qubes.sh <source-vm>`.
   - Expectation: symlink can be refreshed safely without alternate filename prompt on normal updates.

5. External symlink remains untouched.
   - Preconditions: `~/.config/devilspie2/d2wc.lua` symlink points outside `~/.config/d2wc/lua/`.
   - Run: `./install-qubes.sh <source-vm>`.
   - Expectation: warning is printed; external symlink is left unchanged.
