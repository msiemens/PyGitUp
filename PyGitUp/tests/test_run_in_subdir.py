# System imports
import os
from os.path import join

from git import *
from PyGitUp.tests import basepath, init_master, update_file

test_name = 'run-in-subdir'
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


def test_run_in_subdir():
    """ Run 'git up' in a subdir of the repo """
    subdir = join(repo_path, 'dir')
    os.mkdir(subdir)
    os.chdir(subdir)

    from PyGitUp.gitup import GitUp
    gitup = GitUp(testing=True)
    gitup.run()

    assert len(gitup.states) == 1
    assert gitup.states[0] == 'fast-forwarding'
