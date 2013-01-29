###############################################################################
# PyGitUp
# -----------------------------------------------------------------------------
# FILE: git_wrapper.py
# DESCRIPTION: TODO
# AUTHOR: Markus Siemens <markus@m-siemens.de>
# URL: https://github.com/msiemens/PyGitUp
###############################################################################

__all__ = ['git_wrapper']

###############################################################################
# IMPORTS and LIBRARIES SETUP
###############################################################################

# Python libs
import sys
import re
from contextlib import contextmanager

# 3rd party libs
from termcolor import colored  # Assume, colorama is already initialized
from git import GitCommandError

# PyGitUp libs
from PyGitUp.utils import find


###############################################################################
# git_wrapper
###############################################################################

class git_wrapper():
    """
    A wrapper for repo.git, providing better stdout handling.

    It is preferred to repo.git because it doesn't print to stdout
    in real time. In addition, this wrapper provides better error
    handling (it provides stdout messages inside the exception, too).

    TODO: Add stdout to exceptions
    """

    def __init__(self, repo):
        self.repo = repo
        self.git = self.repo.git

    def run(self, name, *args, **kwargs):
        global repo

        tostdout = kwargs.pop('tostdout', False)
        stdout = ''

        # Execute command
        cmd = getattr(self.git, name)(as_process=True, *args, **kwargs)

        # Capture output
        while True:
            output = cmd.stdout.read(4)

            # Print to stdout
            if tostdout:
                sys.stdout.write(output)
                sys.stdout.flush()

            stdout += output

            if output == "":
                break

        # Wait for the process to quit
        cmd.wait()

        return stdout.strip()

    def __getattr__(self, name):
        return lambda *args, **kwargs: self.run(name, *args, **kwargs)

    ###########################################################################
    # Overwrite some methods and add new ones
    ###########################################################################

    @contextmanager
    def stash(self):
        """
        A stashing contextmanager.
        It  stashes all changes inside and unstashed when done.
        """
        global repo
        stashed = False

        if self.repo.is_dirty():
            print colored(
                'stashing {} changes'.format(self.change_count),
                'magenta'
            )
            self.git.stash()
            stashed = True

        yield

        if stashed:
            print colored('unstashing', 'magenta')
            self.git.stash('pop')

    def remote_ref_for_branch(self, branch):
        """ Get the remote reference for a local branch. """

        # Get name of the remote containing the branch
        remote_name = (self.config('branch.{}.remote'.format(branch.name)) or
            'origin')

        # Get name of the remote branch
        remote_branch = (self.config('branch.{}.merge'.format(branch.name)) or
            branch.name)
        remote_branch = remote_branch.split('refs/heads/').pop()

        # Search the remote reference
        remote = find(
            self.repo.remotes,
            lambda remote: remote.name == remote_name
        )
        return find(
            remote.refs,
            lambda ref: ref.name == "{}/{}".format(remote_name, remote_branch)
        )

    @property
    def change_count(self):
        """ The number of changes in the working directory. """
        return len(
            self.git.status(porcelain=True, untracked_files='no').split('\n')
        )

    def checkout(self, branch_name):
        """ Checkout a branch by name. """
        find(self.repo.branches, lambda b: b.name == branch_name).checkout()

    def rebase(self, target_branch):
        """ Rebase to target branch. """
        # current_branch = repo.active_branch
        arguments = (
            (self.config('rebase.arguments') or []) + [target_branch.name]
        )
        self.git.rebase(*arguments)

    def merge_base(self, a, b):
        """ Return the merge_base between commit a and b. """
        return self.git.merge_base(a, b).strip()

    def config(self, key):
        """ Return `git config key` output or None. """
        try:
            return self.git.config(key)
        except GitCommandError:
            return None

    def version(self):
        """
        Return git's version as a list of numbers.

        Example:
        >>> git.version()
            [1, 7, 2]
        """
        return re.search(r'\d+(\.\d+)+', self.git.version()).group(0)

    def is_version_min(self, required_version):
        """ Does git's version match the requirements? """
        return self.version().split('.') >= required_version.split('.')
