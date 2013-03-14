# coding=utf-8

"""
Set up the GIT test environment.
Master: the master repo.
test-*: clone for a specific test
"""

import sys
import os
from os.path import dirname, abspath, relpath, join
import shutil

from git import *

basepath = dirname(abspath(__file__))
testfile_name = 'file.txt'


def _clear_folder(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)


def _write_file(path, contents):
    with open(path, 'w+') as f:
        f.write(contents)


def _init_git(path):
    cwd = os.getcwd()
    os.chdir(path)
    os.system('git init')
    os.chdir(cwd)


def setup_master():
    # Initialize repo
    path = join(basepath, 'master')
    _clear_folder(path)

    _init_git(path)

    repo = Repo(path)

    assert repo.working_dir == path

    # Add file
    path_file = join(path, testfile_name)
    _write_file(path_file, 'line 1\nline 2\ncounter: 1')

    repo.index.add([path_file])
    repo.index.commit('Initial commit')


def setup_test3():
    master_path = join(basepath, 'master')
    master = Repo(master_path, odbt=GitCmdObjectDB)

    # Prepare master repo
    master.git.checkout('head', b='test-3')

    # Clone to test-3 repo
    path = join(basepath, 'test-3')
    _clear_folder(path)

    master.clone(path)
    repo = Repo(path)

    assert repo.working_dir == path

    # Create checkpoint
    repo.git.checkout('head', b='checkpoint')

    # Modify file in master
    master_path_file = join(master_path, testfile_name)
    _write_file(master_path_file , 'line 1\nline 2\ncounter: 2')
    master.index.commit('Test 3')

    # Modify file in test-3 and stash
    path_file = join(path, testfile_name)
    _write_file(path_file, 'line 1\nline 2\ncounter: 2')

    repo.git.stash()


def setup():
    print >> sys.stderr, 'HERE!!!'
    setup_master()
    setup_test3()