# System imports
import os
from os.path import join

from git import *
from PyGitUp.tests import basepath, init_master, update_file

test_name = 'issue-55'
repo_path = join(basepath, test_name + os.sep)


def setup():
    master_path, master = init_master(test_name)

    branch_name = 'feature/#11772-replace-api-url'

    # Prepare master repo
    master.git.checkout(b=branch_name)

    # Clone to test repo
    path = join(basepath, test_name)

    master.clone(path, b=branch_name)
    repo = Repo(path, odbt=GitCmdObjectDB)

    assert repo.working_dir == path

    # Modify file in master
    update_file(master, test_name)


def test_issue_55():
    """ Regression test for #55 """
    os.chdir(repo_path)

    from PyGitUp.gitup import GitUp
    gitup = GitUp(testing=True)
    gitup.run()

    assert len(gitup.states) == 1
    assert gitup.states[0] == 'fast-forwarding'
