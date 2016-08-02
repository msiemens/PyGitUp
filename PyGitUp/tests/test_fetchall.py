# System imports
import os
from os.path import join

from git import *
from nose.tools import *

from PyGitUp.tests import basepath, init_master, capture

test_name = 'fetch-all'
repo_path = join(basepath, test_name + os.sep)


def setup():
    master_path, master = init_master(test_name)
    master_path2, master2 = init_master(test_name + '2')

    # Prepare master repo
    master.git.checkout(b=test_name)

    # Clone to test repo
    path = join(basepath, test_name)

    master.clone(path, b=test_name)
    repo = Repo(path, odbt=GitCmdObjectDB)

    assert repo.working_dir == path

    # Configure git up
    repo.git.config('git-up.fetch.all', 'true')

    # Add second master repo to remotes
    repo.git.remote('add', test_name, master_path2)


def test_fetchall():
    """ Run 'git up' with fetch.all """
    os.chdir(repo_path)

    from PyGitUp.gitup import GitUp
    gitup = GitUp(testing=True)

    with capture() as [stdout, _]:
        gitup.run()

    stdout = stdout.getvalue()

    assert_true('origin' in stdout)
    assert_true(test_name in stdout)
