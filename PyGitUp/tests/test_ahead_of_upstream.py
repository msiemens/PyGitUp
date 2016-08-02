# System imports
import os
from os.path import join

from git import *
from nose.tools import *

from PyGitUp.tests import basepath, write_file, init_master

test_name = 'ahead-of-upstream'
testfile_name = 'file'

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

    # Modify file in our repo
    repo_path_file = join(path, testfile_name)
    write_file(repo_path_file, 'line 1\nline 2\ncounter: 2')
    repo.index.add([repo_path_file])
    repo.index.commit(test_name)


def test_ahead_of_upstream():
    """ Run 'git up' with result: ahead of upstream """
    os.chdir(repo_path)

    from PyGitUp.gitup import GitUp
    gitup = GitUp(testing=True)
    gitup.run()

    assert_equal(len(gitup.states), 1)
    assert_equal(gitup.states[0], 'ahead')
