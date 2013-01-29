###############################################################################
# PyGitUp
# -----------------------------------------------------------------------------
# DESCRIPION: TODO
# AUTHOR: Markus Siemens <markus@m-siemens.de>
# URL: https://github.com/msiemens/PyGitUp
###############################################################################

__all__ = ['GitUp']

###############################################################################
# IMPORTS and LIBRARIES SETUP
###############################################################################

# Python libs
import sys
from contextlib import contextmanager
import subprocess

# 3rd party libs
import colorama
from termcolor import colored

from git import *

# PyGitUp libs
from PyGitUp.utils import *
from PyGitUp.git_wrapper import git_wrapper

###############################################################################
# Setup of 3rd party libs
###############################################################################

colorama.init(autoreset=True)

###############################################################################
# GitUp
###############################################################################

# Initialize frequently used globals
try:
    path = execute('git rev-parse --show-toplevel')
except Exception as e:
    print colored("We don't seem to be in a git repository.", 'red')
    sys.exit(1)

repo = Repo(path, odbt=GitCmdObjectDB)
git = git_wrapper(repo)


class GitUp(object):

    def __init__(self):
        # remote_map: map local branch names to remote branches
        self.remote_map = dict()

        for branch in repo.branches:
            remote = git.remote_ref_for_branch(branch)
            if remote:
                self.remote_map[branch.name] = remote

        # branches: all local branches that has a corresponding remote branch
        self.branches = [
            branch for branch in repo.branches
                if branch.name in self.remote_map.keys()
        ]
        self.branches.sort(key=lambda b: b.name)

        # remotes: all remotes that are associated with local branches
        self.remotes = uniq(
            [r.name.split('/', 2)[0] for r in self.remote_map.values()]
        )

        # change_count
        self.change_count = len(
            git.status(porcelain=True, untracked_files='no').split('\n')
        )

    def run(self):
        """ Run all the git-up stuff. """
        try:
            self.fetch()

            with git.stash():
                with self.returning_to_current_branch():
                    self.rebase_all_branches()

        except GitCommandError as error:
            print error
            raise error  # TODO: error handling

    def rebase_all_branches(self):
        """ Rebase all branches, if possible. """
        col_width = max([len(b.name) for b in self.branches]) + 1

        for branch in self.branches:
            remote = self.remote_map[branch.name]
            print colored(branch.name.ljust(col_width), attrs=['bold']),

            if remote.commit.hexsha == branch.commit.hexsha:
                print colored('up to date', 'green')
                continue

            base = git.merge_base(branch.name, remote.name)

            if base == remote.commit.hexsha:
                print colored('ahead of upstream', 'green')
                continue

            if base == branch.commit.hexsha:
                print colored('fast-forwarding...', 'yellow')
            elif self.config('rebase.auto') == 'false':
                print colored('diverged', 'red')
                continue
            else:
                print colored('rebasing', 'yellow')

            self.log(branch, remote)
            git.checkout(branch.name)
            git.rebase(remote)

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

        if self.config('fetch.all'):
            fetch_kwargs['all'] = True
        else:
            fetch_args.append(self.remotes)

        git.fetch(tostdout=True, *fetch_args, **fetch_kwargs)

    def log(self, branch, remote):
        """ Call a log-command, if set by git-up.fetch.all. """
        log_hook = self.config('rebase.log-hook')
        if log_hook:
            subprocess.call(
                [log_hook, 'git-up', branch.name, remote.name],
                shell=True
            )

    ###########################################################################
    # Helpers
    ###########################################################################

    @contextmanager
    def returning_to_current_branch(self):
        """ A contextmanager returning to the current branch. """
        if repo.head.is_detached:
            print colored("ou're not currently on a branch. "
            "I'm exiting in case you're in the middle of something.", 'red')
            sys.exit(1)

        branch_name = repo.active_branch.name

        yield

        print colored('returning to {}'.format(branch_name), 'magenta')

    def config(self, key):
        """ Get a git-up-specific config value. """
        return git.config('git-up.{}'.format(key))

    def is_prune(self):
        """
        Return True, if `git fetch --prune` is allowed.

        Because of possible incompatibilities, this requires special
        treatment.
        """
        required_version = "1.6.6"
        config_value = self.config("fetch.prune")

        if git.is_version_min(required_version):
            return config_value != 'false'
        else:
            if config_value == 'true':
                print colored(
                    "Warning: fetch.prune is set to 'true' but your git "
                    "version doesn't seem to support it ({} < {}). Defaulting"
                    " to 'false'.".format(git.version(), required_version),
                    'yellow'
                )


def run():
    GitUp().run()

if __name__ == '__main__':
    run()
