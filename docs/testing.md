# d2wc Testing

## Purpose

This document defines the first testing strategy for `d2wc`.

The testing goal is simple: the configurator must never damage a user's working Lua rules file. The parser, validator, renderer, backup logic, and UI proof must therefore be tested before the configurator is allowed to write to a real user configuration.

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

These tests should not require a running desktop session.

### Integration tests

Integration tests should cover file-level behavior.

Examples:

1. Parse the full current `src/d2wc.lua`.
2. Render managed blocks back to Lua.
3. Write to a temporary file.
4. Create backups in a temporary directory.
5. Verify invalid Lua configuration samples produce useful errors.

These tests should not modify the user's real `~/.config/d2wc/` files.

### Desktop proof tests

Desktop proof tests should cover Qubes/XFCE behavior.

Examples:

1. Launch the GTK configurator from a command.
2. Assign the command to a keyboard shortcut.
3. Capture active-window class.
4. Capture active-window domain where `_QUBES_VMNAME` exists.
5. Capture active-window geometry.
6. Detect left-edge placement offset using `get_window_geometry()`.

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

Completion criteria:

1. The parser can read the current script.
2. Parsed output can be inspected in a developer-friendly format.
3. Errors identify the block and reason.

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

Required invalid examples:

```text
d:personal d:work
```

```text
c:okular c:krusader
```

```text
g:half_left g:half_right
```

```text
le:pos1 le:pos2
```

```text
unknown:value
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

### `GEOM`

Tests should verify:

1. Profile name is valid.
2. `x`, `y`, `w`, and `h` exist.
3. Values are integers.
4. Width and height are positive.
5. Duplicate profile names are detected.

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

## Renderer tests

Renderer tests should prove that generated Lua is stable and readable.

Required behavior:

1. Render each managed block in deterministic order where practical.
2. Keep valid Lua syntax.
3. Preserve unmanaged Lua program logic.
4. Avoid duplicate workspace keys.
5. Preserve or regenerate useful comments where practical.

Test approach:

1. Parse fixture.
2. Render without changes.
3. Parse rendered output again.
4. Confirm parsed model is equivalent.

This is more important than byte-for-byte output matching.

## Dry-run tests

Before real saving exists, the tool should support a dry-run path.

Possible command:

```bash
d2wc validate --config tests/fixtures/d2wc-current.lua
```

Possible command:

```bash
d2wc render --config tests/fixtures/d2wc-current.lua --stdout
```

Possible command:

```bash
d2wc plan-add-geom --config tests/fixtures/d2wc-current.lua --name test_left --x 0 --y 0 --w 1200 --h 900
```

The exact command names can change, but dry-run behavior should exist before real writes.

## Backup and write tests

Backup/write tests must use temporary directories.

Required tests:

1. Backup is created before write.
2. Backup name includes timestamp or unique suffix.
3. New content is written to a temporary file first.
4. Target file is replaced only after successful write.
5. Failed validation prevents any write.
6. Failed write leaves previous file intact where possible.

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

GTK proof should happen after parser and validator proof, not before.

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

The test output should be inspectable before it is connected to save workflows.

## Left-edge correction tests

Left-edge tests should use the method described in `docs/left-edge-correction-testing.md`.

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

Only after this should post-resize configurator entry be enabled.

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
4. Backup/write tests pass in temporary directories.
5. Dry-run preview works.
6. User explicitly selects a real config file or initializes one.
7. Backup location is writable.
8. Save preview is shown.

The default behavior during early development should be read-only or test-file-only.

## Suggested test tooling

The likely test stack is:

1. `pytest` for Python tests.
2. Temporary directories through pytest fixtures.
3. Plain fixture files under `tests/fixtures/`.
4. Manual test notes for desktop behavior.

The final tool choice can be confirmed when the Python package skeleton is created.

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

## Continuous integration later

CI can be added after the Python package skeleton exists.

First CI checks:

1. Run unit tests.
2. Run parser tests against fixtures.
3. Run validation tests.
4. Run render round-trip tests.

Desktop behavior will remain manual until a suitable test environment is designed.

## Immediate test priorities

The first real implementation branch should prioritize tests in this order:

1. Parser can find managed blocks.
2. Rule grammar validation.
3. Section validation.
4. Renderer round-trip.
5. Backup/write to temporary directory.
6. CLI dry-run commands.
7. GTK window proof.
8. Active-window capture proof.

No UI save workflow should be built before the parser, validator, renderer, and backup tests exist.
