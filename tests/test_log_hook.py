# System imports
import os
import platform
from os.path import join

# 3rd party libs
from nose.tools import *
from git import *

# PyGitup imports
from PyGitUp.git_wrapper import GitError
from tests import basepath, write_file, init_master, update_file

test_name = 'log-hook'

repo_path = join(basepath, test_name + os.sep)


def setup():
    master_path, master = init_master(test_name)

    # Prepare master repo
    master.git.checkout(b=test_name)

    # Clone to test repo
    path = join(basepath, test_name)

    master.clone(path, b=test_name)
    repo = Repo(path, odbt=GitCmdObjectDB)

    assert repo.working_dir == path

    # Set git-up.rebase.log-hook
    if platform.system() == 'Windows':
        repo.git.config(
            'git-up.rebase.log-hook',
            'IF [%1]==[] exit 1; '  # Note: this whole string is one line
            'IF [%2]==[] exit 1; '  # and will be split by 'git up' to
            'git show $1 > nil; '   # multiple lines.
            'git show $2 > nil;'
        )
    else:
        repo.git.config(
            'git-up.rebase.log-hook',
            'if [ -z "$1" -a -z "$2" ]; then exit 1; fi;'
            'git show $1 > /dev/null;'
            'git show $2 > /dev/null;'
        )

    # Modify file in master
    update_file(master, test_name)


def test_log_hook():
    """ Run 'git up' with log-hook"""
    os.chdir(repo_path)

    from PyGitUp.gitup import GitUp
    gitup = GitUp()
    gitup.run(testing=True)

    assert_equal(len(gitup.states), 1)
    assert_equal(gitup.states[0], 'fast-forwarding')
