# System imports
import os
from os.path import join

from git import *
from PyGitUp.tests import basepath, write_file, init_master, update_file, \
    testfile_name

test_name = 'push'
repo_path = join(basepath, test_name + os.sep)


def _read_file(path):
    with open(path) as f:
        return f.read()


def setup():
    master_path, master = init_master(test_name)
    master.git.config('receive.denyCurrentBranch', 'ignore', add=True)

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
    repo_file = join(path, 'file2.txt')

    write_file(repo_file, 'test')
    repo.index.add([repo_file])
    repo.index.commit(test_name)


def test_rebasing():
    """ Run 'git up' with pushing to origin """
    os.chdir(repo_path)

    from PyGitUp.gitup import GitUp
    gitup = GitUp(testing=True)
    gitup.settings['push.auto'] = True
    gitup.run()

    assert len(gitup.states) == 1
    assert gitup.states[0] == 'rebasing'
    assert gitup.pushed
