# System imports
import os
from os.path import join

from git import *
from PyGitUp.tests import basepath, init_master, update_file, write_file, \
    testfile_name

test_name = 'worktree-dirty'
repo_path = join(basepath, test_name + os.sep)
worktree_path = join(basepath, test_name + '-wt' + os.sep)


def setup_module():
    global master, repo

    master_path, master = init_master(test_name)

    # Prepare master repo
    master.git.checkout(b=test_name)

    # Clone to test repo
    path = join(basepath, test_name)

    master.clone(path, b=test_name)
    repo = Repo(path, odbt=GitCmdObjectDB)

    assert repo.working_dir == path

    # Create a second branch that will be checked out in a worktree
    repo.git.branch(test_name + '-wt', 'origin/' + test_name)
    repo.git.worktree('add', worktree_path, test_name + '-wt')
    repo.git.branch('--set-upstream-to', 'origin/' + test_name,
                    test_name + '-wt')

    # Commit a change to the test file in master. update_file() rewrites
    # the whole file, but only its last line actually changes.
    update_file(master, test_name)

    # Leave an unstaged change to the first line of the same file in the
    # worktree. It doesn't overlap the upstream change, but it's enough to
    # make 'git merge --ff-only' refuse to run on a dirty tree.
    wt_file = join(worktree_path, testfile_name)
    with open(wt_file) as f:
        contents = f.read()
    write_file(wt_file, contents.replace('line 1', 'local change', 1))


def test_worktree_dirty():
    """Run 'git up' with a dirty worktree whose branch can fast-forward."""
    os.chdir(repo_path)

    from PyGitUp.gitup import GitUp
    gitup = GitUp(testing=True)
    gitup.run()

    assert 'fast-forwarding' in gitup.states

    # The worktree branch should have been fast-forwarded
    assert (master.branches[test_name].commit ==
            repo.branches[test_name + '-wt'].commit)

    # The local change should have been restored on top of the update
    with open(join(worktree_path, testfile_name)) as f:
        contents = f.read()
    with open(join(master.working_dir, testfile_name)) as f:
        upstream_contents = f.read()
    assert contents == upstream_contents.replace('line 1', 'local change', 1)

    # ... and must not be left behind in the stash
    assert Git(worktree_path).stash('list') == ''
