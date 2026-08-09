# System imports
import os
import platform
import stat
from os.path import join

import pytest
from git import *
from PyGitUp.git_wrapper import RebaseError, UnresolvedConflictError
from PyGitUp.tests import basepath, write_file, init_master, update_file, \
    testfile_name

pytestmark = pytest.mark.skipif(
    platform.system() == 'Windows',
    reason="resolver scripts here are bash scripts; on Windows the "
           "resolver command runs via cmd.exe (not bash), so a bare "
           ".sh path won't execute there",
)

test_name_success = 'conflict_resolve_success'
test_name_fail = 'conflict_resolve_fail'
test_name_noresolver = 'conflict_no_resolver'
test_name_context = 'conflict_resolve_context'
test_name_worktree = 'conflict_resolve_worktree'

repo_path_success = join(basepath, test_name_success + os.sep)
repo_path_fail = join(basepath, test_name_fail + os.sep)
repo_path_noresolver = join(basepath, test_name_noresolver + os.sep)
repo_path_context = join(basepath, test_name_context + os.sep)
repo_path_worktree = join(basepath, test_name_worktree + os.sep)
worktree_path_worktree = join(basepath, test_name_worktree + '-wt' + os.sep)


def setup_conflict_repo(test_name):
    """Set up a repo with a rebase conflict."""
    master_path, master = init_master(test_name)

    # Prepare master repo
    master.git.checkout(b=test_name)

    # Clone to test repo
    path = join(basepath, test_name)
    master.clone(path, b=test_name)
    repo = Repo(path, odbt=GitCmdObjectDB)
    assert repo.working_dir == path

    # Modify file in master
    update_file(master, test_name)

    # Modify same file in our repo (conflicting change)
    contents = 'completely changed!'
    repo_file = join(path, testfile_name)
    write_file(repo_file, contents)
    repo.index.add([repo_file])
    repo.index.commit(test_name)

    # Modify file in master again
    update_file(master, test_name)

    return master, repo


def make_resolver_script(basedir, script_content):
    """Write a resolver shell script and return its path."""
    script_path = join(basedir, 'resolver.sh')
    write_file(script_path, script_content)
    os.chmod(script_path, stat.S_IRWXU)
    return script_path


def make_context_capturing_script(basedir, marker_path):
    """
    A resolver script that records its cwd and the GITUP_* env vars it
    was invoked with, then resolves the conflict as usual.
    """
    return make_resolver_script(basedir, (
        '#!/bin/bash\n'
        'echo "$PWD" > "{marker}"\n'
        'echo "$GITUP_BRANCH" >> "{marker}"\n'
        'echo "$GITUP_TARGET" >> "{marker}"\n'
        'echo "$GITUP_REPO_PATH" >> "{marker}"\n'
        'git checkout --theirs .\n'
        'git add -A\n'
        'GIT_EDITOR=true git rebase --continue\n'
    ).format(marker=marker_path))


def read_marker(marker_path):
    with open(marker_path) as f:
        lines = [line.strip() for line in f.readlines()]
    return lines


def setup_worktree_conflict(test_name, worktree_path):
    """
    Set up a repo with a branch checked out in a worktree that has a
    conflicting change relative to its upstream.
    """
    master_path, master = init_master(test_name)
    master.git.checkout(b=test_name)

    path = join(basepath, test_name)
    master.clone(path, b=test_name)
    repo = Repo(path, odbt=GitCmdObjectDB)
    assert repo.working_dir == path

    wt_branch = test_name + '-wt'
    repo.git.branch(wt_branch, 'origin/' + test_name)
    repo.git.worktree('add', worktree_path, wt_branch)
    repo.git.branch('--set-upstream-to', 'origin/' + test_name, wt_branch)

    # Conflicting change in the worktree branch. GitPython can't reliably
    # access a worktree's git dir directly (see test_worktree.py), so use
    # the git CLI via a plain Git() instance pointed at the worktree.
    wt_git = Git(worktree_path)
    contents = 'completely changed in worktree!'
    wt_file = join(worktree_path, testfile_name)
    write_file(wt_file, contents)
    wt_git.add(testfile_name)
    wt_git.commit(m=test_name)

    # Diverge master with a conflicting change to the same file
    update_file(master, test_name)

    return master, repo, wt_branch


