# System imports
import os
import platform
import subprocess
from os.path import join

from git import *
from nose.plugins.skip import SkipTest

from PyGitUp.tests import basepath, write_file, init_master

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
    shell = True if platform.system() == 'Windows' else False

    if os.environ.get('TRAVIS', False):
        raise SkipTest('Skip this test on Travis CI :(')

    # Helper methods
    def is_installed(prog):
        dev_null = open(os.devnull, 'wb')
        try:
            return_value = subprocess.call([prog, '--version'], shell=shell,
                                           stdout=dev_null, stderr=dev_null)
            return return_value == 0
        except OSError:
            return False

    def get_output(cmd):
        return str(subprocess.check_output(cmd, shell=shell))

    # Check for ruby and bundler
    if not (is_installed('ruby') and is_installed('gem')
            and 'bundler' in get_output(['gem', 'list'])):

        # Ruby not installed, skip test
        raise SkipTest('Ruby not installed, skipped Bundler integration test')

    os.chdir(repo_path)

    from PyGitUp.gitup import GitUp
    gitup = GitUp(testing=True)
    gitup.run()
