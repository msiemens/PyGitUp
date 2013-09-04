# System imports
import os
from os.path import join

# 3rd party libs
from nose.tools import *
from git import *

# PyGitup imports
from PyGitUp.git_wrapper import CheckoutError
from tests import basepath, init_master, testfile_name, wip, write_file

test_name = 'checkout_error'
second_branch = test_name + '.2'
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

    # Create second branch and add test_file.1 to index
    write_file(join(path, testfile_name + '.1'), 'contents :)')
    repo.index.add([testfile_name + '.1'])

    # Checkout first branch and add same file but untracked
    repo.git.checkout(test_name)
    write_file(join(path, testfile_name), 'content')


@wip
@raises(CheckoutError)
def test_fast_forwarded():
    """ Run 'git up' with checkout errors """
    os.chdir(repo_path)

    from PyGitUp.gitup import GitUp
    gitup = GitUp()
    gitup.run(testing=True)
