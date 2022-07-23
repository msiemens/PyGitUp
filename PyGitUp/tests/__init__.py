from os.path import join
from tempfile import mkdtemp

import contextlib
import os
from git import *

basepath = mkdtemp(prefix='PyGitUp.')
testfile_name = 'file.txt'


@contextlib.contextmanager
def capture():
    import sys
    from io import StringIO
    oldout, olderr = sys.stdout, sys.stderr
    out = None
    try:
        out = [StringIO(), StringIO()]
        sys.stdout, sys.stderr = out
        yield out
    finally:
        sys.stdout, sys.stderr = oldout, olderr
        if out:
            out[0] = out[0].getvalue()
            out[1] = out[1].getvalue()


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


# noinspection PyDefaultArgument
def update_file(repo, commit_message='', counter=[0], filename=testfile_name):
    """
    Update 'testfile_name' using an increasing counter and commit the changes.
    """
    counter[0] += 1  # See: http://stackoverflow.com/a/279592/997063

    path_file = join(repo.working_dir, filename)
    contents = f'line 1\nline 2\ncounter: {counter[0]}'
    write_file(path_file, contents)

    repo.index.add([path_file])
    repo.index.commit(commit_message)

    return path_file

def mkrepo(path):
    """
    Make a repository in 'path', create the the dir, if it doesn't exist.
    """
    return Repo.init(path)


def init_master(test_name):
    """
    Initialize the master repo and create & commit a file.
    """
    # Create repo
    path = join(basepath, 'master.' + test_name)
    repo = mkrepo(path)

    assert repo.working_dir == path

    # Add file
    update_file(repo, 'Initial commit')
    repo.git.checkout(b='initial')

    return path, repo
