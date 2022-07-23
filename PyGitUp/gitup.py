from git import Git
from git import GitCommandNotFound

__all__ = ['GitUp']

###############################################################################
# IMPORTS and LIBRARIES SETUP
###############################################################################

# Python libs
import argparse
import codecs
import errno
import sys
import os
import re
import json
import subprocess
from io import StringIO
from tempfile import NamedTemporaryFile
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

# 3rd party libs
try:
    # noinspection PyUnresolvedReferences
    import pkg_resources as pkg
except ImportError:  # pragma: no cover
    NO_DISTRIBUTE = True
else:  # pragma: no cover
    NO_DISTRIBUTE = False

import colorama
from git import Repo, GitCmdObjectDB
from termcolor import colored

# PyGitUp libs
from PyGitUp.utils import execute, uniq, find
from PyGitUp.git_wrapper import GitWrapper, GitError

ON_WINDOWS = sys.platform == 'win32'

###############################################################################
# Setup of 3rd party libs
###############################################################################

colorama.init(autoreset=True, convert=ON_WINDOWS)

###############################################################################
# Setup constants
###############################################################################

PYPI_URL = 'https://pypi.python.org/pypi/git-up/json'


###############################################################################
# GitUp
###############################################################################

def get_git_dir():
    toplevel_dir = execute(['git', 'rev-parse', '--show-toplevel'])

    if toplevel_dir is not None \
            and os.path.isfile(os.path.join(toplevel_dir, '.git')):
        # Not a normal git repo. Check if it's a submodule, then use
        # toplevel_dir. Otherwise it's a worktree, thus use  common_dir.
        # NOTE: git worktree support only comes with git v2.5.0 or
        # later, on earlier versions toplevel_dir is the best we can do.

        cmd = ['git', 'rev-parse', '--is-inside-work-tree']
        inside_worktree = execute(cmd, cwd=os.path.join(toplevel_dir, '..'))

        if inside_worktree == 'true' or Git().version_info[:3] < (2, 5, 0):
            return toplevel_dir
        else:
            return execute(['git', 'rev-parse', '--git-common-dir'])

    return toplevel_dir


