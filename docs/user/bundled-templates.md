# Bundled Templates

`d2wc` ships with two bundled managed Lua templates so a new install can start with window sizes that better match the user's display.

The templates are included because window placement uses real screen measurements. A layout that feels comfortable on a large 2160 display can be far too large on a 1080 display. Windows may open too wide, too tall, or too far across the screen for the smaller display.

The bundled choices are:

1. `2160`
2. `1080`

The `1080` template is based on the `2160` template, but scaled down by half. That gives 1080 users a practical first layout instead of starting with windows sized for a much larger display.

The `1080` template is still only a starting point. Different desktops, themes, window borders, font sizes, and display layouts can make the same values feel slightly different from one system to another. The goal is not to make every window perfect immediately. The goal is to make the first install usable, then let the user fine-tune from there.

After installation, geometry profiles can be adjusted in the configurator:

```text
Window geometry
```

Those profiles can then be linked to windows through:

```text
Workspace placement
```
