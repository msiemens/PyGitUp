# System imports
import os
from os.path import join

from git import *
from nose.tools import *

from PyGitUp.tests import basepath, init_master

test_name = 'remote-branch-deleted'
new_branch_name = test_name + '.2'
repo_path = join(basepath, test_name + os.sep)


def setup():
    master_path, master = init_master(test_name)

    # Prepare master repo
    master.git.checkout(b=test_name)

    # Create new branch
    master.git.checkout(b=new_branch_name)

    # Clone to test repo
    path = join(basepath, test_name)

    master.clone(path, b=test_name)
    repo = Repo(path, odbt=GitCmdObjectDB)

    assert repo.working_dir == path

    # Checkout new branch in cloned repo
    repo.git.checkout(new_branch_name, 'origin/' + new_branch_name, b=True)

    # Remove branch from master again
    master.git.checkout(test_name)
    master.git.branch(new_branch_name, d=True)


def test_remote_branch_deleted():
    """ Run 'git up' with remotely deleted branch """
    os.chdir(repo_path)

    from PyGitUp.gitup import GitUp
    gitup = GitUp(testing=True)
    gitup.run()

    assert_equal(len(gitup.states), 2)
    assert_equal(gitup.states[1], 'remote branch doesn\'t exist')
