# System imports
import os
import sys
from os.path import join

from git import *
from PyGitUp.tests import basepath, init_master, update_file

test_name = 'push-auto'
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

    # Modify file in master
    update_file(master, test_name)


def run_cli(monkeypatch, argv):
    """ Run the command line entry point and return the settings it used. """
    from PyGitUp import gitup

    recorded = {}

    def fake_run(self):
        recorded.update(self.settings)

    monkeypatch.setattr(gitup.GitUp, 'run', fake_run)
    monkeypatch.setattr(sys, 'argv', argv)

    gitup.run()

    return recorded


def test_push_auto_from_config_is_kept(monkeypatch):
    """ Run 'git up' without '--push' and keep git-up.push.auto """
    os.chdir(repo_path)
    Repo(repo_path).git.config('git-up.push.auto', 'true')

    assert run_cli(monkeypatch, ['git-up'])['push.auto'] is True


def test_push_argument_enables_pushing(monkeypatch):
    """ Run 'git up --push' with git-up.push.auto turned off """
    os.chdir(repo_path)
    Repo(repo_path).git.config('git-up.push.auto', 'false')

    assert run_cli(monkeypatch, ['git-up', '--push'])['push.auto'] is True


def test_push_auto_off_by_default(monkeypatch):
    """ Run 'git up' without '--push' and without git-up.push.auto """
    os.chdir(repo_path)
    Repo(repo_path).git.config('git-up.push.auto', 'false')

    assert run_cli(monkeypatch, ['git-up'])['push.auto'] is False
