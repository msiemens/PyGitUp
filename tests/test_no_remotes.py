# System imports
import os

# 3rd party libs
from nose.tools import *

# PyGitup imports
from tests import init_master
from PyGitUp.git_wrapper import GitError

test_name = 'no_remotes'


def setup():
    global master_path
    master_path, master = init_master(test_name)

    # Prepare master repo
    master.git.checkout(b=test_name)


@raises(GitError)
def test_no_remotes():
    """ Run 'git up' w/o remotes """
    os.chdir(master_path)

    from PyGitUp.gitup import GitUp
    GitUp()
