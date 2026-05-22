# d2wc Testing

## Purpose

This document defines the testing strategy for `d2wc`.

The testing goal is simple: the configurator must never damage a user's working Lua rules file. Parser, validator, renderer, backup logic, CLI editing operations, and future UI behavior must therefore be tested before the configurator is allowed to write to a real user configuration.

## Current confirmed verification

The latest confirmed source-checkout verification is recorded in [Development Status](development-status.md).

Latest reported verification after PR #9:

```text
153 pytest tests passed.
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

## Test levels

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

These tests should not modify the user's real `~/.config/d2wc/` files.

### Desktop proof tests

Desktop proof tests should cover Qubes/XFCE behavior.

Examples:

1. Launch the GTK configurator from a command.
2. Assign the command to a keyboard shortcut.
3. Capture active-window class.
4. Capture active-window domain where `_QUBES_VMNAME` exists.
5. Treat an empty `_QUBES_VMNAME` as `dom0`.
6. Capture active-window geometry.
7. Detect left-edge placement offset using `get_window_geometry()`.
8. Preview generated split profiles on the active screen.

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

## Parser tests

Parser tests should prove that the managed Lua sections can be found and read.

Required parser test cases:

1. Finds `EXCLUDE`.
2. Finds `PIN`.
3. Finds `WORKSPACE_ROUTES`.
4. Finds `GEOM`.
5. Finds `WORKSPACE_PLACEMENT`.
6. Finds `LEFT_EDGE_CORRECTION`.
7. Preserves unmanaged Lua content outside managed blocks.
8. Fails clearly when a required block is missing.
9. Fails clearly when a block is malformed.

## Rule grammar tests

Rule grammar tests should cover prefixed tokens.

Supported prefixes:

1. `d:` for domain.
2. `c:` for class.
3. `g:` for geometry profile.
4. `le:` for left-edge correction mode.

Required valid examples:

```text
d:personal
```

```text
c:krusader
```

```text
d:work c:navigator
```

```text
d:personal c:okular g:half_left
```

```text
d:dom0 c:qubes-qube-manager le:pos1
```

Required grammar-invalid examples:

```text
"d:personal d:work c:okular g:half_left"
```

```text
"d:personal c:okular c:krusader g:half_left"
```

```text
"d:personal c:okular g:half_left g:half_right"
```

```text
"d:personal c:okular le:pos1 le:pos2"
```

```text
"d:personal c:okular x:unknown"
```

Completion criteria:

1. Duplicate prefixes are rejected.
2. Unknown prefixes are rejected.
3. Valid rules produce structured data.
4. Error messages are user-facing enough for the configurator.

## Section validation tests

Each managed section has different validation rules.

### `EXCLUDE`

Tests should verify:

1. Rule has at least `d:` or `c:`.
2. Rule does not require `g:`.
3. Rule does not require `le:`.
4. Duplicate rules are detected.

### `PIN`

Tests should verify:

1. Rule has at least `d:` or `c:`.
2. Rule does not require `g:`.
3. Rule does not require `le:`.
4. Duplicate rules are detected.

### `WORKSPACE_ROUTES`

Tests should verify:

1. Workspace key is an integer.
2. Workspace key is not duplicated.
3. Route rule has at least `d:` or `c:`.
4. Adding a rule appends to the existing workspace list instead of creating another same-number key.
5. Comments around route rows are preserved where practical.
6. Tail comments after `-- add more here` are preserved as tail content.

### `GEOM`

Tests should verify:

1. Profile name is valid.
2. `x`, `y`, `w`, and `h` exist.
3. Values are integers.
4. Width and height are positive.
5. Duplicate profile names are detected.
6. Generated `half_left` and `half_right` profiles are valid `GEOM` entries.
7. Rendered `x`, `y`, `w`, and `h` columns remain readable and aligned.

### `WORKSPACE_PLACEMENT`

Tests should verify:

1. Rule has at least `d:` or `c:`.
2. Rule has exactly one `g:`.
3. Referenced geometry profile exists.
4. Duplicate or shadowed rules are detected where practical.

### `LEFT_EDGE_CORRECTION`

Tests should verify:

1. Rule has at least `d:` or `c:`.
2. Rule has exactly one `le:`.
3. Correction mode is `pos1` or `pos2`.
4. Duplicate correction rules are detected.

## Runtime settings tests

Runtime settings are not Lua rule strings, but they affect generated output and save behavior.

Required tests for `window_border_width`:

1. Default value exists or is derived safely.
2. Value must be numeric.
3. Value must be an integer.
4. Value must be zero or positive.
5. Negative values are rejected.
6. Non-numeric values are rejected.
7. Changing the value changes generated split-profile geometry predictably.
8. Validation errors explain the problem in user-facing language.

## Generated split-profile tests

Generated split-profile tests should prove that `d2wc` can calculate `half_left` and `half_right` from screen geometry and `window_border_width`.

Required tests:

1. Generate `half_left` and `half_right` from a simple single-monitor geometry.
2. Use `window_border_width` when calculating width and x-position values.
3. Confirm both generated profiles have valid integer `x`, `y`, `w`, and `h` values.
4. Confirm width and height are positive.
5. Confirm changing `window_border_width` changes generated output.
6. Preview both generated profiles together before writing.
7. Reject invalid border widths before rendering.
8. Write generated profiles only to a temporary config during tests.

## Renderer tests

Renderer tests should prove that generated Lua is stable and readable.

Required behavior:

1. Render each managed block in deterministic order where practical.
2. Keep valid Lua syntax.
3. Preserve unmanaged Lua program logic.
4. Avoid duplicate workspace keys.
5. Preserve pure note comments.
6. Preserve blank separator lines.
7. Align right-side comments in managed rule-list sections where supported.
8. Align right-side comments in `GEOM` entries.
9. Render generated `half_left` and `half_right` profiles as normal `GEOM` entries.
10. Preserve marker-tail comments after `-- add more here` in edited sections.

Test approach:

1. Parse fixture.
2. Render without changes.
3. Write rendered output to a temporary file.
4. Parse rendered output again.
5. Confirm parsed model is equivalent.
6. Validate rendered output.

This is more important than byte-for-byte output matching.

## Dry-run and guarded-write tests

The tool should support dry-run or preview behavior before real writes.

Existing guarded behavior includes:

1. `save` preview by default.
2. `save --write` for real safe-save writes.
3. `GEOM` edit commands preview by default and write only with `--write`.
4. `WORKSPACE_PLACEMENT` edit commands preview by default and write only with `--write`.
5. `WORKSPACE_ROUTES` edit commands preview by default and write only with `--write`.

The next guarded edit commands should follow the same pattern for `PIN` and `EXCLUDE`.

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

The first UI proof should be GTK/PyGObject.

Required manual proof tests:

1. `python -m d2wc configure` opens a GTK window.
2. Window opens on Qubes/XFCE.
3. Window can be closed cleanly.
4. Command can be assigned to a keyboard shortcut.
5. Configurator can load a test Lua file.
6. Configurator can show parsed configuration summary.
7. No real user config is modified.

GTK proof should happen after parser, validator, renderer, safe save behavior, and current target-rule edit proofs are proven, not before.

## Active-window capture tests

Active-window capture is desktop-specific and should be tested carefully.

Required tests on Qubes/XFCE:

1. Capture a normal terminal window.
2. Capture a file manager window.
3. Capture a browser window.
4. Capture a dom0 tool where relevant.
5. Read class.
6. Read title.
7. Read geometry.
8. Read `_QUBES_VMNAME` where available.
9. Treat empty `_QUBES_VMNAME` as `dom0` where relevant.
10. Handle missing `_QUBES_VMNAME` without failure.

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
2. [UI Flow](ui-flow.md)
3. [Runtime Architecture](runtime-architecture.md)
4. [Implementation Plan](implementation-plan.md)
5. [Left-Edge Correction Testing](left-edge-correction-testing.md)
6. [Lua Design History Notes](lua-design-history.md)

## Immediate test priorities

The current core proof has already covered parser, grammar, validation, renderer, settings, split-profile, backup path, safe save, CLI, duplicate-validation, shadow-validation, placement edit, route edit, and route comment preservation tests.

The next immediate test priorities are:

1. `PIN` add, modify, and delete operation tests.
2. `EXCLUDE` add, modify, and delete operation tests.
3. Rule-list comment preservation tests for `PIN` and `EXCLUDE`.
4. Marker-tail preservation tests for `PIN` and `EXCLUDE`.
5. Guarded CLI preview/write tests for `PIN` and `EXCLUDE`.
6. Continue using copied temporary configs for manual smoke testing.

No UI save workflow should be built before the target-rule operations are proven through CLI/core tests.
