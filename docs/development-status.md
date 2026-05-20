# d2wc Development Status

## Current PR

Current active PR:

```text
PR: #2
Branch: configurator-core-proof
Previous confirmed baseline: c2371920ac834144a8052f47091a3e7596ff3ae2
Current confirmed head: 2e783a1a827d607400d01a9b9209e228cfba9ce3
Status: local verification passed
```

## Latest confirmed local verification

Verification reported on 2026-05-20:

```bash
PYTHONPATH=src python -m d2wc validate --config src/d2wc.lua
PYTHONPATH=src python -m d2wc render --config src/d2wc.lua --stdout > /tmp/d2wc-rendered.lua
PYTHONPATH=src python -m d2wc validate --config /tmp/d2wc-rendered.lua
PYTHONPATH=src python -m pytest
```

Result:

```text
src/d2wc.lua validates successfully.
Rendered /tmp/d2wc-rendered.lua validates successfully.
59 pytest tests passed.
Test environment: Linux, Python 3.14.4, pytest 8.3.5.
```

This four-command set is the standard renderer verification path. It should be used whenever renderer behavior changes, because it confirms both the original Lua source and the rendered output validate cleanly.

## Latest renderer changes

The latest renderer patch confirms these behaviors:

1. Right-side comments in managed rule-list sections are aligned using the longest rendered left-side entry plus 5 spaces.
2. Pure note comments are preserved.
3. Blank separator lines are preserved.
4. `GEOM` `x`, `y`, `w`, and `h` numeric columns have a minimum width of 4.
5. `GEOM` right-side comments are aligned using the longest rendered `GEOM` left-side entry plus 5 spaces.
6. Renderer expectations in the test suite were updated with the code change.

## Current safe capability

The current Python core proof supports:

1. Source-checkout CLI execution.
2. Read-only validation of managed Lua blocks.
3. Dry-run rendering to stdout.
4. Parser and validator tests for managed Lua sections.
5. Renderer round-trip tests.
6. Backup path helper tests.
7. Runtime settings validation tests.
8. Split-profile generation tests.
9. Duplicate and shadow validation tests.

The tool still does not write to a real user configuration file.

## Next practical work

The next practical step is to close out PR #2 as the read-only core proof once the PR description is updated and the branch is ready for review.

After PR #2 is merged, the next implementation branch should focus on safe save mechanics before UI work:

1. Define the file write safety contract.
2. Render to temporary file first.
3. Validate rendered content before replacement.
4. Create a timestamped backup before replacing the target.
5. Replace the target only after all validation and backup steps succeed.
6. Add tests that use temporary directories only.
7. Keep real user config writes disabled until the safety gates are proven.

GTK UI work should remain deferred until parser, validator, renderer, and safe save behavior are all covered by tests.
