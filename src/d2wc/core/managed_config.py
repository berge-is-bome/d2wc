"""Managed configuration extraction and canonical rendering."""

from __future__ import annotations

from dataclasses import dataclass

from d2wc.core.lua_blocks import ManagedBlock
from d2wc.core.section_validation import extract_active_rule_strings, extract_geometry_profile_entries


@dataclass(frozen=True)
class GeometryProfile:
    """One named geometry profile."""

    name: str
    x: int
    y: int
    w: int
    h: int


@dataclass(frozen=True)
class WorkspaceRoute:
    """One workspace route list."""

    workspace: int
    rules: tuple[str, ...]


@dataclass(frozen=True)
class ManagedConfig:
    """Structured managed configuration sections."""

    exclude: tuple[str, ...]
    pin: tuple[str, ...]
    workspace_routes: tuple[WorkspaceRoute, ...]
    geom: tuple[GeometryProfile, ...]
    workspace_placement: tuple[str, ...]
    left_edge_correction: tuple[str, ...]


def extract_managed_config(blocks: dict[str, ManagedBlock]) -> ManagedConfig:
    """Extract structured values from validated managed blocks."""

    return ManagedConfig(
        exclude=tuple(extract_active_rule_strings(blocks["EXCLUDE"].text)),
        pin=tuple(extract_active_rule_strings(blocks["PIN"].text)),
        workspace_routes=tuple(extract_workspace_routes(blocks["WORKSPACE_ROUTES"].text)),
        geom=tuple(extract_geometry_profiles(blocks["GEOM"])),
        workspace_placement=tuple(extract_active_rule_strings(blocks["WORKSPACE_PLACEMENT"].text)),
        left_edge_correction=tuple(extract_active_rule_strings(blocks["LEFT_EDGE_CORRECTION"].text)),
    )


def render_managed_config(
    config: ManagedConfig,
    original_blocks: dict[str, ManagedBlock] | None = None,
) -> dict[str, str]:
    """Render all managed sections to canonical Lua block text.

    When original blocks are supplied, user comments inside managed sections are
    preserved. That is the normal path for dry-run rendering from an existing
    Lua file.
    """

    if original_blocks is None:
        return {
            "EXCLUDE": render_rule_list_block("EXCLUDE", config.exclude),
            "PIN": render_rule_list_block("PIN", config.pin),
            "WORKSPACE_ROUTES": render_workspace_routes_block(config.workspace_routes),
            "GEOM": render_geom_block(config.geom),
            "WORKSPACE_PLACEMENT": render_rule_list_block("WORKSPACE_PLACEMENT", config.workspace_placement),
            "LEFT_EDGE_CORRECTION": render_rule_list_block("LEFT_EDGE_CORRECTION", config.left_edge_correction),
        }

    return {
        "EXCLUDE": render_rule_list_block_preserving_comments("EXCLUDE", original_blocks["EXCLUDE"].text),
        "PIN": render_rule_list_block_preserving_comments("PIN", original_blocks["PIN"].text),
        "WORKSPACE_ROUTES": original_blocks["WORKSPACE_ROUTES"].text,
        "GEOM": render_geom_block_preserving_comments(config.geom, original_blocks["GEOM"].text),
        "WORKSPACE_PLACEMENT": render_rule_list_block_preserving_comments(
            "WORKSPACE_PLACEMENT", original_blocks["WORKSPACE_PLACEMENT"].text
        ),
        "LEFT_EDGE_CORRECTION": render_rule_list_block_preserving_comments(
            "LEFT_EDGE_CORRECTION", original_blocks["LEFT_EDGE_CORRECTION"].text
        ),
    }


def render_rule_list_block(name: str, rules: tuple[str, ...]) -> str:
    """Render a simple Lua list of rule strings."""

    lines = [f"local {name} = {{"]
    for rule in rules:
        lines.append(f'  "{_escape_lua_string(rule)}",')
    lines.append("}")
    return "\n".join(lines)


def render_rule_list_block_preserving_comments(name: str, block_text: str) -> str:
    """Render a rule list while preserving user comments and blank lines."""

    lines = block_text.splitlines()
    if len(lines) < 2:
        return block_text

    entries: list[tuple[str, str | None]] = []
    for line in lines[1:-1]:
        active, comment = _split_lua_comment(line)
        rules = extract_active_rule_strings(active)
        if not rules:
            entries.append((line.rstrip(), None))
            continue

        left = f'  "{_escape_lua_string(rules[0])}",'
        entries.append((left, comment.strip() if comment else ""))

    max_left_width = max((len(left) for left, comment in entries if comment is not None), default=0)

    rendered = [f"local {name} = {{"]
    for left, comment in entries:
        if comment is None:
            rendered.append(left)
        elif comment:
            rendered.append(_append_aligned_comment(left, comment, max_left_width))
        else:
            rendered.append(left)
    rendered.append("}")
    return "\n".join(rendered)


def render_workspace_routes_block(routes: tuple[WorkspaceRoute, ...]) -> str:
    """Render WORKSPACE_ROUTES."""

    lines = ["local WORKSPACE_ROUTES = {"]
    for route in routes:
        rendered_rules = " ".join(f'"{_escape_lua_string(rule)}",' for rule in route.rules)
        lines.append(f"  [{route.workspace}] = {{ {rendered_rules} }},")
    lines.append("}")
    return "\n".join(lines)


