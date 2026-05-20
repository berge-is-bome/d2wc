import pytest

from d2wc.core.rule_grammar import RuleParseError, parse_prefixed_rule


def test_parse_domain_only_rule() -> None:
    rule = parse_prefixed_rule("d:personal")

    assert rule.domain == "personal"
    assert rule.class_name is None
    assert rule.geometry_profile is None
    assert rule.left_edge_mode is None
    assert rule.has_target


def test_parse_domain_class_geometry_rule() -> None:
    rule = parse_prefixed_rule("d:personal c:Okular g:half_left")

    assert rule.domain == "personal"
    assert rule.class_name == "okular"
    assert rule.geometry_profile == "half_left"
    assert rule.left_edge_mode is None
    assert rule.has_target


def test_parse_left_edge_rule() -> None:
    rule = parse_prefixed_rule("d:dom0 c:qubes-qube-manager le:pos1")

    assert rule.domain == "dom0"
    assert rule.class_name == "qubes-qube-manager"
    assert rule.geometry_profile is None
    assert rule.left_edge_mode == "pos1"


@pytest.mark.parametrize(
    "bad_rule, match",
    [
        ("", "empty"),
        ("d:", "invalid token"),
        ("personal", "invalid token"),
        ("x:personal", "unknown prefix"),
        ("d:personal d:work", "duplicate prefix"),
        ("c:okular c:krusader", "duplicate prefix"),
        ("g:half_left g:half_right", "duplicate prefix"),
        ("le:pos1 le:pos2", "duplicate prefix"),
    ],
)
def test_parse_invalid_rules(bad_rule: str, match: str) -> None:
    with pytest.raises(RuleParseError, match=match):
        parse_prefixed_rule(bad_rule)
