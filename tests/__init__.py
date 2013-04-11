# coding=utf-8

"""
Set up the GIT test environment.
master: the master repo.
test-*: clone for a specific test
"""

import os
from os.path import join
from tempfile import mkdtemp

from git import *

basepath = mkdtemp(prefix='PyGitUp.')
testfile_name = 'file.txt'


def teardown():
    """
     Cleanup created files
    """
    import shutil
    import stat

    def onerror(func, path, exc_info):

        if not os.access(path, os.W_OK):
            os.chmod(path, stat.S_IWUSR)
            func(path)
        else:
            raise

    os.chdir(join(basepath, '..'))
    shutil.rmtree(basepath, onerror=onerror)


def write_file(path, contents):
    with open(path, 'w+') as f:
        f.write(contents)


def init_git(path):
    os.chdir(path)
    os.popen('git init').read()


def mkrepo(path):
    if not os.path.exists(path):
        os.makedirs(path, 0700)
    init_git(path)


def init_master(test_name):
    # Create repo
    path = join(basepath, 'master.' + test_name)
    mkrepo(path)
    repo = Repo(path)

    assert repo.working_dir == path

    # Add file
    path_file = join(path, testfile_name)
    write_file(path_file, 'line 1\nline 2\ncounter: 1')

    repo.index.add([path_file])
    repo.index.commit('Initial commit')
    repo.git.checkout('head', b='initial')

    return path, repo

