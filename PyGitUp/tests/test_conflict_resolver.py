# System imports
import os
import stat
from os.path import join

import pytest
from git import *
from PyGitUp.git_wrapper import RebaseError, UnresolvedConflictError
from PyGitUp.tests import basepath, write_file, init_master, update_file, \
    testfile_name

test_name_success = 'conflict_resolve_success'
test_name_fail = 'conflict_resolve_fail'
test_name_noresolver = 'conflict_no_resolver'

repo_path_success = join(basepath, test_name_success + os.sep)
repo_path_fail = join(basepath, test_name_fail + os.sep)
repo_path_noresolver = join(basepath, test_name_noresolver + os.sep)


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


def setup_module():
    global master_success, repo_success
    global master_fail, repo_fail
    global master_noresolver, repo_noresolver

    master_success, repo_success = setup_conflict_repo(test_name_success)
    master_fail, repo_fail = setup_conflict_repo(test_name_fail)
    master_noresolver, repo_noresolver = setup_conflict_repo(
        test_name_noresolver
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
    gitup.settings['rebase.conflict-resolver'] = script + ' {prompt}'
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
    gitup.settings['rebase.conflict-resolver'] = script + ' {prompt}'

    with pytest.raises(UnresolvedConflictError):
        gitup.run()


def test_no_resolver():
    """Without a resolver, RebaseError is raised as before."""
    os.chdir(repo_path_noresolver)

    from PyGitUp.gitup import GitUp
    gitup = GitUp(testing=True)

    with pytest.raises(RebaseError):
        gitup.run()


def test_prompt_content():
    """Prompt includes branch name, target, and instructions."""
    from PyGitUp.gitup import GitUp
    os.chdir(repo_path_success)

    gitup = GitUp(testing=True)
    prompt = gitup._build_resolver_prompt(
        'my-branch', 'origin/main', repo_path_success
    )

    assert 'my-branch' in prompt
    assert 'origin/main' in prompt
    assert 'Resolve the git rebase conflicts' in prompt
