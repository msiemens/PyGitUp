# coding=utf-8
"""
Python implementation of git-up.

Why use git-up? ``git pull` has two problems:
  - It merges upstream changes by default, when it's really more polite to
    rebase over them, unless your collaborators enjoy a commit graph that
    looks like bedhead.
  - It only updates the branch you're currently on, which means git push
    will shout at you for being behind on branches you don't particularly
    care about right now.
(from the orignial git-up https://github.com/aanand/git-up/)

Project Author: Markus Siemens <markus@m-siemens.de>
Project URL: https://github.com/msiemens/PyGitUp
"""

from __future__ import print_function

__all__ = ['GitUp']

###############################################################################
# IMPORTS and LIBRARIES SETUP
###############################################################################

# Python libs
import sys
import os
from contextlib import contextmanager
import subprocess

# 3rd party libs
import colorama
from termcolor import colored

from git import Repo, GitCmdObjectDB

# PyGitUp libs
from PyGitUp.utils import execute, uniq
from PyGitUp.git_wrapper import GitWrapper, GitError

###############################################################################
# Setup of 3rd party libs
###############################################################################

colorama.init(autoreset=True)

###############################################################################
# Setup global vars
###############################################################################

# Initialize frequently used globals
try:
    path = execute('git rev-parse --show-toplevel')
except IndexError:
    sys.exit(1)

repo = Repo(path, odbt=GitCmdObjectDB)
git = GitWrapper(repo)


###############################################################################
# GitUp
###############################################################################

class GitUp(object):
    """ Conainter class for GitUp methods """

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
            if branch.name in list(self.remote_map.keys())
        ]
        self.branches.sort(key=lambda b: b.name)

        # remotes: all remotes that are associated with local branches
        self.remotes = uniq(
            [r.name.split('/', 2)[0] for r in list(self.remote_map.values())]
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

            if self.with_bundler():
                self.check_bundler()

        except GitError as error:
            print(colored(error.message, 'red'))

            # Print more information about the error
            if error.stdout or error.stderr:
                print()
                print("Here's what git said:")
                print()

                if error.stdout:
                    print(error.stdout)
                if error.stderr:
                    print(error.stderr)

            if error.details:
                print()
                print("Here's what we know:")
                print(str(error.details))
                print()


    def rebase_all_branches(self):
        """ Rebase all branches, if possible. """
        col_width = max([len(b.name) for b in self.branches]) + 1

        for branch in self.branches:
            remote = self.remote_map[branch.name]
            print(colored(branch.name.ljust(col_width), attrs=['bold']),
                  end=' ')

            if remote.commit.hexsha == branch.commit.hexsha:
                print(colored('up to date', 'green'))
                continue

            base = git.merge_base(branch.name, remote.name)

            if base == remote.commit.hexsha:
                print(colored('ahead of upstream', 'green'))
                continue

            if base == branch.commit.hexsha:
                print(colored('fast-forwarding...', 'yellow'))
            elif self.config('rebase.auto') == 'false':
                print(colored('diverged', 'red'))
                continue
            else:
                print(colored('rebasing', 'yellow'))

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

        try:
            git.fetch(tostdout=True, *fetch_args, **fetch_kwargs)
        except GitError as error:
            error.message = "`git fetch` failed"
            raise error

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
            print(colored("You're not currently on a branch. I'm exiting in"
                          "case you're in the middle of something.", 'red'))
            sys.exit(1)

        branch_name = repo.active_branch.name

        yield

        print(colored('returning to {0}'.format(branch_name), 'magenta'))

    def config(self, key):
        """ Get a git-up-specific config value. """
        return git.config('git-up.{0}'.format(key))

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
                print(colored(
                    "Warning: fetch.prune is set to 'true' but your git "
                    "version doesn't seem to support it ({0} < {1}). Defaulting"
                    " to 'false'.".format(git.version(), required_version),
                    'yellow'
                ))

    ###########################################################################
    # Gemfile Checking
    ###########################################################################

    def with_bundler(self):
        """
        Check, if bundler check is requested.

        Check, if the user wants us to check for new gems and return True in
        this case.
        :rtype : bool
        """
        def gemfile_exists():
            """
            Check, if a Gemfile exists in the current repo.
            """
            return os.path.exists('Gemfile')

        if 'GIT_UP_BUNDLER_CHECK' in os.environ:
            print(colored(
                '''The GIT_UP_BUNDLER_CHECK environment variable is deprecated.
You can now tell git-up to check (or not check) for missing
gems on a per-project basis using git's config system. To
set it globally, run this command anywhere:

git config --global git-up.bundler.check true

To set it within a project, run this command inside that
project's directory:

git config git-up.bundler.check true

Replace 'true' with 'false' to disable checking.''', 'yellow'))

        if self.config('bundler.check') == 'true':
            return gemfile_exists()

        if ('GIT_UP_BUNDLER_CHECK' in os.environ
                and os.environ['GIT_UP_BUNDLER_CHECK'] == 'true'):
            return gemfile_exists()

        return False

    def check_bundler(self):
        """
        Run the bundler check.
        """
        def get_config(name):
            return name if self.config('bundler.' + name) else ''

        from pkg_resources import Requirement, resource_filename
        bundler_script = resource_filename(Requirement.parse('git-up'),
                                           'check-bundler.rb')
        subprocess.call(['ruby', bundler_script, get_config('autoinstall'),
                         get_config('local'), get_config('rbenv')])

###############################################################################


def run():
    GitUp().run()

if __name__ == '__main__':
    run()
