# Configurator Options

The configurator options screen controls how `d2wc` behaves.

Open it from the main configurator window:

```text
Menu -> Configure
```

The options screen has two sections:

1. `Behavior`
2. `Notifications`

Use `Back` to return to the normal rule editor.

## Behavior

![d2wc Configure Behavior screen](images/d2wc-configure-behavior.png)

`Behavior` controls what happens when Devilspie2 sees an application window that is not already handled by your `d2wc` managed rules.

### Automatically open d2wc for unconfigured windows

When this option is enabled, Devilspie2 opens `d2wc` automatically for new application windows that do not already match a managed rule.

This is useful during initial setup because `d2wc` can appear when an application opens, and offer a way to configure it.

### Entry point

This option controls what `d2wc` opens when you have selected `d2wc` to launch automatically.

Available choices:

1. `Open configurator directly`
2. `Show Cancel/Configure overlay button`

#### Open configurator directly

This opens the `configurator` when an unconfigured window appears.

#### Show Cancel/Configure overlay button

This shows a small overlay button at the bottom right hand corner of the window, and automatically places the mouse on the `Cancel` button. This option is less intrusive during initial configuration.

![d2wc Configure Notifications screen](images/d2wc-configure-overlay-button.png)

Use this when you want the fastest setup workflow.

The prompt has two buttons:

1. `Cancel`
2. `Configure`

Choose `Cancel` when you do not want to configure that window.

Choose `Configure` to open the full configurator for that window.

## Notifications

![d2wc Configure Notifications screen](images/d2wc-configure-notifications.png)

`Notifications` controls the small success messages shown by the configurator after actions complete.

### Toast timeout

`Toast timeout` controls how long success messages stay visible.

### Toast opacity

`Toast opacity` controls how solid or transparent success messages appear.
