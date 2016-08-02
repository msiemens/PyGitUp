# System imports
import socket

from nose.plugins.skip import SkipTest
from nose.tools import *

from PyGitUp.tests import capture

test_name = 'version'


def test_version():
    """ Run 'git up': Check version """
    try:
        import pkg_resources as pkg
    except ImportError:
        raise SkipTest('pip not installed')

    try:
        socket.gethostbyname('pypi.python.org')
    except socket.error:
        raise SkipTest('Can\'t connect to PYPI')

    from PyGitUp.gitup import GitUp
    with capture() as [stdout, _]:
        GitUp(sparse=True).version_info()
    stdout = stdout.getvalue()

    package = pkg.get_distribution('git-up')
    local_version_str = package.version

    assert_in(local_version_str, stdout)


