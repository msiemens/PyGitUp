# System imports
import os
from os.path import join

from git import *
from nose.tools import *

from PyGitUp.tests import basepath, write_file, init_master, update_file, testfile_name

test_name = 'rebasing'
repo_path = join(basepath, test_name + os.sep)


def _read_file(path):
    with open(path) as f:
        return f.read()


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
    master_file = update_file(master, test_name)

    # Modify file in our repo
    contents = _read_file(master_file)
    contents = contents.replace('line 1', 'line x')
    repo_file = join(path, testfile_name)

    write_file(repo_file, contents)
    repo.index.add([repo_file])
    repo.index.commit(test_name)


def test_rebasing():
    """ Run 'git up' with result: rebasing """
    os.chdir(repo_path)

    from PyGitUp.gitup import GitUp
    gitup = GitUp(testing=True)
    gitup.run()

    assert_equal(len(gitup.states), 1)
    assert_equal(gitup.states[0], 'rebasing')
