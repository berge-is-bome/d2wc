from d2wc.event_inventory import KnownWindowCandidate, parse_known_window_candidates


def test_parse_known_window_candidates_keeps_only_normal_windows() -> None:
    raw = """
machine: work
application: work:org.example.App
class_instance_name: work:Example
window_type: WINDOW_TYPE_NORMAL

machine: work
application: work:org.example.Dialog
class_instance_name: work:Dialog
window_type: WINDOW_TYPE_DIALOG
"""

    result = parse_known_window_candidates(raw)

    assert result == (
        KnownWindowCandidate(
            machine="work",
            application="example",
            raw_class_instance_name="work:Example",
            window_type="WINDOW_TYPE_NORMAL",
            raw_source=(
                "machine: work\n"
                "application: work:org.example.App\n"
                "class_instance_name: work:Example\n"
                "window_type: WINDOW_TYPE_NORMAL"
            ),
        ),
    )


def test_parse_known_window_candidates_normalizes_dom0_and_alias_keys() -> None:
    raw = """
_QUBES_VMNAME=""
application_name="dom0:Qubes-app-menu"
wm_class_instance="dom0:Qubes-app-menu"
window_type=WINDOW_TYPE_NORMAL
"""

    result = parse_known_window_candidates(raw)

    assert len(result) == 1
    assert result[0].machine == "dom0"
    assert result[0].application == "qubes-app-menu"
    assert result[0].raw_class_instance_name == "dom0:Qubes-app-menu"


def test_parse_known_window_candidates_ignores_incomplete_records() -> None:
    raw = """
machine: work
window_type: WINDOW_TYPE_NORMAL
"""

    assert parse_known_window_candidates(raw) == ()
