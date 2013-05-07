# System imports
import os
from os.path import join

# 3rd party libs
from nose.tools import *
from git import *

# PyGitup imports
from PyGitUp.git_wrapper import GitError
from tests import basepath, write_file, init_master, wip

test_name = 'unstash_error'
testfile_name = 'file'

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

    # Create checkpoint
    repo.git.checkout(b='checkpoint')

    # Modify file in master
    master_path_file = join(master_path, testfile_name)
    write_file(master_path_file , 'line 1\nline 2\ncounter: 2')
    master.index.add([master_path_file])
    master.index.commit(test_name)

    # Modify file in test-3 and commit
    path_file = join(path, testfile_name)
    write_file(path_file , 'line 1\nline 2\ncounter: 3')
    repo.index.add([path_file])
    repo.index.commit(test_name)

    # Modify file in test-3 and stash
    path_file = join(path, testfile_name)
    write_file(path_file, 'conflict!')

    repo.git.stash()

    # Setup repositories
    repo.head.reset('checkpoint', True, True)
    repo.git.stash('pop')

@wip
@raises(GitError)
def test_unstash_error():
    """ Run 'git up' with an unclean unstash """
    os.chdir(repo_path)

    from PyGitUp.gitup import run
    run(testing=True)
