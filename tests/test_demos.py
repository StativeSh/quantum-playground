import pytest

from qplay import demos
from qplay.__main__ import main


@pytest.mark.parametrize("name", sorted(demos.DEMOS))
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
