# coding=utf-8
import os
from os.path import join
from tempfile import mkdtemp
from functools import wraps

from nose.plugins.attrib import attr
from nose.plugins.skip import SkipTest
from git import *

basepath = mkdtemp(prefix='PyGitUp.')
testfile_name = 'file.txt'


def wip(f):
    @wraps(f)
    def run_test(*args, **kwargs):
        try:
            f(*args, **kwargs)
        except Exception as e:
            raise SkipTest("WIP test failed: " + str(e))
        raise AssertionError("Passing test marked as WIP")
    return attr('wip')(run_test)


def setup():
    global repo
    mkrepo(basepath)
    repo = Repo(basepath)
    update_file(repo, 'Initial commit')
    repo.git.checkout(b='initial')


def teardown():
    """
     Cleanup created files and directories
    """
    import shutil
    import stat

    def onerror(func, path, _):

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


#noinspection PyDefaultArgument
def update_file(repo, commit_message='', counter=[0]):
    """
    Update 'testfile_name' using an increasing counter and commit the changes.
    """
    counter[0] += 1  # See: http://stackoverflow.com/a/279592/997063

    path_file = join(repo.working_dir, testfile_name)
    contents = 'line 1\nline 2\ncounter: {0}'.format(counter[0])
    write_file(path_file, contents)

    repo.index.add([path_file])
    repo.index.commit(commit_message)

    return path_file


def init_git(path):
    """
    Create a git repo in the given dir.
    """
    os.chdir(path)
    os.popen('git init').read()


def mkrepo(path):
    """
    Make a repository in 'path', create the the dir, if it doesn't exist.
    """
    if not os.path.exists(path):
        os.makedirs(path, 0700)
    init_git(path)


def init_master(test_name):
    """
    Initialize the master repo and create & commit a file.
    """
    # Create repo
    repo.git.checkout('initial', f=True)

    return basepath, repo

