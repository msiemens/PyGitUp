# System imports
import os
from os.path import join

from git import *
from nose.tools import *

from PyGitUp.git_wrapper import GitError
from PyGitUp.tests import basepath, init_master, update_file

test_name = 'test-fail'
repo_path = join(basepath, test_name + os.sep)


def setup():
    master_path, master = init_master(test_name)

    # Prepare master repo
    master.git.checkout(b=test_name)

    # Clone to test repo
    path = join(basepath, test_name)

    master.clone(path, b=test_name)
    repo = Repo(path, odbt=GitCmdObjectDB)

    assert repo.working_dir == path

    # Set remote
    repo.git.remote('set-url', 'origin', 'does-not-exist')

    # Modify file in master
    update_file(master, test_name)


@raises(GitError)
def test_fetch_fail():
    """ Run 'git up' with a non-existent remote """
    os.chdir(repo_path)

    from PyGitUp.gitup import GitUp
    gitup = GitUp(testing=True)
    gitup.run()
