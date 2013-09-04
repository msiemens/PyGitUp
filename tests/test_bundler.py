# System imports
import os
import subprocess
from os.path import join

# 3rd party libs
from nose.plugins.skip import SkipTest
from git import *

# PyGitup imports
from tests import basepath, write_file, init_master

test_name = 'bundler'
repo_path = join(basepath, test_name + os.sep)


def setup():
    master_path, master = init_master(test_name)

    # Prepare master repo
    master.git.checkout(b=test_name)

    # Add Gemfile
    gemfile = join(master_path, 'Gemfile')
    write_file(gemfile, "source 'https://rubygems.org'\ngem 'colored'")
    master.index.add([gemfile])
    master.index.commit(test_name)

    # Clone to test repo
    path = join(basepath, test_name)

    master.clone(path, b=test_name)
    repo = Repo(path, odbt=GitCmdObjectDB)
    repo.git.config('git-up.bundler.check', 'true')

    assert repo.working_dir == path


def test_bundler():
    """ Run bundler integration """
    if os.environ.get('TRAVIS', False):
        raise SkipTest('Skip this test on Travis CI :(')

    def is_installed(prog):
        dev_null = open(os.devnull, 'wb')
        return_value = subprocess.call([prog, '--version'], shell=True,
                                       stdout=dev_null, stderr=dev_null)
        return return_value == 0

    if not (is_installed('ruby') and is_installed('gem')):
        # Ruby not installed, skip test
        raise SkipTest('Ruby not installed, skipped Bundler integration test')

    os.chdir(repo_path)

    from PyGitUp.gitup import GitUp
    gitup = GitUp(testing=True)
    gitup.run()

