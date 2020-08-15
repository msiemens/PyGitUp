# System imports
import os
from os.path import join

import pytest

from PyGitUp.git_wrapper import GitError
from PyGitUp.tests import basepath

test_name = 'git-not-in-path'
repo_path = join(basepath, test_name + os.sep)


def setup():
    os.makedirs(repo_path, 0o700)


def test_not_a_git_repo():
    """ Run 'git up' with git no being in PATH """
    os.chdir(repo_path)
    environ = os.environ.copy()
    os.environ['PATH'] = ''

    try:
        with pytest.raises(GitError, match="The git executable could not be "
                                           "found"):
            from PyGitUp.gitup import GitUp
            GitUp(testing=True)

    finally:
        os.environ.update(environ)
