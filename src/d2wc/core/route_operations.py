"""WORKSPACE_ROUTES editing operations."""

from __future__ import annotations

from dataclasses import dataclass

from d2wc.core.lua_blocks import MANAGED_BLOCK_NAMES, ManagedBlockParser
from d2wc.core.managed_config import ManagedConfig, WorkspaceRoute, extract_managed_config
from d2wc.core.rendering import RenderValidationError
from d2wc.core.rule_grammar import RuleParseError, parse_prefixed_rule
from d2wc.core.validation import ValidationResult, validate_managed_blocks


class RouteOperationError(ValueError):
    """Raised when a route edit cannot be applied."""


class RouteRuleExistsError(RouteOperationError):
    """Raised when adding a duplicate route target."""


class RouteRuleNotFoundError(RouteOperationError):
    """Raised when modifying or deleting a missing route rule."""


@dataclass(frozen=True)
class RouteEditResult:
    """Result of applying a WORKSPACE_ROUTES edit in memory."""

    source: str
    validation: ValidationResult
    workspace: int
    rule: str
    operation: str


@dataclass(frozen=True)
class RouteModifyResult:
    """Result of modifying a WORKSPACE_ROUTES rule in memory."""

    source: str
    validation: ValidationResult
    old_workspace: int
    new_workspace: int
    old_rule: str
    new_rule: str


def add_route_rule_to_source(source: str, workspace: int, rule_text: str) -> RouteEditResult:
    """Add one WORKSPACE_ROUTES rule to Lua source."""

    _validate_workspace(workspace)
    normalized_rule = _normalize_route_rule(rule_text)
    parsed, config = _parse_valid_config(source)
    updated_routes = _add_rule(config.workspace_routes, workspace, normalized_rule)
    rendered_source, rendered_validation = _render_updated_source(source, parsed.blocks, config, updated_routes)

    return RouteEditResult(
        source=rendered_source,
        validation=rendered_validation,
        workspace=workspace,
        rule=normalized_rule,
        operation="add",
    )


def modify_route_rule_in_source(
    source: str,
    old_rule_text: str,
    new_workspace: int,
    new_rule_text: str,
) -> RouteModifyResult:
    """Modify one WORKSPACE_ROUTES rule in Lua source.

    Matching is based on parsed rule meaning, not token order. The rendered rule
    is written in canonical prefix order.
    """

    _validate_workspace(new_workspace)
    old_rule = _normalize_route_rule(old_rule_text)
    new_rule = _normalize_route_rule(new_rule_text)
    parsed, config = _parse_valid_config(source)
    updated_routes, old_workspace = _modify_rule(config.workspace_routes, old_rule, new_workspace, new_rule)
    rendered_source, rendered_validation = _render_updated_source(source, parsed.blocks, config, updated_routes)

    return RouteModifyResult(
        source=rendered_source,
        validation=rendered_validation,
        old_workspace=old_workspace,
        new_workspace=new_workspace,
        old_rule=old_rule,
        new_rule=new_rule,
    )


def delete_route_rule_from_source(source: str, rule_text: str) -> RouteEditResult:
    """Delete one WORKSPACE_ROUTES rule from Lua source.

    Matching is based on parsed rule meaning, not token order.
    """

    normalized_rule = _normalize_route_rule(rule_text)
    parsed, config = _parse_valid_config(source)
    updated_routes, old_workspace = _delete_rule(config.workspace_routes, normalized_rule)
    rendered_source, rendered_validation = _render_updated_source(source, parsed.blocks, config, updated_routes)

    return RouteEditResult(
        source=rendered_source,
        validation=rendered_validation,
        workspace=old_workspace,
        rule=normalized_rule,
        operation="delete",
    )


def _parse_valid_config(source: str):
    parsed = ManagedBlockParser().parse(source)
    validation = validate_managed_blocks(parsed.blocks)
    if not validation.ok:
        raise RenderValidationError(validation)
    return parsed, extract_managed_config(parsed.blocks)


def _render_updated_source(
    source: str,
    blocks: dict[str, object],
    config: ManagedConfig,
    updated_routes: tuple[WorkspaceRoute, ...],
) -> tuple[str, ValidationResult]:
    updated_config = ManagedConfig(
        exclude=config.exclude,
        pin=config.pin,
        workspace_routes=_sort_routes(updated_routes),
        geom=config.geom,
        workspace_placement=config.workspace_placement,
        left_edge_correction=config.left_edge_correction,
    )

    route_block = _render_workspace_routes_block_preserving_comments(
        updated_config.workspace_routes,
        blocks["WORKSPACE_ROUTES"].text,
    )
    rendered_source = _replace_managed_block(source, blocks, "WORKSPACE_ROUTES", route_block)

    rendered_parsed = ManagedBlockParser().parse(rendered_source)
    rendered_validation = validate_managed_blocks(rendered_parsed.blocks)
    if not rendered_validation.ok:
        raise RenderValidationError(rendered_validation)

    return rendered_source, rendered_validation


