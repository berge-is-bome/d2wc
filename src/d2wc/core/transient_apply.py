"""Transient one-rule Devilspie2 apply helper.

This module is intentionally not a Devilspie2 process manager.  It builds a
short-lived, minimal d2wc managed config for the one Add/Modify action that was
just saved, starts only that transient process in its own process group, waits
briefly for Devilspie2 to consume the folder, then terminates and reaps exactly
that process group.
"""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
from typing import Callable, Protocol

from d2wc.core.lua_blocks import MANAGED_BLOCK_NAMES, ManagedBlockParser
from d2wc.core.managed_config import (
    GeometryProfile,
    ManagedConfig,
    WorkspaceRoute,
    extract_managed_config,
    render_managed_config,
)
from d2wc.core.rendering import RenderValidationError
from d2wc.core.rule_grammar import PrefixedRule, RuleParseError, parse_prefixed_rule
from d2wc.core.validation import validate_managed_blocks

TRANSIENT_APPLY_SETTLE_SECONDS = 1.0
TRANSIENT_APPLY_TERMINATE_TIMEOUT_SECONDS = 1.0
TRANSIENT_CONFIG_FILENAME = "d2wc.lua"


class _ActionRequest(Protocol):
    section: str
    operation: str
    rule: str
    existing_rule: str
    workspace: int | None


class _Process(Protocol):
    pid: int

    def wait(self, timeout: float | None = None) -> int: ...


@dataclass(frozen=True)
class TransientApplyResult:
    """Result of a transient apply attempt."""

    attempted: bool
    applied: bool
    warning: str = ""
    config_source: str | None = None


@dataclass(frozen=True)
class TransientApplyPlan:
    """Minimal source for a transient apply and the selected action metadata."""

    source: str
    section: str
    rule: str


TempDirFactory = Callable[[], AbstractContextManager[str]]
CommandResolver = Callable[[str], str | None]
SubprocessLauncher = Callable[..., _Process]
Sleep = Callable[[float], None]
KillProcessGroup = Callable[[int, int], None]


def apply_transient_rule_after_save(
    config_path: Path,
    request: _ActionRequest,
    *,
    command: str = "devilspie2",
    temp_dir_factory: TempDirFactory | None = None,
    command_resolver: CommandResolver | None = None,
    subprocess_launcher: SubprocessLauncher | None = None,
    sleep: Sleep | None = None,
    kill_process_group: KillProcessGroup | None = None,
    settle_timeout: float = TRANSIENT_APPLY_SETTLE_SECONDS,
    terminate_timeout: float = TRANSIENT_APPLY_TERMINATE_TIMEOUT_SECONDS,
) -> TransientApplyResult:
    """Build and run a one-rule transient Devilspie2 config after a save.

    Missing or failed Devilspie2 launch returns a warning instead of raising so
    callers can keep the already-successful managed config save successful.
    """

    try:
        plan = build_transient_apply_plan(config_path, request)
    except NoTransientApplyNeeded:
        return TransientApplyResult(attempted=False, applied=False)
    except (OSError, ValueError, RenderValidationError, RuleParseError) as exc:
        return TransientApplyResult(attempted=False, applied=False, warning=f"Runtime apply warning: {exc}")

    resolver = command_resolver or shutil.which
    executable = resolver(command)
    if executable is None:
        return TransientApplyResult(
            attempted=True,
            applied=False,
            warning=f"Runtime apply warning: could not find {command}; saved config but did not apply it now",
            config_source=plan.source,
        )

    launcher = subprocess_launcher or subprocess.Popen
    temp_factory = temp_dir_factory or tempfile.TemporaryDirectory
    sleep_func = sleep or _default_sleep
    killpg = kill_process_group or os.killpg

    try:
        with temp_factory() as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            transient_config_path = temp_dir / TRANSIENT_CONFIG_FILENAME
            transient_config_path.write_text(plan.source, encoding="utf-8")
            process = launcher(
                [executable, "--folder", str(temp_dir)],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                close_fds=True,
            )
            warning = _settle_terminate_and_reap(
                process,
                sleep=sleep_func,
                settle_timeout=settle_timeout,
                terminate_timeout=terminate_timeout,
                kill_process_group=killpg,
            )
            return TransientApplyResult(
                attempted=True,
                applied=not warning,
                warning=warning,
                config_source=plan.source,
            )
    except OSError as exc:
        return TransientApplyResult(
            attempted=True,
            applied=False,
            warning=f"Runtime apply warning: could not start {command}: {exc}",
            config_source=plan.source,
        )


