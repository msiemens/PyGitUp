# System imports
import os
from os.path import join

import pytest
from git import *
from PyGitUp.git_wrapper import RebaseError
from PyGitUp.tests import basepath, init_master, update_file, write_file

test_name = 'overwrite_untracked_error'
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
    update_file(master, test_name, filename='test1.txt')

    # Modify file in working directory
    write_file(join(path, 'test1.txt'), 'Hello world!')


def test_fast_forwarded():
    """ Fail correctly when a rebase would overwrite untracked files """
    os.chdir(repo_path)

    from PyGitUp.gitup import GitUp
    gitup = GitUp(testing=True)

    with pytest.raises(RebaseError):
        gitup.run()
