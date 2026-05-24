# Configurator Notification Settings

## Current behavior

Successful row actions in the GTK configurator use a temporary in-window toast notification instead of a blocking dialog.

Current defaults:

1. Success message text is intentionally short:

```text
Operation completed successfully.
```

2. The toast is compact.
3. The toast is translucent with 50% opacity.
4. The toast closes automatically after a short timeout.
5. The toast can also be dismissed manually.
6. Error and validation messages still use blocking dialogs because those require deliberate user attention.

## Future configuration menu

A future `Menu -> Configure` workflow should allow users to adjust notification behavior without editing code.

Candidate settings:

1. Enable or disable success toasts.
2. Toast opacity.
3. Toast timeout duration.
4. Toast position.
5. Toast verbosity:
   1. compact success message only
   2. success message plus action name
   3. detailed output including target path and backup archive
6. Whether successful operations should ever use a blocking dialog.

## Safety note

Detailed write information should remain available somewhere for debugging and recovery, but it does not need to interrupt normal successful edits. Errors should continue to show enough detail to diagnose the failed action.