def build_transient_apply_plan(config_path: Path, request: _ActionRequest) -> TransientApplyPlan:
    """Render a temporary d2wc config containing only the just-saved rule."""

    section = request.section.upper()
    operation = request.operation.lower()
    if section == "GEOM":
        raise NoTransientApplyNeeded()
    if operation not in {"add", "modify", "delete"}:
        raise NoTransientApplyNeeded()
    if operation == "delete" and section != "PIN":
        raise NoTransientApplyNeeded()

    rule = _rule_for_transient_request(request, operation)

    source = config_path.read_text(encoding="utf-8")
    parsed = ManagedBlockParser().parse(source)
    validation = validate_managed_blocks(parsed.blocks)
    if not validation.ok:
        raise RenderValidationError(validation)

    saved_config = extract_managed_config(parsed.blocks)
    minimal_config = _minimal_config_for_request(saved_config, section, operation, rule, request)
    rendered_blocks = render_managed_config(minimal_config)
    transient_source = _replace_managed_blocks(source, parsed.blocks, rendered_blocks)
    if operation == "delete" and section == "PIN":
        transient_source = _append_pin_delete_unpin(transient_source, saved_config, rule)

    transient_parsed = ManagedBlockParser().parse(transient_source)
    transient_validation = validate_managed_blocks(transient_parsed.blocks)
    if not transient_validation.ok:
        raise RenderValidationError(transient_validation)

    return TransientApplyPlan(source=transient_source, section=section, rule=rule)


class NoTransientApplyNeeded(Exception):
    """Raised internally when an action should not be transient-applied."""


def _rule_for_transient_request(request: _ActionRequest, operation: str) -> str:
    if operation == "delete":
        rule = request.existing_rule.strip() or request.rule.strip()
    else:
        rule = request.rule.strip()
    if not rule:
        raise ValueError("transient apply requires the saved rule text")
    return rule


def _minimal_config_for_request(
    saved_config: ManagedConfig,
    section: str,
    operation: str,
    rule: str,
    request: _ActionRequest,
) -> ManagedConfig:
    empty = ManagedConfig(
        exclude=(),
        pin=(),
        workspace_routes=(),
        geom=(),
        workspace_placement=(),
        left_edge_correction=(),
    )

    if section == "EXCLUDE":
        return ManagedConfig((rule,), empty.pin, empty.workspace_routes, empty.geom, empty.workspace_placement, empty.left_edge_correction)
    if section == "PIN":
        pin = () if operation == "delete" else (rule,)
        workspace_routes = _matching_workspace_routes_for_target(saved_config, rule) if operation == "delete" else empty.workspace_routes
        return ManagedConfig(empty.exclude, pin, workspace_routes, empty.geom, empty.workspace_placement, empty.left_edge_correction)
    if section == "WORKSPACE_ROUTES":
        if request.workspace is None:
            raise ValueError("transient WORKSPACE_ROUTES apply requires a workspace number")
        return ManagedConfig(
            empty.exclude,
            _matching_pin_rules_for_target(saved_config, rule),
            (WorkspaceRoute(request.workspace, (rule,)),),
            empty.geom,
            empty.workspace_placement,
            empty.left_edge_correction,
        )
    if section == "WORKSPACE_PLACEMENT":
        profile = _referenced_geometry_profile(saved_config, rule)
        return ManagedConfig(empty.exclude, empty.pin, empty.workspace_routes, profile, (rule,), empty.left_edge_correction)
    if section == "LEFT_EDGE_CORRECTION":
        placement_rule, profile = _left_edge_geometry_context(saved_config, rule)
        return ManagedConfig(empty.exclude, empty.pin, empty.workspace_routes, (profile,), (placement_rule,), (rule,))

    raise NoTransientApplyNeeded()


