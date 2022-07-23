import pytest
from PyGitUp.gitup import GitUp

def test_fetch_interrupted(monkeypatch):
    """ Run 'git up' and interrupt on fetch """

    gitup = GitUp(testing=True)

    def mock_fetch(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(gitup, "fetch", mock_fetch)

    with pytest.raises(SystemExit) as error:
        gitup.run()

    assert error.value.code == 130
