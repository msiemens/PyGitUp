# System imports
import os
from os.path import join

# 3rd party libs
from nose.tools import *

# PyGitup imports
from tests import basepath
from PyGitUp.git_wrapper import GitError

test_name = 'not-on-a-repo'
repo_path = join(basepath, test_name + os.sep)


def setup():
    os.makedirs(repo_path, 0700)


@raises(GitError)
def test_ahead_of_upstream():
    """ Run 'git up' being not on a git repo """
    os.chdir(repo_path)

    from PyGitUp.gitup import GitUp
    GitUp()
