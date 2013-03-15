# System imports
import os
from os.path import join

# 3rd party libs
from nose.tools import *
from git import *

# PyGitup imports
from PyGitUp.git_wrapper import GitError
from tests import basepath

repo_path = join(basepath, 'test-3' + os.sep)
master_path = join(basepath, 'master' + os.sep)

repo = None
master = None


def setup():
    global repo, master

    # Initialize repos
    repo = Repo(repo_path)
    master = Repo(master_path)

    # Setup repositories
    master_branch = [b for b in master.branches if b.name == 'test-3']

    if len(master_branch) == 1:
        master_branch[0].checkout()
    else:
        raise Exception("Invalid git setup")

    repo.head.reset('checkpoint', True, True)
    repo.git.stash('pop')


def teardown():
    global repo, master

    del repo
    del master


@raises(GitError)
def test_unstash_error():
    """ Run 'git up' with an unclean unstash """
    os.chdir(repo_path)

    from PyGitUp.gitup import run
    run(testing=True)
