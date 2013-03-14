"""

"""
from nose.tools import *

import os
from os.path import dirname, join, abspath
from git import *
from PyGitUp.git_wrapper import GitError

repo_path = join(dirname(abspath(__file__)), 'test-3')
master_path = join(dirname(abspath(__file__)), 'master')

repo = Repo(repo_path)
master = Repo(master_path)


def setup():
    # Setup repositories
    master_branch = [b for b in master.branches if b.name == 'test-3']

    if len(master_branch) == 1:
        master_branch[0].checkout()
    else:
        raise Exception("Invalid git setup")

    repo.head.reset('checkpoint', True, True)
    repo.git.stash('pop')


@raises(GitError)
def test_unstash_error():
    """ Run 'git up' with an unclean unstash """
    os.chdir(repo_path)

    from PyGitUp.gitup import run
    run()
