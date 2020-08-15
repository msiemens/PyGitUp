# System imports
import os
from os.path import join

from git import *
from PyGitUp.tests import basepath, init_master, update_file

test_name = 'multiple-remotes'
repo_path = join(basepath, test_name + os.sep)


def setup():
    master1_path, master1 = init_master(test_name + '.1')

    # Prepare master repo
    master1.git.checkout(b=test_name)

    # Clone to test repo
    path = join(basepath, test_name)

    master1.clone(path, b=test_name)
    repo = Repo(path, odbt=GitCmdObjectDB)

    assert repo.working_dir == path

    # Modify file in master
    update_file(master1, test_name)

    # Create second remote
    master2_path = join(basepath, 'master.' + test_name + '.2')
    master1.clone(master2_path, b=test_name)
    master2 = Repo(master2_path, odbt=GitCmdObjectDB)

    # Add second master as remote, too
    repo.git.checkout(b=test_name + '.2')
    repo.git.remote('add', 'upstream', master2_path)
    repo.git.fetch(all=True)
    repo.git.branch(set_upstream_to='upstream/' + test_name)

    update_file(master2, test_name)


def test_fast_forwarded():
    """ Run 'git up' with multiple remotes """
    os.chdir(repo_path)

    from PyGitUp.gitup import GitUp
    gitup = GitUp(testing=True)
    gitup.run()

    assert len(gitup.states) == 2
    assert gitup.states[0] == 'fast-forwarding'
    assert gitup.states[1] == 'fast-forwarding'
