import pytest

from qplay import animations, demos
from qplay.__main__ import main

# Over about 1.5 s each; run with `make test-all` (CI always does).
SLOW_DEMOS = {"double-slit", "ising"}
SLOW_ANIMATIONS = {"double-slit", "gas"}


def _params(names, slow):
    return [pytest.param(n, marks=pytest.mark.slow) if n in slow else n for n in sorted(names)]


@pytest.mark.parametrize("name", _params(demos.DEMOS, SLOW_DEMOS))
def test_demo_renders(name, tmp_path):
    path = demos.run(name, tmp_path)
    assert path.exists() and path.stat().st_size > 1000


def test_cli_list_and_run(tmp_path, capsys):
    assert main(["list"]) == 0
    assert "pendulum" in capsys.readouterr().out
    assert main(["run", "pendulum", "--out", str(tmp_path)]) == 0
    assert (tmp_path / "pendulum.png").exists()


def test_unknown_demo_is_an_error(tmp_path):
    with pytest.raises(SystemExit):
        main(["run", "nope", "--out", str(tmp_path)])


@pytest.mark.parametrize("name", _params(animations.ANIMATIONS, SLOW_ANIMATIONS))
def test_animation_renders(name, tmp_path):
    path = animations.render(name, tmp_path, n_frames=3, fps=5)
    assert path.suffix == ".gif" and path.stat().st_size > 1000


def test_cli_animate(tmp_path, capsys):
    assert main(["animate", "figure-eight", "--frames", "3", "--out", str(tmp_path)]) == 0
    assert (tmp_path / "figure-eight.gif").exists()
    with pytest.raises(SystemExit):
        main(["animate", "nope", "--out", str(tmp_path)])


def test_package_version_matches_installed_distribution():
    import importlib.metadata

    import qplay

    assert importlib.metadata.version("quantum-playground") == qplay.__version__
