from pathlib import Path

from d2wc.cli import main
from d2wc.core.rendering import render_source


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_cli_render_requires_stdout(capsys) -> None:
    exit_code = main(["render", "--config", str(REPO_ROOT / "src" / "d2wc.lua")])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "render is dry-run only" in captured.out


def test_cli_render_stdout_prints_rendered_lua_source(capsys) -> None:
    config_path = REPO_ROOT / "src" / "d2wc.lua"
    source = config_path.read_text(encoding="utf-8")
    expected = render_source(source).source

    exit_code = main(["render", "--config", str(config_path), "--stdout"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == expected
    assert captured.err == ""


def test_cli_render_rejects_invalid_config(tmp_path, capsys) -> None:
    config_path = tmp_path / "invalid.lua"
    config_path.write_text(
        '''
local EXCLUDE = { "g:half_left" }
local PIN = {}
local WORKSPACE_ROUTES = {}
local GEOM = { half_left = { x = 0, y = 0, w = 10, h = 10 } }
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {}
''',
        encoding="utf-8",
    )

    exit_code = main(["render", "--config", str(config_path), "--stdout"])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "cannot render invalid config" in captured.out
    assert "EXCLUDE: rule must include d: or c:: g:half_left" in captured.out
