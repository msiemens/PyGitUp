# System imports
import socket

import pytest

from PyGitUp.tests import capture

test_name = 'version'


def test_version():
    """ Run 'git up': Check version """
    try:
        from importlib import metadata
    except ImportError:
        pytest.skip('pip not installed')

    try:
        socket.gethostbyname('pypi.python.org')
    except OSError:
        pytest.skip('Can\'t connect to PYPI')

    from PyGitUp.gitup import GitUp
    with capture() as [stdout, _]:
        GitUp(sparse=True).version_info()
    stdout = stdout.getvalue()

    local_version_str = metadata.version('git-up')

    assert local_version_str in stdout
