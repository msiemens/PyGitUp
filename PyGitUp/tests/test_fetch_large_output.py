# System imports
from os import sep, chdir
from os.path import join
import io

from git import *

from PyGitUp.tests import basepath, init_master

TEST_NAME = 'fetch-large-output'
REPO_PATH = join(basepath, TEST_NAME + sep)


def setup_module():
    master_path, master = init_master(TEST_NAME)

    # Prepare master repo
    master.git.checkout(b=TEST_NAME)

    # Clone to test repo
    path = join(basepath, TEST_NAME)

    master.clone(path, b=TEST_NAME)
    repo = Repo(path, odbt=GitCmdObjectDB)

    assert repo.working_dir == path

    # Generate lots of branches
    total_branch_name_bytes = 0
    for i in range(0, 1500):
        branch_name = 'branch-name-%d' % i
        total_branch_name_bytes += len(branch_name)
        master.git.checkout(b=branch_name)


def test_fetch_large_output():
    """ Run 'git up' with a fetch that outputs lots of data """
    # Arrange
    chdir(REPO_PATH)
    from PyGitUp.gitup import GitUp
    gitup = GitUp(testing=True)

    # Act
    gitup.run()

    # Assert
    assert len(gitup.states) == 1
    assert gitup.states[0] == 'up to date'
