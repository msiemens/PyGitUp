# System imports
import os
import subprocess
from os.path import join

# 3rd party libs
from nose.tools import *
from git import *

# PyGitup imports
from tests import basepath, write_file, init_master, update_file, testfile_name
from PyGitUp.git_wrapper import GitWrapper, GitError

test_name = 'no_remotes'

def _read_file(path):
    with open(path) as f:
        return f.read()


def setup():
    global master_path
    master_path, master = init_master(test_name)

    # Prepare master repo
    master.git.checkout(b=test_name)


@raises(GitError)
def test_ahead_of_upstream():
    """ Run 'git up' w/o remotes """
    os.chdir(master_path)

    from PyGitUp.gitup import GitUp
    gitup = GitUp()
    gitup.run(testing=True)
