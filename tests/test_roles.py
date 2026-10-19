from jarvis.dashboard import render
from jarvis.roles import ROLES


def test_all_responsibilities_have_contracts_and_truthful_status(tmp_path):
    assert len(ROLES) == 18
    assert len({r.name for r in ROLES}) == 18
    assert len({r.department for r in ROLES}) == 5
    assert all(r.purpose and r.inputs and r.outputs for r in ROLES)
    page = render(tmp_path / "desk")
    assert "News &amp; Event" in page and "PARTIAL" in page
    assert "Capital Governor / Risk" in page
