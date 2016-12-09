import os
import sys
from contextlib import contextmanager
from datetime import datetime

import git

# VARIABBLES DEFINITIONS
root_dir = os.path.dirname(__file__)
repo = git.Repo(root_dir)

# ASSERTIONS
# assert not repo.is_dirty(), 'Repo {} is dirty!'.format(root_dir)

# METHODS


def get_branch(name):
    return [b for b in repo.branches if b.name == name][0]


def current_version():
    """
    Get the current version number from setup.py
    """
    # Monkeypatch setuptools.setup so we get the verison number
    import setuptools

    version = [None]

    def monkey_setup(**settings):
        version[0] = settings['version']

    old_setup = setuptools.setup
    setuptools.setup = monkey_setup

    import setup  # setup.py
    reload(setup)
    setuptools.setup = old_setup

    return version[0]


def update_changelog(changes, new_version):
    readme_path = os.path.join(root_dir, 'README.rst')

    to_append = 'v' + new_version
    to_append += ' (*' + datetime.now().strftime('%Y-%m-%d') + '*)' + '\n'
    to_append += '~' * (len(to_append) - 1) + '\n'
    to_append += '\n'
    to_append += changes.strip() + '\n'

    new_file = []
    changelog_found = False

    with open(readme_path) as f:
        for l in f:
            line = l.strip()
            if line == 'Changelog':
                print 'Found changelog!'
                changelog_found = True
                new_file.append(line)
                continue
            elif changelog_found and line == '---------':
                print 'Found seperator!'
                new_file.append(line)
                new_file.append('')
                new_file.extend(to_append.splitlines())
            else:
                new_file.append(line)

    with open(readme_path, 'w') as f:
        f.writelines(new_file)


def show_diff():
    print repo.git.diff()


def merge(new_version):
    # git checkout master
    get_branch('master').checkout()
    # git merge --no-ff dev
    repo.git.merge('def', no_ff=True)
    # git tag vX.X
    repo.git.tag('v' + new_version)


def push():
    repo.git.push()
    repo.git.push(tags=True)


def upload_package():
    _argv = sys.argv
    sys.argv = ['__main__', 'sdist', 'upload']

    import setup
    reload(setup)
    sys.argv = _argv


@contextmanager
def returning_to_dev():
    yield
    repo.git.checkout('dev')