def _append_pin_delete_unpin(source: str, saved_config: ManagedConfig, deleted_rule: str) -> str:
    keep_pin_rules = _matching_pin_rules_for_target(saved_config, deleted_rule)
    cleanup = "\n".join(
        (
            "",
            "-- D2WC transient PIN delete cleanup",
            _render_lua_rule_list("D2WC_TRANSIENT_UNPIN", (deleted_rule,)),
            _render_lua_rule_list("D2WC_TRANSIENT_KEEP_PIN", keep_pin_rules),
            "if domain and list_rule_matches_window(D2WC_TRANSIENT_UNPIN, domain, cls)",
            "  and not list_rule_matches_window(D2WC_TRANSIENT_KEEP_PIN, domain, cls) then",
            "  local d2wc_transient_workspace = compute_workspace(domain, cls)",
            "  unpin_window()",
            "  if d2wc_transient_workspace and d2wc_transient_workspace > 0",
            "    and d2wc_transient_workspace <= get_workspace_count() then",
            "    set_window_workspace(d2wc_transient_workspace)",
            "  end",
            "end",
        )
    )
    return source.rstrip() + "\n" + cleanup + "\n"


def _matching_pin_rules_for_target(saved_config: ManagedConfig, target_rule: str) -> tuple[str, ...]:
    target = parse_prefixed_rule(target_rule)
    if not target.has_target:
        return ()

    matches: list[str] = []
    for pin_rule in saved_config.pin:
        pin_target = parse_prefixed_rule(pin_rule)
        if _rule_targets_can_match_same_window(target, pin_target):
            matches.append(pin_rule)

    return tuple(matches)


def _matching_workspace_routes_for_target(saved_config: ManagedConfig, target_rule: str) -> tuple[WorkspaceRoute, ...]:
    target = parse_prefixed_rule(target_rule)
    if not target.has_target:
        return ()

    matches: list[WorkspaceRoute] = []
    for route in saved_config.workspace_routes:
        rules = tuple(
            route_rule
            for route_rule in route.rules
            if _rule_targets_can_match_same_window(target, parse_prefixed_rule(route_rule))
        )
        if rules:
            matches.append(WorkspaceRoute(route.workspace, rules))

    return tuple(matches)


def _rule_targets_can_match_same_window(left: PrefixedRule, right: PrefixedRule) -> bool:
    if not left.has_target or not right.has_target:
        return False
    if left.domain is not None and right.domain is not None and left.domain != right.domain:
        return False
    if left.class_name is not None and right.class_name is not None:
        return _class_patterns_can_match_same_window(left.class_name, right.class_name)
    return True


def _class_patterns_can_match_same_window(left: str, right: str) -> bool:
    if left == right:
        return True
    if _class_match_rank(left, right) > 0 or _class_match_rank(right, left) > 0:
        return True
    if left.endswith("*") and _wildcard_class_pattern_can_overlap(left[:-1], right):
        return True
    if right.endswith("*") and _wildcard_class_pattern_can_overlap(right[:-1], left):
        return True
    return False


def _class_match_rank(rule_class: str, actual_class: str) -> int:
    if rule_class == actual_class:
        return 4

    tokens = _split_dotted(actual_class)
    if rule_class in tokens:
        return 3

    if rule_class.endswith("*"):
        prefix = rule_class[:-1]
        if actual_class.startswith(prefix):
            return 2
        for token in tokens:
            if token.startswith(prefix):
                return 1

    return 0


def _wildcard_class_pattern_can_overlap(wildcard_prefix: str, other_pattern: str) -> bool:
    if not wildcard_prefix:
        return True
    if other_pattern.endswith("*"):
        other_prefix = other_pattern[:-1]
        if not other_prefix:
            return True
        if wildcard_prefix.startswith(other_prefix) or other_prefix.startswith(wildcard_prefix):
            return True
        return _wildcard_prefix_tail_can_overlap(wildcard_prefix, other_prefix) or _wildcard_prefix_tail_can_overlap(
            other_prefix,
            wildcard_prefix,
        )

    if other_pattern.startswith(wildcard_prefix):
        return True
    if any(token.startswith(wildcard_prefix) for token in _split_dotted(other_pattern)):
        return True
    return _wildcard_prefix_tail_can_overlap(wildcard_prefix, other_pattern)


