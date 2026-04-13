# System imports
import os
from os.path import join

from git import *
from PyGitUp.tests import basepath, init_master, update_file, write_file

test_name = 'worktree-rebase'
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

    # Add the worktree with the second branch checked out
    repo.git.worktree('add', worktree_path, test_name + '-wt')

    # Set up tracking for the worktree branch
    repo.git.branch('--set-upstream-to', 'origin/' + test_name,
                     test_name + '-wt')

    # Modify file in master to create something to rebase/fast-forward
    update_file(master, test_name)


def test_worktree():
    """Run 'git up' with branches checked out in worktrees."""
    os.chdir(repo_path)

    # --- Fast-forward case ---
    from PyGitUp.gitup import GitUp
    gitup = GitUp(testing=True)
    gitup.run()

    assert 'fast-forwarding' in gitup.states

    # The worktree branch should have been updated
    assert (master.branches[test_name].commit ==
            repo.branches[test_name + '-wt'].commit)

    # --- Rebase case ---
    # Make a local commit on the worktree branch so it diverges
    wt_repo = Repo(worktree_path, odbt=GitCmdObjectDB)
    wt_file = join(worktree_path, 'worktree_file.txt')
    write_file(wt_file, 'worktree change')
    wt_repo.index.add([wt_file])
    wt_repo.index.commit('worktree commit')

    # Make another commit on master so the branch diverges
    update_file(master, test_name + ' second update')

    gitup2 = GitUp(testing=True)
    gitup2.run()

    assert 'rebasing' in gitup2.states

    # The worktree branch should contain the master commit
    wt_repo = Repo(worktree_path, odbt=GitCmdObjectDB)
    master_commit = master.branches[test_name].commit.hexsha
    # Walk the worktree branch history to verify the master commit is there
    wt_commits = [c.hexsha for c in wt_repo.iter_commits()]
    assert master_commit in wt_commits
