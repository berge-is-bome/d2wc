from d2wc.ui.gtk_app import _mode_message


def test_mode_message_for_missing_test_config() -> None:
    text = _mode_message(None, None)

    assert "Mode: event preview only" in text
    assert "Test config: not loaded" in text
