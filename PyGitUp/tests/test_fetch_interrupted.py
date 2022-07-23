# System imports
import os
from os.path import join

import pytest
from git import *
from PyGitUp.tests import basepath, init_master, capture

test_name = 'fetch-interrupted'
repo_path = join(basepath, test_name + os.sep)

def setup():
    _, master = init_master(test_name)

    master.git.checkout(b=test_name)
    path = join(basepath, test_name)

    master.clone(path, b=test_name)
    repo = Repo(path, odbt=GitCmdObjectDB)

    assert repo.working_dir == path

    master_path2, _ = init_master(test_name + '2')
    # Add second master repo to remotes
    repo.git.remote('add', test_name, master_path2)


def test_fetch_interrupted(monkeypatch):
    """ Run 'git up' and interrupt on fetch """
    os.chdir(repo_path)

    from PyGitUp.gitup import GitUp
    gitup = GitUp(testing=True)

    def mock_fetch(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(gitup, "fetch", mock_fetch)

    with pytest.raises(SystemExit) as error:
        gitup.run()

    assert error.value.code == 130
