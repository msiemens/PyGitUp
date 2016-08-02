# System imports
import os
from os.path import join

from git import *
from nose.tools import *

from PyGitUp.tests import basepath, init_master, update_file

test_name = 'returning-to-branch'
new_branch_name = test_name + '.2'
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

    # Create a new branch in repo
    repo.git.checkout(b=new_branch_name)

    # Modify file in master
    update_file(master, test_name)


def test_returning_to_branch():
    """ Run 'git up': return to branch """
    os.chdir(repo_path)

    from PyGitUp.gitup import GitUp
    gitup = GitUp(testing=True)
    gitup.run()

    assert_equal(len(gitup.states), 1)
    assert_equal(gitup.states[0], 'fast-forwarding')
    assert_equal(gitup.repo.head.ref.name, new_branch_name)
