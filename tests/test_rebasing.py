# System imports
import os
import subprocess
from os.path import join

# 3rd party libs
from nose.tools import *
from git import *

# PyGitup imports
from tests import basepath, write_file, init_master, update_file, testfile_name
from PyGitUp.git_wrapper import GitWrapper

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

    write_file(repo_file , contents)
    repo.index.add([repo_file])
    repo.index.commit(test_name)

    if repo.git.cat_file_header is not None:
        subprocess.call(("TASKKILL /F /T /PID {0} 2>nul 1>nul".format(
            str(repo.git.cat_file_header.proc.pid)
        )), shell=True)
    if repo.git.cat_file_all is not None:
        subprocess.call(("TASKKILL /F /T /PID {0} 2>nul 1>nul".format(
            str(repo.git.cat_file_all.proc.pid)
        )), shell=True)


def test_ahead_of_upstream():
    """ Run 'git up' with result: rebasing """
    os.chdir(repo_path)

    from PyGitUp.gitup import GitUp
    gitup = GitUp()
    gitup.run(testing=True)

    assert_equal(len(gitup.states), 1)
    assert_equal(gitup.states[0], 'rebasing')