class GitUp:
    """ Conainter class for GitUp methods """

    default_settings = {
        'fetch.prune': True,
        'fetch.all': False,
        'rebase.show-hashes': False,
        'rebase.arguments': None,
        'rebase.auto': True,
        'rebase.log-hook': None,
        'updates.check': True,
        'push.auto': False,
        'push.tags': False,
        'push.all': False,
    }

    def __init__(self, testing=False, sparse=False):
        # Sparse init: config only
        if sparse:
            self.git = GitWrapper(None)

            # Load configuration
            self.settings = self.default_settings.copy()
            self.load_config()
            return

        # Testing: redirect stderr to stdout
        self.testing = testing
        if self.testing:
            self.stderr = sys.stdout  # Quiet testing
        else:  # pragma: no cover
            self.stderr = sys.stderr

        self.states = []
        self.should_fetch = True
        self.pushed = False

        # Check, if we're in a git repo
        try:
            repo_dir = get_git_dir()
        except (OSError, GitCommandNotFound) as e:
            if isinstance(e, GitCommandNotFound) or e.errno == errno.ENOENT:
                exc = GitError("The git executable could not be found")
                raise exc
            else:
                raise
        else:
            if repo_dir is None:
                exc = GitError("We don't seem to be in a git repository.")
                raise exc

            self.repo = Repo(repo_dir, odbt=GitCmdObjectDB)

        # Check for branch tracking information
        if not any(b.tracking_branch() for b in self.repo.branches):
            exc = GitError("Can\'t update your repo because it doesn\'t has "
                           "any branches with tracking information.")
            self.print_error(exc)

            raise exc

        self.git = GitWrapper(self.repo)

        # target_map: map local branch names to remote tracking branches
        #: :type: dict[str, git.refs.remote.RemoteReference]
        self.target_map = dict()

        for branch in self.repo.branches:
            target = branch.tracking_branch()

            if target:
                if target.name.startswith('./'):
                    # Tracking branch is in local repo
                    target.is_local = True
                else:
                    target.is_local = False

                self.target_map[branch.name] = target

        # branches: all local branches with tracking information
        #: :type: list[git.refs.head.Head]
        self.branches = [b for b in self.repo.branches if b.tracking_branch()]
        self.branches.sort(key=lambda br: br.name)

        # remotes: all remotes that are associated with local branches
        #: :type: list[git.refs.remote.RemoteReference]
        self.remotes = uniq(
            # name = '<remote>/<branch>' -> '<remote>'
            [r.name.split('/', 2)[0]
             for r in list(self.target_map.values())]
        )

        # change_count: Number of unstaged changes
        self.change_count = len(
            self.git.status(porcelain=True, untracked_files='no').split('\n')
        )

        # Load configuration
        self.settings = self.default_settings.copy()
        self.load_config()

    def run(self):
        """ Run all the git-up stuff. """
        try:
            if self.should_fetch:
                self.fetch()

            self.rebase_all_branches()

            if self.settings['push.auto']:
                self.push()

        except GitError as error:
            self.print_error(error)

            # Used for test cases
            if self.testing:
                raise
            else:  # pragma: no cover
                sys.exit(1)
        except KeyboardInterrupt:
            sys.exit(130)

    def rebase_all_branches(self):
        """ Rebase all branches, if possible. """
        col_width = max(len(b.name) for b in self.branches) + 1
        if self.repo.head.is_detached:
            raise GitError("You're not currently on a branch. I'm exiting"
                           " in case you're in the middle of something.")
        original_branch = self.repo.active_branch

        with self.git.stasher() as stasher:
            for branch in self.branches:
                target = self.target_map[branch.name]

                # Print branch name
                if branch.name == original_branch.name:
                    attrs = ['bold']
                else:
                    attrs = []
                print(colored(branch.name.ljust(col_width), attrs=attrs),
                        end=' ')

                # Check, if target branch exists
                try:
                    if target.name.startswith('./'):
                        # Check, if local branch exists
                        self.git.rev_parse(target.name[2:])
                    else:
                        # Check, if remote branch exists
                        _ = target.commit

                except (ValueError, GitError):
                    # Remote branch doesn't exist!
                    print(colored('error: remote branch doesn\'t exist', 'red'))
                    self.states.append('remote branch doesn\'t exist')

                    continue

                # Get tracking branch
                if target.is_local:
                    target = find(self.repo.branches,
                                  lambda b: b.name == target.name[2:])

                # Check status and act appropriately
                if target.commit.hexsha == branch.commit.hexsha:
                    print(colored('up to date', 'green'))
                    self.states.append('up to date')

                    continue  # Do not do anything

                base = self.git.merge_base(branch.name, target.name)

                if base == target.commit.hexsha:
                    print(colored('ahead of upstream', 'cyan'))
                    self.states.append('ahead')

                    continue  # Do not do anything

                fast_fastforward = False
                if base == branch.commit.hexsha:
                    print(colored('fast-forwarding...', 'yellow'), end='')
                    self.states.append('fast-forwarding')
                    # Don't fast fast-forward the currently checked-out branch
                    fast_fastforward = (branch.name !=
                                        self.repo.active_branch.name)

                elif not self.settings['rebase.auto']:
                    print(colored('diverged', 'red'))
                    self.states.append('diverged')

                    continue  # Do not do anything
                else:
                    print(colored('rebasing', 'yellow'), end='')
                    self.states.append('rebasing')

                if self.settings['rebase.show-hashes']:
                    print(' {}..{}'.format(base[0:7],
                                           target.commit.hexsha[0:7]))
                else:
                    print()

                self.log(branch, target)
                if fast_fastforward:
                    branch.commit = target.commit
                else:
                    stasher()
                    self.git.checkout(branch.name)
                    self.git.rebase(target)

            if (self.repo.head.is_detached  # Only on Travis CI,
                    # we get a detached head after doing our rebase *confused*.
                    # Running self.repo.active_branch would fail.
                    or not self.repo.active_branch.name == original_branch.name):
                print(colored(f'returning to {original_branch.name}',
                              'magenta'))
                original_branch.checkout()

    def fetch(self):
        """
        Fetch the recent refs from the remotes.

        Unless git-up.fetch.all is set to true, all remotes with
        locally existent branches will be fetched.
        """
        fetch_kwargs = {'multiple': True}
        fetch_args = []

        if self.is_prune():
            fetch_kwargs['prune'] = True

        if self.settings['fetch.all']:
            fetch_kwargs['all'] = True
        else:
            if '.' in self.remotes:
                self.remotes.remove('.')

                if not self.remotes:
                    # Only local target branches,
                    # `git fetch --multiple` will fail
                    return

            fetch_args.append(self.remotes)

        try:
            self.git.fetch(*fetch_args, **fetch_kwargs)
        except GitError as error:
            error.message = "`git fetch` failed"
            raise error

    def push(self):
        """
        Push the changes back to the remote(s) after fetching
        """
        print('pushing...')
        push_kwargs = {}
        push_args = []

        if self.settings['push.tags']:
            push_kwargs['push'] = True

        if self.settings['push.all']:
            push_kwargs['all'] = True
        else:
            if '.' in self.remotes:
                self.remotes.remove('.')

                if not self.remotes:
                    # Only local target branches,
                    # `git push` will fail
                    return

            push_args.append(self.remotes)

        try:
            self.git.push(*push_args, **push_kwargs)
            self.pushed = True
        except GitError as error:
            error.message = "`git push` failed"
            raise error

    def log(self, branch, remote):
        """ Call a log-command, if set by git-up.fetch.all. """
        log_hook = self.settings['rebase.log-hook']

        if log_hook:
            if ON_WINDOWS:  # pragma: no cover
                # Running a string in CMD from Python is not that easy on
                # Windows. Running 'cmd /C log_hook' produces problems when
                # using multiple statements or things like 'echo'. Therefore,
                # we write the string to a bat file and execute it.

                # In addition, we replace occurrences of $1 with %1 and so forth
                # in case the user is used to Bash or sh.
                # If there are occurrences of %something, we'll replace it with
                # %%something. This is the case when running something like
                # 'git log --pretty=format:"%Cred%h..."'.
                # Also, we replace a semicolon with a newline, because if you
                # start with 'echo' on Windows, it will simply echo the
                # semicolon and the commands behind instead of echoing and then
                # running other commands

                # Prepare log_hook
                log_hook = re.sub(r'\$(\d+)', r'%\1', log_hook)
                log_hook = re.sub(r'%(?!\d)', '%%', log_hook)
                log_hook = re.sub(r'; ?', r'\n', log_hook)

                # Write log_hook to an temporary file and get it's path
                with NamedTemporaryFile(
                        prefix='PyGitUp.', suffix='.bat', delete=False
                ) as bat_file:
                    # Don't echo all commands
                    bat_file.file.write(b'@echo off\n')
                    # Run log_hook
                    bat_file.file.write(log_hook.encode('utf-8'))

                # Run bat_file
                state = subprocess.call(
                    [bat_file.name, branch.name, remote.name]
                )

                # Clean up file
                os.remove(bat_file.name)
            else:  # pragma: no cover
                # Run log_hook via 'shell -c'
                state = subprocess.call(
                    [log_hook, 'git-up', branch.name, remote.name],
                    shell=True
                )

            if self.testing:
                assert state == 0, 'log_hook returned != 0'

    def version_info(self):
        """ Tell, what version we're running at and if it's up to date. """

        # Retrive and show local version info
        package = pkg.get_distribution('git-up')
        local_version_str = package.version
        local_version = package.parsed_version

        print('GitUp version is: ' + colored('v' + local_version_str, 'green'))

        if not self.settings['updates.check']:
            return

        # Check for updates
        print('Checking for updates...', end='')

        try:
            # Get version information from the PyPI JSON API
            reader = codecs.getreader('utf-8')
            details = json.load(reader(urlopen(PYPI_URL)))
            online_version = details['info']['version']
        except (HTTPError, URLError, ValueError):
            recent = True  # To not disturb the user with HTTP/parsing errors
        else:
            recent = local_version >= pkg.parse_version(online_version)

        if not recent:
            # noinspection PyUnboundLocalVariable
            print(
                '\rRecent version is: '
                + colored('v' + online_version, color='yellow', attrs=['bold'])
            )
            print('Run \'pip install -U git-up\' to get the update.')
        else:
            # Clear the update line
            sys.stdout.write('\r' + ' ' * 80 + '\n')

    ###########################################################################
    # Helpers
    ###########################################################################

    def load_config(self):
        """
        Load the configuration from git config.
        """
        for key in self.settings:
            value = self.config(key)
            # Parse true/false
            if value == '' or value is None:
                continue  # Not set by user, go on
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            elif value:
                pass  # A user-defined string, store the value later

            self.settings[key] = value

    def config(self, key):
        """ Get a git-up-specific config value. """
        return self.git.config(f'git-up.{key}')

    def is_prune(self):
        """
        Return True, if `git fetch --prune` is allowed.

        Because of possible incompatibilities, this requires special
        treatment.
        """
        required_version = "1.6.6"
        config_value = self.settings['fetch.prune']

        if self.git.is_version_min(required_version):
            return config_value is not False
        else:  # pragma: no cover
            if config_value == 'true':
                print(colored(
                    "Warning: fetch.prune is set to 'true' but your git"
                    "version doesn't seem to support it ({} < {})."
                    "Defaulting to 'false'.".format(self.git.version,
                                                    required_version),
                    'yellow'
                ))

    def print_error(self, error):
        """
        Print more information about an error.

        :type error: GitError
        """
        print(colored(error.message, 'red'), file=self.stderr)

        if error.stdout or error.stderr:
            print(file=self.stderr)
            print("Here's what git said:", file=self.stderr)
            print(file=self.stderr)

            if error.stdout:
                print(error.stdout, file=self.stderr)
            if error.stderr:
                print(error.stderr, file=self.stderr)

        if error.details:
            print(file=self.stderr)
            print("Here's what we know:", file=self.stderr)
            print(str(error.details), file=self.stderr)
            print(file=self.stderr)