def render_geom_block(profiles: tuple[GeometryProfile, ...]) -> str:
    """Render GEOM profiles with aligned numeric columns."""

    lines = ["local GEOM = {"]
    lines.extend(_render_geom_profile_lines(profiles))
    lines.append("}")
    return "\n".join(lines)


def render_geom_block_preserving_comments(profiles: tuple[GeometryProfile, ...], block_text: str) -> str:
    """Render GEOM while preserving comments and applying profile additions/removals."""

    lines = block_text.splitlines()
    if len(lines) < 2:
        return block_text

    profile_map = {profile.name: profile for profile in profiles}
    rendered_names: set[str] = set()
    max_left_width = max((len(_render_geom_profile_line(profile, profiles)) for profile in profiles), default=0)

    rendered = ["local GEOM = {"]
    for line in lines[1:-1]:
        active, comment = _split_lua_comment(line)
        name = _geom_profile_name_from_line(active)
        if name is None:
            rendered.append(line.rstrip())
            continue
        if name not in profile_map:
            continue

        left = _render_geom_profile_line(profile_map[name], profiles)
        rendered_names.add(name)
        if comment:
            rendered.append(_append_aligned_comment(left, comment.strip(), max_left_width))
        else:
            rendered.append(left)

    for profile in profiles:
        if profile.name not in rendered_names:
            rendered.append(_render_geom_profile_line(profile, profiles))

    rendered.append("}")
    return "\n".join(rendered)


def extract_geometry_profiles(block: ManagedBlock) -> list[GeometryProfile]:
    """Extract ordered geometry profiles from a GEOM block."""

    profiles: list[GeometryProfile] = []
    for name, fields in extract_geometry_profile_entries(block.text):
        profiles.append(
            GeometryProfile(
                name=name,
                x=_require_int(fields["x"]),
                y=_require_int(fields["y"]),
                w=_require_int(fields["w"]),
                h=_require_int(fields["h"]),
            )
        )
    return profiles


def extract_workspace_routes(block_text: str) -> list[WorkspaceRoute]:
    """Extract ordered WORKSPACE_ROUTES entries."""

    routes: list[WorkspaceRoute] = []
    text = _strip_lua_comments(block_text)
    index = 0
    while index < len(text):
        key_index = text.find("[", index)
        if key_index == -1:
            break
        close_key_index = text.find("]", key_index)
        if close_key_index == -1:
            break

        key_text = text[key_index + 1 : close_key_index].strip()
        try:
            workspace = int(key_text)
        except ValueError:
            index = close_key_index + 1
            continue

        open_brace_index = text.find("{", close_key_index)
        if open_brace_index == -1:
            break
        close_brace_index = _find_matching_brace(text, open_brace_index)
        if close_brace_index is None:
            break

        route_body = text[open_brace_index : close_brace_index + 1]
        routes.append(
            WorkspaceRoute(
                workspace=workspace,
                rules=tuple(extract_active_rule_strings(route_body)),
            )
        )
        index = close_brace_index + 1

    return routes


def _render_geom_profile_lines(profiles: tuple[GeometryProfile, ...]) -> list[str]:
    return [_render_geom_profile_line(profile, profiles) for profile in profiles]


def _render_geom_profile_line(profile: GeometryProfile, all_profiles: tuple[GeometryProfile, ...]) -> str:
    name_width = max(22, max((len(item.name) for item in all_profiles), default=0))
    x_width = max(4, max((len(str(item.x)) for item in all_profiles), default=0))
    y_width = max(4, max((len(str(item.y)) for item in all_profiles), default=0))
    w_width = max(4, max((len(str(item.w)) for item in all_profiles), default=0))
    h_width = max(4, max((len(str(item.h)) for item in all_profiles), default=0))

    return (
        "  "
        f"{profile.name:<{name_width}} = "
        "{ "
        f"x = {profile.x:<{x_width}}, "
        f"y = {profile.y:<{y_width}}, "
        f"w = {profile.w:<{w_width}}, "
        f"h = {profile.h:<{h_width}} "
        "},"
    )


def _append_aligned_comment(left: str, comment: str, max_left_width: int) -> str:
    return left + (" " * (max_left_width - len(left) + 5)) + comment


def _strip_lua_comments(text: str) -> str:
    return "\n".join(line.split("--", 1)[0] for line in text.splitlines())


def _split_lua_comment(line: str) -> tuple[str, str]:
    marker = line.find("--")
    if marker == -1:
        return line, ""
    return line[:marker], line[marker:]


def _geom_profile_name_from_line(line: str) -> str | None:
    if "=" not in line or "{" not in line:
        return None
    candidate = line.split("=", 1)[0].strip()
    if not candidate or candidate[0].isdigit() or not candidate.replace("_", "").isalnum():
        return None
    return candidate.lower()


def _find_matching_brace(text: str, open_brace_index: int) -> int | None:
    depth = 0
    for index in range(open_brace_index, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
    return None


def _require_int(value: int | str) -> int:
    if not isinstance(value, int):
        raise TypeError(f"expected integer value, got {value!r}")
    return value


def _escape_lua_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
