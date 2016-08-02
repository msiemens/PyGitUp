# System imports
import os
from os.path import join

from nose.tools import *

from PyGitUp.tests import basepath, init_master, update_file

test_name = 'local_tracking'
repo_path = join(basepath, test_name + os.sep)


def _read_file(path):
    with open(path) as f:
        return f.read()


def setup():
    global repo_path
    master_path, master = init_master(test_name)

    # Prepare master repo
    master.git.checkout(b=test_name)

    # Create branch with local tracking
    master.git.checkout(b=test_name + '_b', t=True)
    repo_path = master_path

    # Modify tracking branch
    master.git.checkout(test_name)
    update_file(master)


def test_local_tracking():
    """ Run 'git up' with a local tracking branch """
    os.chdir(repo_path)

    from PyGitUp.gitup import GitUp
    gitup = GitUp(testing=True)
    gitup.run()

    assert_equal(len(gitup.states), 1)
    assert_equal(gitup.states[0], 'fast-forwarding')
