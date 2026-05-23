"""Generic managed-section actions for the dedicated d2wc UI test config."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from d2wc.core.geom_operations import (
    GeometryOperationError,
    GeometryProfileInUseError,
    add_geometry_profile_to_source,
    delete_geometry_profile_from_source,
    modify_geometry_profile_in_source,
)
from d2wc.core.left_edge_operations import (
    LeftEdgeOperationError,
    add_left_edge_rule_to_source,
    delete_left_edge_rule_from_source,
    modify_left_edge_rule_in_source,
)
from d2wc.core.managed_config import GeometryProfile
from d2wc.core.placement_operations import (
    PlacementOperationError,
    add_placement_rule_to_source,
    delete_placement_rule_from_source,
    modify_placement_rule_in_source,
)
from d2wc.core.rendering import RenderValidationError
from d2wc.core.route_operations import (
    RouteOperationError,
    add_route_rule_to_source,
    delete_route_rule_from_source,
    modify_route_rule_in_source,
)
from d2wc.core.saving import SaveConfigError, SaveValidationError, save_source_config
from d2wc.core.target_rule_operations import (
    TargetRuleOperationError,
    add_exclude_rule_to_source,
    add_pin_rule_to_source,
    delete_exclude_rule_from_source,
    delete_pin_rule_from_source,
    modify_exclude_rule_in_source,
    modify_pin_rule_in_source,
)
from d2wc.test_config import TestConfigActionResult

MANAGED_ACTION_SECTIONS = (
    "EXCLUDE",
    "PIN",
    "WORKSPACE_ROUTES",
    "GEOM",
    "WORKSPACE_PLACEMENT",
    "LEFT_EDGE_CORRECTION",
)
MANAGED_ACTION_OPERATIONS = ("add", "modify", "delete")


@dataclass(frozen=True)
class ManagedSectionActionRequest:
    """One managed-section request from the GTK test-config editor."""

    section: str
    operation: str
    rule: str = ""
    existing_rule: str = ""
    workspace: int | None = None
    profile_name: str = ""
    x: int | None = None
    y: int | None = None
    w: int | None = None
    h: int | None = None


def apply_managed_section_action(config_path: Path, request: ManagedSectionActionRequest) -> TestConfigActionResult:
    """Apply one managed-section action to the dedicated test config."""

    section = request.section.upper()
    operation = request.operation.lower()
    action = f"{operation} {section}"

    if section not in MANAGED_ACTION_SECTIONS:
        return TestConfigActionResult(False, action, config_path, message=f"Unsupported section: {request.section}")
    if operation not in MANAGED_ACTION_OPERATIONS:
        return TestConfigActionResult(False, action, config_path, message=f"Unsupported operation: {request.operation}")

    try:
        source = config_path.read_text(encoding="utf-8")
        edit = _apply_to_source(source, request)
        result = save_source_config(config_path, edit.source, validation=edit.validation)
    except (
        OSError,
        GeometryOperationError,
        GeometryProfileInUseError,
        LeftEdgeOperationError,
        PlacementOperationError,
        RouteOperationError,
        TargetRuleOperationError,
        RenderValidationError,
        SaveConfigError,
        SaveValidationError,
    ) as exc:
        return TestConfigActionResult(False, action, config_path, message=str(exc))
    except ValueError as exc:
        return TestConfigActionResult(False, action, config_path, message=str(exc))

    return TestConfigActionResult(
        ok=True,
        action=action,
        path=result.config_path,
        backup_path=result.backup_path,
        backup_member=result.backup_member,
        message=_success_message(request),
    )


def _apply_to_source(source: str, request: ManagedSectionActionRequest):
    section = request.section.upper()
    operation = request.operation.lower()

    if section == "EXCLUDE":
        return _target_rule_action(
            source,
            operation,
            request,
            add_exclude_rule_to_source,
            modify_exclude_rule_in_source,
            delete_exclude_rule_from_source,
        )
    if section == "PIN":
        return _target_rule_action(
            source,
            operation,
            request,
            add_pin_rule_to_source,
            modify_pin_rule_in_source,
            delete_pin_rule_from_source,
        )
    if section == "WORKSPACE_ROUTES":
        if operation == "add":
            if request.workspace is None:
                raise ValueError("WORKSPACE_ROUTES add requires a workspace number")
            return add_route_rule_to_source(source, request.workspace, _required_rule(request))
        if operation == "modify":
            if request.workspace is None:
                raise ValueError("WORKSPACE_ROUTES modify requires a workspace number")
            return modify_route_rule_in_source(source, _required_existing_rule(request), request.workspace, _required_rule(request))
        return delete_route_rule_from_source(source, _required_existing_or_rule(request))
    if section == "GEOM":
        if operation == "add":
            return add_geometry_profile_to_source(source, _geometry_profile_from_request(request))
        if operation == "modify":
            return modify_geometry_profile_in_source(source, _geometry_profile_from_request(request))
        if not request.profile_name.strip():
            raise ValueError("GEOM delete requires a profile name")
        return delete_geometry_profile_from_source(source, request.profile_name)
    if section == "WORKSPACE_PLACEMENT":
        return _target_rule_action(
            source,
            operation,
            request,
            add_placement_rule_to_source,
            modify_placement_rule_in_source,
            delete_placement_rule_from_source,
        )
    if section == "LEFT_EDGE_CORRECTION":
        return _target_rule_action(
            source,
            operation,
            request,
            add_left_edge_rule_to_source,
            modify_left_edge_rule_in_source,
            delete_left_edge_rule_from_source,
        )

    raise ValueError(f"Unsupported section: {request.section}")


def _target_rule_action(source: str, operation: str, request: ManagedSectionActionRequest, add_callback, modify_callback, delete_callback):
    if operation == "add":
        return add_callback(source, _required_rule(request))
    if operation == "modify":
        return modify_callback(source, _required_existing_rule(request), _required_rule(request))
    return delete_callback(source, _required_existing_or_rule(request))


def _required_rule(request: ManagedSectionActionRequest) -> str:
    if not request.rule.strip():
        raise ValueError("Target entry is required")
    return request.rule.strip()


def _required_existing_rule(request: ManagedSectionActionRequest) -> str:
    if not request.existing_rule.strip():
        raise ValueError("Existing entry selection is required")
    return request.existing_rule.strip()


def _required_existing_or_rule(request: ManagedSectionActionRequest) -> str:
    value = request.existing_rule.strip() or request.rule.strip()
    if not value:
        raise ValueError("Existing entry selection is required")
    return value


def _geometry_profile_from_request(request: ManagedSectionActionRequest) -> GeometryProfile:
    if not request.profile_name.strip():
        raise ValueError("GEOM add or modify requires a profile name")
    missing = [name for name, value in (("x", request.x), ("y", request.y), ("w", request.w), ("h", request.h)) if value is None]
    if missing:
        raise ValueError(f"GEOM add or modify requires numeric values for: {', '.join(missing)}")
    return GeometryProfile(request.profile_name, request.x or 0, request.y or 0, request.w or 0, request.h or 0)


def _success_message(request: ManagedSectionActionRequest) -> str:
    section = request.section.upper()
    operation = request.operation.lower()
    if section == "GEOM":
        return f"{operation.title()}ed GEOM profile: {request.profile_name}"
    if section == "WORKSPACE_ROUTES" and operation in {"add", "modify"}:
        return f"{operation.title()}ed WORKSPACE_ROUTES rule on workspace {request.workspace}: {request.rule}"
    return f"{operation.title()}ed {section} entry: {request.rule or request.existing_rule}"
