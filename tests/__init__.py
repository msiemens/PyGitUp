# coding=utf-8

"""
Set up the GIT test environment.
master: the master repo.
test-*: clone for a specific test
"""

import os
import sys

from contextlib import contextmanager
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


def _write_file(path, contents):
    with open(path, 'w+') as f:
        f.write(contents)


def _init_git(path):
    os.chdir(path)
    os.popen('git init').read()


def _mkrepo(path):
    if not os.path.exists(path):
        os.makedirs(path, 0700)
    _init_git(path)


def _setup_master():
    # Create repo
    path = join(basepath, 'master')
    _mkrepo(path)
    repo = Repo(path)

    assert repo.working_dir == path

    # Add file
    path_file = join(path, testfile_name)
    _write_file(path_file, 'line 1\nline 2\ncounter: 1')

    repo.index.add([path_file])
    repo.index.commit('Initial commit')


def _setup_test3():
    master_path = join(basepath, 'master')
    master = Repo(master_path)

    # Prepare master repo
    master.git.checkout('head', b='test-3')

    # Clone to test-3 repo
    path = join(basepath, 'test-3')

    master.clone(path, b='test-3')
    repo = Repo(path, odbt=GitCmdObjectDB)

    assert repo.working_dir == path

    # Create checkpoint
    repo.git.checkout('head', b='checkpoint')

    # Modify file in master
    master_path_file = join(master_path, testfile_name)
    _write_file(master_path_file , 'line 1\nline 2\ncounter: 2')
    master.index.add([master_path_file])
    master.index.commit('Test 3')

    # Modify file in test-3 and commit
    path_file = join(path, testfile_name)
    _write_file(path_file , 'line 1\nline 2\ncounter: 3')
    repo.index.add([path_file])
    repo.index.commit('Test 3')

    # Modify file in test-3 and stash
    path_file = join(path, testfile_name)
    _write_file(path_file, 'conflict!')

    repo.git.stash()


def setup():
    _setup_master()
    _setup_test3()
    pass
