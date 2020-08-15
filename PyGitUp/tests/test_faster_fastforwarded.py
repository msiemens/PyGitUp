# System imports
import os
from os.path import join

from git import *
from PyGitUp.tests import basepath, init_master, update_file

test_name = 'faster-forwarded'
repo_path = join(basepath, test_name + os.sep)


def setup():
    global master, repo
    master_path, master = init_master(test_name)

    # Prepare master repo
    master.git.checkout(b=test_name)

    # Clone to test repo
    path = join(basepath, test_name)

    master.clone(path, b=test_name)
    repo = Repo(path, odbt=GitCmdObjectDB)
    repo.git.checkout('origin/' + test_name, b=test_name + '.2')

    assert repo.working_dir == path

    # Modify file in master
    update_file(master, test_name)


def test_faster_forwarded():
    """ Run 'git up' with result: (fast) fast-forwarding """
    os.chdir(repo_path)

    assert master.branches[test_name].commit != repo.branches[test_name].commit
    assert master.branches[test_name].commit != repo.branches[test_name + '.2'].commit

    from PyGitUp.gitup import GitUp
    gitup = GitUp(testing=True)
    gitup.run()

    assert len(gitup.states) == 2
    assert gitup.states[0] == 'fast-forwarding'
    assert gitup.states[1] == 'fast-forwarding'
    assert master.branches[test_name].commit == repo.branches[test_name].commit
    assert master.branches[test_name].commit == repo.branches[test_name + '.2'].commit