def _wildcard_prefix_tail_can_overlap(wildcard_prefix: str, other_pattern: str) -> bool:
    if "." not in wildcard_prefix:
        return False
    tail_prefix = wildcard_prefix.rsplit(".", 1)[-1]
    if not tail_prefix:
        return "." not in other_pattern
    return other_pattern.startswith(tail_prefix)


def _split_dotted(value: str) -> list[str]:
    return [part for part in value.split(".") if part]


def _render_lua_rule_list(name: str, rules: tuple[str, ...]) -> str:
    lines = [f"local {name} = {{"]
    for rule in rules:
        lines.append(f'  "{_escape_lua_string(rule)}",')
    lines.append("}")
    return "\n".join(lines)


def _escape_lua_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _referenced_geometry_profile(saved_config: ManagedConfig, rule: str) -> tuple[GeometryProfile, ...]:
    parsed_rule = parse_prefixed_rule(rule)
    if parsed_rule.geometry_profile is None:
        return ()
    return (_geometry_profile_by_name(saved_config, parsed_rule.geometry_profile),)


def _left_edge_geometry_context(saved_config: ManagedConfig, rule: str) -> tuple[str, GeometryProfile]:
    left_edge_rule = parse_prefixed_rule(rule)
    matches: list[tuple[str, GeometryProfile]] = []

    for placement_rule in saved_config.workspace_placement:
        parsed_placement = parse_prefixed_rule(placement_rule)
        if not _same_rule_target(left_edge_rule, parsed_placement):
            continue
        if parsed_placement.geometry_profile is None:
            continue
        profile = _geometry_profile_by_name(saved_config, parsed_placement.geometry_profile)
        if profile.x != 0:
            raise ValueError(
                "transient LEFT_EDGE_CORRECTION apply requires matching WORKSPACE_PLACEMENT "
                f"profile '{profile.name}' to have x = 0"
            )
        matches.append((placement_rule, profile))

    if not matches:
        raise ValueError(
            "transient LEFT_EDGE_CORRECTION apply could not find matching WORKSPACE_PLACEMENT rule "
            "with an x = 0 GEOM profile"
        )
    if len(matches) > 1:
        raise ValueError("transient LEFT_EDGE_CORRECTION apply found multiple matching WORKSPACE_PLACEMENT rules")

    return matches[0]


def _same_rule_target(left: PrefixedRule, placement: PrefixedRule) -> bool:
    return left.domain == placement.domain and left.class_name == placement.class_name


def _geometry_profile_by_name(saved_config: ManagedConfig, profile_name: str) -> GeometryProfile:
    for profile in saved_config.geom:
        if profile.name == profile_name:
            return profile
    raise ValueError(f"transient apply could not find GEOM profile: {profile_name}")


def _replace_managed_blocks(source: str, blocks: dict[str, object], replacements: dict[str, str]) -> str:
    rendered = source
    for name in reversed(MANAGED_BLOCK_NAMES):
        block = blocks[name]
        rendered = rendered[: block.start_index] + replacements[name] + rendered[block.end_index :]
    return rendered


def _settle_terminate_and_reap(
    process: _Process,
    *,
    sleep: Sleep,
    settle_timeout: float,
    terminate_timeout: float,
    kill_process_group: KillProcessGroup,
) -> str:
    sleep(settle_timeout)

    try:
        process.wait(timeout=0)
        return ""
    except subprocess.TimeoutExpired:
        pass

    try:
        kill_process_group(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass

    try:
        process.wait(timeout=terminate_timeout)
        return ""
    except subprocess.TimeoutExpired:
        pass

    try:
        kill_process_group(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass

    try:
        process.wait(timeout=terminate_timeout)
        return ""
    except subprocess.TimeoutExpired:
        return "Runtime apply warning: transient devilspie2 did not exit cleanly"


def _default_sleep(seconds: float) -> None:
    import time

    time.sleep(seconds)