def setup_module():
    global master_success, repo_success
    global master_fail, repo_fail
    global master_noresolver, repo_noresolver
    global master_context, repo_context
    global master_worktree, repo_worktree, worktree_branch

    master_success, repo_success = setup_conflict_repo(test_name_success)
    master_fail, repo_fail = setup_conflict_repo(test_name_fail)
    master_noresolver, repo_noresolver = setup_conflict_repo(
        test_name_noresolver
    )
    master_context, repo_context = setup_conflict_repo(test_name_context)
    master_worktree, repo_worktree, worktree_branch = (
        setup_worktree_conflict(test_name_worktree, worktree_path_worktree)
    )


def test_resolver_succeeds():
    """Resolver fixes conflicts and completes rebase."""
    os.chdir(repo_path_success)

    script = make_resolver_script(repo_path_success, (
        '#!/bin/bash\n'
        'git checkout --theirs .\n'
        'git add -A\n'
        'GIT_EDITOR=true git rebase --continue\n'
    ))

    from PyGitUp.gitup import GitUp
    gitup = GitUp(testing=True)
    gitup.settings['rebase.conflict-resolver'] = script
    gitup.run()

    assert 'rebasing' in gitup.states


def test_resolver_fails():
    """Resolver exits non-zero; UnresolvedConflictError is raised."""
    os.chdir(repo_path_fail)

    script = make_resolver_script(repo_path_fail, (
        '#!/bin/bash\n'
        'exit 1\n'
    ))

    from PyGitUp.gitup import GitUp
    gitup = GitUp(testing=True)
    gitup.settings['rebase.conflict-resolver'] = script

    with pytest.raises(UnresolvedConflictError):
        gitup.run()


def test_no_resolver():
    """Without a resolver, RebaseError is raised as before."""
    os.chdir(repo_path_noresolver)

    from PyGitUp.gitup import GitUp
    gitup = GitUp(testing=True)
    gitup.settings['rebase.conflict-resolver'] = None

    with pytest.raises(RebaseError):
        gitup.run()


def test_resolver_runs_in_repo_with_context():
    """
    The resolver runs with cwd set to the repo (not inherited from the
    calling process) and with GITUP_BRANCH/GITUP_TARGET/GITUP_REPO_PATH
    set correctly.
    """
    os.chdir(repo_path_context)

    marker = join(basepath, 'resolver-context.txt')
    script = make_context_capturing_script(repo_path_context, marker)

    from PyGitUp.gitup import GitUp
    gitup = GitUp(testing=True)
    gitup.settings['rebase.conflict-resolver'] = script

    # Move outside the repo before running: if the resolver's cwd were
    # ever accidentally inherited from the calling process instead of
    # passed explicitly, this would make that bug visible.
    os.chdir(basepath)

    gitup.run()

    assert 'rebasing' in gitup.states

    pwd, branch, target, repo_path = read_marker(marker)
    assert os.path.realpath(pwd) == os.path.realpath(
        repo_path_context.rstrip(os.sep)
    )
    assert branch == test_name_context
    assert target == 'origin/' + test_name_context
    assert os.path.realpath(repo_path) == os.path.realpath(
        repo_path_context.rstrip(os.sep)
    )


def test_resolver_in_worktree():
    """The resolver is also invoked for branches rebased via a worktree."""
    os.chdir(repo_path_worktree)

    marker = join(basepath, 'resolver-worktree-context.txt')
    script = make_context_capturing_script(worktree_path_worktree, marker)

    from PyGitUp.gitup import GitUp
    gitup = GitUp(testing=True)
    gitup.settings['rebase.conflict-resolver'] = script
    gitup.run()

    assert 'rebasing' in gitup.states

    pwd, branch, target, repo_path = read_marker(marker)
    assert os.path.realpath(pwd) == os.path.realpath(
        worktree_path_worktree.rstrip(os.sep)
    )
    assert branch == worktree_branch
    assert target == 'origin/' + test_name_worktree
    assert os.path.realpath(repo_path) == os.path.realpath(
        worktree_path_worktree.rstrip(os.sep)
    )