###############################################################################


EPILOG = '''
For configuration options, please see
https://github.com/msiemens/PyGitUp#readme.

\b
Python port of https://github.com/aanand/git-up/
Project Author: Markus Siemens <markus@m-siemens.de>
Project URL: https://github.com/msiemens/PyGitUp
\b
'''


def run():  # pragma: no cover
    """
    A nicer `git pull`.
    """

    parser = argparse.ArgumentParser(description="A nicer `git pull`.", epilog=EPILOG)
    parser.add_argument('-V', '--version', action='store_true',
                        help='Show version (and if there is a newer version).')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='Be quiet, only print error messages.')
    parser.add_argument('--no-fetch', '--no-f', dest='fetch', action='store_false',
                        help='Don\'t try to fetch from origin.')
    parser.add_argument('-p', '--push', action='store_true',
                        help='Push the changes after pulling successfully.')

    args = parser.parse_args()

    if args.version:
        if NO_DISTRIBUTE:
            print(colored('Please install \'git-up\' via pip in order to '
                          'get version information.', 'yellow'))
        else:
            GitUp(sparse=True).version_info()
        return

    if args.quiet:
        sys.stdout = StringIO()

    try:
        gitup = GitUp()
        gitup.settings['push.auto'] = args.push
        gitup.should_fetch = args.fetch
    except GitError:
        sys.exit(1)  # Error in constructor
    else:
        gitup.run()


if __name__ == '__main__':  # pragma: no cover
    run()
