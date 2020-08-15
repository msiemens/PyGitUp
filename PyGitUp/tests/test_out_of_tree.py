# System imports
import os
from os.path import join

from git import *
from PyGitUp.tests import basepath, write_file, init_master

test_name = 'out-of-tree'
testfile_name = 'file'

repo_path = join(basepath, test_name + os.sep)
git_dir = join(repo_path, 'git-dir', '.git')
work_tree = join(repo_path, 'work-tree')


def setup():
    master_path, master = init_master(test_name)

    os.makedirs(git_dir)
    os.makedirs(work_tree)

    # Prepare master repo
    master.git.checkout(b=test_name)

    # Create work tree
    with open(join(work_tree, '.git'), 'w') as f:
        f.write('gitdir: ' + git_dir)

    # Clone master
    os.environ['GIT_DIR'] = git_dir
    os.environ['GIT_WORK_TREE'] = work_tree

    repo = Repo.init(work_tree)
    repo.git.remote('add', 'origin', master_path)
    repo.git.fetch('origin')
    repo.git.checkout('origin/' + test_name, b=test_name)

    del os.environ['GIT_DIR']
    del os.environ['GIT_WORK_TREE']

    # Modify file in our repo
    repo_path_file = join(master_path, testfile_name)
    write_file(repo_path_file, 'line 1\nline 2\ncounter: 2')
    master.index.add([repo_path_file])
    master.index.commit(test_name)


def test_out_of_tree():
    """ Run 'git up' with an out-of-tree source """
    os.chdir(work_tree)

    from PyGitUp.gitup import GitUp
    gitup = GitUp(testing=True)
    gitup.run()

    assert gitup.states == ['fast-forwarding']
