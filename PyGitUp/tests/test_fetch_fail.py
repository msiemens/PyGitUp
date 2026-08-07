# System imports
import os
from io import BytesIO
from os.path import join

import pytest
from git import *
from PyGitUp.git_wrapper import GitError, GitWrapper
from PyGitUp.tests import basepath, capture, init_master, update_file

test_name = 'test-fail'
repo_path = join(basepath, test_name + os.sep)


def setup_module():
    master_path, master = init_master(test_name)

    # Prepare master repo
    master.git.checkout(b=test_name)

    # Clone to test repo
    path = join(basepath, test_name)

    master.clone(path, b=test_name)
    repo = Repo(path, odbt=GitCmdObjectDB)

    assert repo.working_dir == path

    # Set remote
    repo.git.remote('set-url', 'origin', 'does-not-exist')

    # Modify file in master
    update_file(master, test_name)


def test_fetch_fail():
    """ Run 'git up' with a non-existent remote """
    os.chdir(repo_path)
    repo = Repo(repo_path, odbt=GitCmdObjectDB)

    from PyGitUp.gitup import GitUp

    def fetch_error(progress=False, quiet=False):
        repo.git.config('git-up.fetch.progress', str(progress).lower())

        with capture() as output:
            gitup = GitUp(testing=True, quiet=quiet)

            with pytest.raises(GitError) as exc_info:
                gitup.run()

        return exc_info.value, output[0]

    for progress, quiet in ((False, False), (True, False), (True, True)):
        error, output = fetch_error(progress=progress, quiet=quiet)

        assert isinstance(error.stderr, str)
        assert 'does-not-exist' in error.stderr
        assert output.count('does not appear to be a git repository') == 1
        assert error.stderr_already_output is (progress and not quiet)


def test_fetch_error_uses_gitpython_stderr_as_fallback():
    class FailingCommand:
        stdout = BytesIO()
        stderr = BytesIO()

        @staticmethod
        def wait():
            raise GitCommandError(
                ['git', 'fetch'],
                1,
                stderr='fallback-message',
            )

    with pytest.raises(GitError) as exc_info:
        GitWrapper.run_cmd(FailingCommand())

    assert 'fallback-message' in exc_info.value.stderr
