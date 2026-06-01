# Bundled Templates

`d2wc` ships with two bundled managed Lua templates so a new install starts with window sizes that are closer to the user's display size.

Window geometry profiles store real screen coordinates and real width and height values. A layout that feels reasonable on a 2160 display can be much too large on a 1080 display.

The bundled choices are:

1. `2160`: the normal default template.
2. `1080`: a smaller default template for 1080 displays.

The `1080` template is a best-guess starting point created by applying a `0.5` scaling factor to the geometry values from the `2160` template.

The `1080` template is not expected to be perfect for every desktop, panel layout, font scale, or window decoration setup. It gives first-time users a safer starting layout on smaller displays.

After installation, geometry profiles can be adjusted in the configurator:

```text
Window geometry
```

Those profiles can then be linked to windows through:

```text
Workspace placement
```