def _add_rule(routes: tuple[WorkspaceRoute, ...], workspace: int, new_rule: str) -> tuple[WorkspaceRoute, ...]:
    _ensure_target_available(routes, new_rule)
    return _append_rule_to_workspace(routes, workspace, new_rule)


def _modify_rule(
    routes: tuple[WorkspaceRoute, ...],
    old_rule: str,
    new_workspace: int,
    new_rule: str,
) -> tuple[tuple[WorkspaceRoute, ...], int]:
    old_signature = _rule_signature(old_rule)
    new_signature = _rule_signature(new_rule)
    updated_routes: list[WorkspaceRoute] = []
    found = False
    placed = False
    old_workspace: int | None = None

    for route in routes:
        updated_rules: list[str] = []
        for existing_rule in route.rules:
            existing_signature = _rule_signature(existing_rule)
            if existing_signature == old_signature:
                found = True
                old_workspace = route.workspace
                if route.workspace == new_workspace:
                    updated_rules.append(new_rule)
                    placed = True
                continue
            if existing_signature == new_signature:
                raise RouteRuleExistsError(f"route rule already exists for target: {_format_target(new_rule)}")
            updated_rules.append(existing_rule)

        if updated_rules:
            updated_routes.append(WorkspaceRoute(workspace=route.workspace, rules=tuple(updated_rules)))

    if not found or old_workspace is None:
        raise RouteRuleNotFoundError(f"route rule not found: {old_rule}")

    if not placed:
        updated_routes = list(_append_rule_to_workspace(tuple(updated_routes), new_workspace, new_rule))

    return _sort_routes(tuple(updated_routes)), old_workspace


def _delete_rule(routes: tuple[WorkspaceRoute, ...], rule: str) -> tuple[tuple[WorkspaceRoute, ...], int]:
    signature = _rule_signature(rule)
    updated_routes: list[WorkspaceRoute] = []
    found = False
    old_workspace: int | None = None

    for route in routes:
        updated_rules: list[str] = []
        for existing_rule in route.rules:
            if _rule_signature(existing_rule) == signature:
                found = True
                old_workspace = route.workspace
                continue
            updated_rules.append(existing_rule)
        if updated_rules:
            updated_routes.append(WorkspaceRoute(workspace=route.workspace, rules=tuple(updated_rules)))

    if not found or old_workspace is None:
        raise RouteRuleNotFoundError(f"route rule not found: {rule}")

    return _sort_routes(tuple(updated_routes)), old_workspace


def _append_rule_to_workspace(
    routes: tuple[WorkspaceRoute, ...],
    workspace: int,
    rule: str,
) -> tuple[WorkspaceRoute, ...]:
    updated_routes: list[WorkspaceRoute] = []
    appended = False
    for route in routes:
        if route.workspace == workspace:
            updated_routes.append(WorkspaceRoute(workspace=route.workspace, rules=(*route.rules, rule)))
            appended = True
        else:
            updated_routes.append(route)
    if not appended:
        updated_routes.append(WorkspaceRoute(workspace=workspace, rules=(rule,)))
    return _sort_routes(tuple(updated_routes))


def _ensure_target_available(routes: tuple[WorkspaceRoute, ...], new_rule: str) -> None:
    new_signature = _rule_signature(new_rule)
    for route in routes:
        for existing_rule in route.rules:
            if _rule_signature(existing_rule) == new_signature:
                raise RouteRuleExistsError(f"route rule already exists for target: {_format_target(new_rule)}")


