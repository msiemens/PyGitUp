# System imports
import os
from os.path import join

from git import *
from nose.tools import *

from PyGitUp.tests import basepath, init_master, update_file

test_name = 'up-to-date'
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

    # Modify file in master
    update_file(master, test_name)

    # Update repo
    repo.remotes.origin.pull()


def test_up_to_date():
    """ Run 'git up' with result: up to date """
    os.chdir(repo_path)

    from PyGitUp.gitup import GitUp
    gitup = GitUp(testing=True)
    gitup.run()

    assert_equal(len(gitup.states), 1)
    assert_equal(gitup.states[0], 'up to date')
