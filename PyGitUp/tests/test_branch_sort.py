import os
import sys
from os.path import join

from git import GitCmdObjectDB, Repo

from PyGitUp.tests import basepath, init_master, update_file


test_name = 'branch-sort'
repo_path = join(basepath, test_name + os.sep)


def setup_module():
    master_path, master = init_master(test_name)

    branches = [
        ('a-old', '2001-01-01T00:00:00+00:00'),
        ('z-new', '2003-01-01T00:00:00+00:00'),
        ('m-middle', '2002-01-01T00:00:00+00:00'),
    ]
    for branch_name, commit_date in branches:
        master.git.checkout('initial')
        master.git.checkout(b=branch_name)
        update_file(master, branch_name)
        master.git.commit(
            '--amend', '--no-edit',
            env={
                'GIT_AUTHOR_DATE': commit_date,
                'GIT_COMMITTER_DATE': commit_date,
            },
        )

    master.clone(repo_path, b='a-old')
    repo = Repo(repo_path, odbt=GitCmdObjectDB)
    for branch_name, _ in branches[1:]:
        repo.git.branch('--track', branch_name, f'origin/{branch_name}')


def branch_names(branch_sort=None):
    from PyGitUp.gitup import GitUp

    os.chdir(repo_path)
    return [branch.name for branch in GitUp(
        testing=True, branch_sort=branch_sort
    ).branches]


def unset_sort_config(repo):
    for key in ('branch.sort', 'git-up.branch.sort'):
        try:
            repo.git.config('--unset-all', key)
        except Exception:
            pass


def test_branches_are_alphabetical_by_default(monkeypatch):
    from PyGitUp.git_wrapper import GitWrapper

    repo = Repo(repo_path)
    unset_sort_config(repo)
    monkeypatch.setattr(
        GitWrapper,
        'for_each_ref',
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError('default sorting must not invoke git for-each-ref')
        ),
        raising=False,
    )

    assert branch_names() == ['a-old', 'm-middle', 'z-new']


def test_native_branch_sort_does_not_change_default():
    repo = Repo(repo_path)
    unset_sort_config(repo)
    repo.git.config('branch.sort', '-committerdate')

    assert branch_names() == ['a-old', 'm-middle', 'z-new']


def test_git_up_branch_sort_overrides_native_config():
    repo = Repo(repo_path)
    unset_sort_config(repo)
    repo.git.config('branch.sort', '-committerdate')
    repo.git.config('git-up.branch.sort', 'refname')

    assert branch_names() == ['a-old', 'm-middle', 'z-new']


def test_cli_branch_sort_overrides_config(monkeypatch):
    from PyGitUp import gitup

    repo = Repo(repo_path)
    unset_sort_config(repo)
    repo.git.config('git-up.branch.sort', 'refname')
    os.chdir(repo_path)

    recorded = []
    monkeypatch.setattr(
        gitup.GitUp,
        'run',
        lambda self: recorded.extend(branch.name for branch in self.branches),
    )
    monkeypatch.setattr(
        sys, 'argv', ['git-up', '--branch-sort=-committerdate']
    )

    gitup.run()

    assert recorded == ['z-new', 'm-middle', 'a-old']