def _render_workspace_routes_block_preserving_comments(
    routes: tuple[WorkspaceRoute, ...],
    block_text: str,
) -> str:
    lines = block_text.splitlines()
    if len(lines) < 2:
        return _render_workspace_routes_block(routes)

    route_comments: dict[int, str] = {}
    route_extra_lines: dict[int, list[str]] = {}
    prefix_lines: list[str] = []
    tail_marker_lines: list[str] = []
    current_workspace: int | None = None
    seen_route = False

    for line in lines[1:-1]:
        if _is_add_more_marker(line):
            tail_marker_lines.append(line.rstrip())
            continue

        active, comment = _split_lua_comment(line)
        workspace = _workspace_key_from_line(active)
        if workspace is not None:
            current_workspace = workspace
            seen_route = True
            if comment:
                trailing_spaces = len(active) - len(active.rstrip(" "))
                route_comments[workspace] = (" " * trailing_spaces) + comment
            continue

        stripped = line.strip()
        if not stripped:
            continue

        if not seen_route:
            prefix_lines.append(line.rstrip())
            continue

        if current_workspace is None:
            continue

        if _is_route_closing_comment(active, comment):
            trailing_spaces = len(active) - len(active.rstrip(" "))
            route_comments[current_workspace] = (" " * trailing_spaces) + comment
            current_workspace = None
            continue

        if _is_standalone_lua_comment(line):
            route_extra_lines.setdefault(current_workspace, []).append(line.rstrip())

    rendered = ["local WORKSPACE_ROUTES = {"]
    rendered.extend(prefix_lines)
    if prefix_lines and routes:
        rendered.append("")

    for index, route in enumerate(_sort_routes(routes)):
        if index > 0:
            rendered.append("")
        left = _render_workspace_route_line(route)
        rendered.append(left + route_comments.get(route.workspace, ""))
        rendered.extend(route_extra_lines.get(route.workspace, []))

    rendered.extend(tail_marker_lines)
    rendered.append("}")
    return "\n".join(rendered)


def _render_workspace_routes_block(routes: tuple[WorkspaceRoute, ...]) -> str:
    lines = ["local WORKSPACE_ROUTES = {"]
    for index, route in enumerate(_sort_routes(routes)):
        if index > 0:
            lines.append("")
        lines.append(_render_workspace_route_line(route))
    lines.append("}")
    return "\n".join(lines)


def _render_workspace_route_line(route: WorkspaceRoute) -> str:
    rendered_rules = " ".join(f'"{_escape_lua_string(rule)}",' for rule in route.rules)
    return f"  [{route.workspace}] = {{ {rendered_rules} }},"


def _sort_routes(routes: tuple[WorkspaceRoute, ...]) -> tuple[WorkspaceRoute, ...]:
    return tuple(sorted(routes, key=lambda route: route.workspace))


def _is_route_closing_comment(active: str, comment: str) -> bool:
    return bool(comment) and active.strip().startswith("}")


def _is_standalone_lua_comment(line: str) -> bool:
    return line.lstrip().startswith("--")


def _normalize_route_rule(rule_text: str) -> str:
    try:
        rule = parse_prefixed_rule(rule_text)
    except RuleParseError as exc:
        raise RouteOperationError(str(exc)) from exc

    if not rule.has_target:
        raise RouteOperationError(f"route rule must include d: or c:: {rule_text}")
    if rule.geometry_profile is not None:
        raise RouteOperationError(f"route rule must not include g:: {rule_text}")
    if rule.left_edge_mode is not None:
        raise RouteOperationError(f"route rule must not include le:: {rule_text}")

    parts: list[str] = []
    if rule.domain is not None:
        parts.append(f"d:{rule.domain}")
    if rule.class_name is not None:
        parts.append(f"c:{rule.class_name}")
    return " ".join(parts)


def _validate_workspace(workspace: int) -> None:
    if workspace < 1:
        raise RouteOperationError(f"workspace must be at least 1: {workspace}")


def _rule_signature(rule_text: str) -> tuple[str | None, str | None]:
    rule = parse_prefixed_rule(rule_text)
    return rule.domain, rule.class_name


def _format_target(rule_text: str) -> str:
    rule = parse_prefixed_rule(rule_text)
    parts: list[str] = []
    if rule.domain is not None:
        parts.append(f"d:{rule.domain}")
    if rule.class_name is not None:
        parts.append(f"c:{rule.class_name}")
    return " ".join(parts)


def _workspace_key_from_line(line: str) -> int | None:
    stripped = line.strip()
    if not stripped.startswith("[") or "]" not in stripped:
        return None
    key_text, after_key = stripped[1:].split("]", 1)
    if "=" not in after_key or "{" not in after_key:
        return None
    try:
        return int(key_text.strip())
    except ValueError:
        return None


def _replace_managed_block(source: str, blocks: dict[str, object], name: str, replacement: str) -> str:
    block = blocks[name]
    return source[: block.start_index] + replacement + source[block.end_index :]


def _replace_managed_blocks(source: str, blocks: dict[str, object], replacements: dict[str, str]) -> str:
    rendered = source
    for name in reversed(MANAGED_BLOCK_NAMES):
        block = blocks[name]
        replacement = replacements[name]
        rendered = rendered[: block.start_index] + replacement + rendered[block.end_index :]
    return rendered


def _is_add_more_marker(line: str) -> bool:
    return line.strip().lower() == "-- add more here"


def _split_lua_comment(line: str) -> tuple[str, str]:
    marker = line.find("--")
    if marker == -1:
        return line, ""
    return line[:marker], line[marker:]


def _escape_lua_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
