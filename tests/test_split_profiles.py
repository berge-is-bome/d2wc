import pytest

from d2wc.core.split_profiles import Geometry, generate_split_profiles


def test_generate_split_profiles_without_border_width() -> None:
    profiles = generate_split_profiles(Geometry(x=0, y=0, w=3840, h=2160))

    assert profiles.half_left == Geometry(x=0, y=0, w=1920, h=2160)
    assert profiles.half_right == Geometry(x=1920, y=0, w=1920, h=2160)


def test_generate_split_profiles_with_border_width() -> None:
    profiles = generate_split_profiles(
        Geometry(x=0, y=0, w=3840, h=2160),
        window_border_width=6,
    )

    assert profiles.half_left == Geometry(x=0, y=0, w=1926, h=2160)
    assert profiles.half_right == Geometry(x=1914, y=0, w=1926, h=2160)


def test_generate_split_profiles_rejects_negative_border_width() -> None:
    with pytest.raises(ValueError, match="window_border_width"):
        generate_split_profiles(Geometry(x=0, y=0, w=3840, h=2160), -1)


def test_generate_split_profiles_rejects_invalid_screen_size() -> None:
    with pytest.raises(ValueError, match="screen width and height"):
        generate_split_profiles(Geometry(x=0, y=0, w=0, h=2160))
