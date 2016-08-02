# System imports
import os
from os.path import join

from git import *
from nose.tools import *

from PyGitUp.git_wrapper import GitError
from PyGitUp.tests import basepath, init_master, update_file

test_name = 'detached'
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
    update_file(repo, test_name)
    update_file(repo, test_name)

    # Check out parent commit
    repo.git.checkout('HEAD~')


@raises(GitError)
def test_detached():
    """ Run 'git up' with detached head """
    os.chdir(repo_path)

    from PyGitUp.gitup import GitUp
    gitup = GitUp(testing=True)
    gitup.run()
