# System imports
import os
import platform
from os.path import join

from git import Repo, GitCmdObjectDB
from PyGitUp.tests import basepath, init_master, update_file

test_name = 'log-hook-injection'
repo_path = join(basepath, test_name + os.sep)
marker_path = '/tmp/gitup_log_hook_injection_marker'
captured_arg_path = '/tmp/gitup_log_hook_arg'


def setup_module():
    master_path, master = init_master(test_name)

    # Prepare master repo with a branch name that includes command substitution syntax
    # Allowed by git-check-ref-format (no spaces, only allowed punctuation).
    branch_name = 'poc$(cat</dev/null>' + marker_path + ')'
    master.git.checkout(b=branch_name)

    # Clone to test repo
    path = join(basepath, test_name)
    master.clone(path, b=branch_name)
    repo = Repo(path, odbt=GitCmdObjectDB)

    assert repo.working_dir == path

    # Set git-up.rebase.log-hook with unquoted $1 to mirror risky usage
    if platform.system() == 'Windows':
        hook = f'echo %1 > {captured_arg_path}'
    else:
        hook = f'printf %s \"$1\" > {captured_arg_path}'
    repo.git.config('git-up.rebase.log-hook', hook)

    # Modify file in master to force a fast-forward in the clone
    update_file(master, test_name)


def teardown_module():
    if os.path.exists(marker_path):
        os.remove(marker_path)
    if os.path.exists(captured_arg_path):
        os.remove(captured_arg_path)


def test_log_hook_injection_is_escaped():
    """Ensure branch names containing $(...) are escaped before reaching the log hook."""
    if os.path.exists(marker_path):
        os.remove(marker_path)
    if os.path.exists(captured_arg_path):
        os.remove(captured_arg_path)

    os.chdir(repo_path)

    from PyGitUp.gitup import GitUp
    gitup = GitUp(testing=True)
    gitup.run()

    # Without escaping, the raw branch name would be written.
    # With escaping, $ and ` are backslash-escaped.
    expected = 'poc\\$(cat</dev/null>' + marker_path + ')'
    with open(captured_arg_path, 'r') as f:
        written = f.read()
    assert written == expected

    # Ensure payload did not execute (marker file not created)
    assert not os.path.exists(marker_path)

    # Sanity: normal fast-forward happened
    assert len(gitup.states) == 1
    assert gitup.states[0] == 'fast-forwarding'
