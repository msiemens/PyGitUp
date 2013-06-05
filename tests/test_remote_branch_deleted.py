# System imports
import os
from os.path import join

# 3rd party libs
from nose.tools import *
from git import *

# PyGitup imports
from PyGitUp.git_wrapper import GitError
from tests import basepath, write_file, init_master, update_file, testfile_name

test_name = 'remote-branch-deleted'
new_branch_name = test_name + '.2'

repo_path = join(basepath, test_name + os.sep)

def _read_file(path):
    with open(path) as f:
        return f.read()


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


def test_ahead_of_upstream():
    """ Run 'git up' with remotely deleted branch """
    os.chdir(repo_path)

    from PyGitUp.gitup import GitUp
    gitup = GitUp()
    gitup.run(testing=True)

    assert_equal(len(gitup.states), 2)
    assert_equal(gitup.states[1], 'remote branch doesn\'t exist')
