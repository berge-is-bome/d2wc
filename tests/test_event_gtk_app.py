from d2wc.ui.managed_actions import EDITOR_ACTIONS


def test_managed_editor_actions() -> None:
    assert EDITOR_ACTIONS == ("Add", "Modify", "Delete")
