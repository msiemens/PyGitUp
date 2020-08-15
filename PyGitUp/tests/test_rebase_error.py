# System imports
import os
from os.path import join

import pytest
from git import *
from PyGitUp.git_wrapper import RebaseError
from PyGitUp.tests import basepath, write_file, init_master, update_file, testfile_name

test_name = 'rebase_error'
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

    # Modify file in our repo
    contents = 'completely changed!'
    repo_file = join(path, testfile_name)

    write_file(repo_file, contents)
    repo.index.add([repo_file])
    repo.index.commit(test_name)

    # Modify file in master
    update_file(master, test_name)


def test_rebase_error():
    """ Run 'git up' with a failing rebase """
    os.chdir(repo_path)

    from PyGitUp.gitup import GitUp
    gitup = GitUp(testing=True)

    with pytest.raises(RebaseError):
        gitup.run()

