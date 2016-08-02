# System imports
import os

from nose.tools import *

from PyGitUp.git_wrapper import GitError
from PyGitUp.tests import init_master

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
    GitUp(testing=True)
