from pathlib import Path


WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "release.yml"


def test_candidate_release_uses_pypi_trusted_publisher():
    workflow = WORKFLOW.read_text()

    candidate = workflow.split("  publish-candidate:", 1)[1]
    assert "contains(github.ref_name, 'rc')" in candidate
    assert "name: pypi" in candidate
    assert "testpypi" not in candidate
    assert "test.pypi.org" not in candidate
