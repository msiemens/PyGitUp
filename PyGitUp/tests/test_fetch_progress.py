from os import chdir, sep
from os.path import join, normpath

from git import GitCmdObjectDB, Repo

from PyGitUp.tests import basepath, capture, init_master


TEST_NAME = 'fetch-progress'
REPO_PATH = join(basepath, TEST_NAME + sep)


def setup_module():
    _, master = init_master(TEST_NAME)

    master.git.checkout(b=TEST_NAME)
    master.clone(REPO_PATH, b=TEST_NAME)
    master.git.checkout(b='new-remote-branch')

    repo = Repo(REPO_PATH, odbt=GitCmdObjectDB)
    assert repo.working_dir == normpath(REPO_PATH)


def test_fetch_progress():
    chdir(REPO_PATH)
    repo = Repo(REPO_PATH, odbt=GitCmdObjectDB)

    from PyGitUp.gitup import GitUp

    def fetch_output(progress=False, quiet=False):
        repo.git.update_ref('-d', 'refs/remotes/origin/new-remote-branch')
        repo.git.config('git-up.fetch.progress', str(progress).lower())

        with capture() as output:
            gitup = GitUp(quiet=quiet)
            gitup.fetch()

        return output[1]

    assert 'new-remote-branch' not in fetch_output()
    assert 'new-remote-branch' in fetch_output(progress=True)
    assert 'new-remote-branch' not in fetch_output(progress=True, quiet=True)
