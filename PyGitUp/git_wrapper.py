# coding=utf-8
"""
A wrapper extending GitPython's repo.git.

This wrapper class provides support for stdout messages in Git Exceptions
and (nearly) realtime stdout output. In addition, some methods of the
original repo.git are shadowed by custom methods providing functionality
needed for `git up`.
"""

from __future__ import print_function

__all__ = ['GitWrapper', 'GitError']

###############################################################################
# IMPORTS
###############################################################################

# Python libs
import sys
import re
import subprocess
import platform
from contextlib import contextmanager

import six

# 3rd party libs
from termcolor import colored  # Assume, colorama is already initialized
from git import GitCommandError, CheckoutError as OrigCheckoutError, Git

# PyGitUp libs
from PyGitUp.utils import find


###############################################################################
# GitWrapper
###############################################################################

class GitWrapper(object):
    """
    A wrapper for repo.git providing better stdout handling + better exeptions.

    It is preferred to repo.git because it doesn't print to stdout
    in real time. In addition, this wrapper provides better error
    handling (it provides stdout messages inside the exception, too).
    """

    def __init__(self, repo):
        if repo:
            #: :type: git.Repo
            self.repo = repo
            #: :type: git.Git
            self.git = self.repo.git
        else:
            #: :type: git.Git
            self.git = Git()

    def __del__(self):
        # Is the following true?

        # GitPython runs persistent git processes in  the working directory.
        # Therefore, when we use 'git up' in something like a test environment,
        # this might cause troubles because of the open file handlers (like
        # trying to remove the directory right after the test has finished).
        # 'clear_cache' kills the processes...

        if platform.system() == 'Windows':  # pragma: no cover
            pass
            # ... or rather "should kill", because but somehow it recently
            # started to not kill cat_file_header out of the blue (I even
            # tried running old code, but the once working code failed).
            # Thus, we kill it  manually here.
            if self.git.cat_file_header is not None:
                subprocess.call(("TASKKILL /F /T /PID {0} 2>nul 1>nul".format(
                    str(self.git.cat_file_header.proc.pid)
                )), shell=True)
            if self.git.cat_file_all is not None:
                subprocess.call(("TASKKILL /F /T /PID {0} 2>nul 1>nul".format(
                    str(self.git.cat_file_all.proc.pid)
                )), shell=True)

        self.git.clear_cache()

    def run(self, name, *args, **kwargs):
        """ Run a git command specified by name and args/kwargs. """

        tostdout = kwargs.pop('tostdout', False)
        stdout = six.b('')

        # Execute command
        cmd = getattr(self.git, name)(as_process=True, *args, **kwargs)

        # Capture output
        while True:
            output = cmd.stdout.read(1)

            # Print to stdout
            if tostdout:
                sys.stdout.write(output.decode('utf-8'))
                sys.stdout.flush()

            stdout += output

            if output == six.b(""):
                break

        # Wait for the process to quit
        try:
            cmd.wait()
        except GitCommandError as error:
            # Add more meta-information to errors
            message = "'{0}' returned exit status {1}".format(
                ' '.join(str(c) for c in error.command),
                error.status
            )

            raise GitError(message, stderr=error.stderr, stdout=stdout)

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
        stashed = False

        if self.repo.is_dirty(submodules=False):
            if self.change_count > 1:
                message = 'stashing {0} changes'
            else:
                message = 'stashing {0} change'
            print(colored(
                message.format(self.change_count),
                'magenta'
            ))
            try:
                self.run('stash')
            except GitError as e:
                raise StashError(stderr=e.stderr, stdout=e.stdout)

            stashed = True

        yield

        if stashed:
            print(colored('unstashing', 'magenta'))
            try:
                self.run('stash', 'pop')
            except GitError as e:
                raise UnstashError(stderr=e.stderr, stdout=e.stdout)

    def checkout(self, branch_name):
        """ Checkout a branch by name. """
        try:
            find(
                self.repo.branches, lambda b: b.name == branch_name
            ).checkout()
        except OrigCheckoutError as e:
            raise CheckoutError(branch_name, details=e)

    def rebase(self, target_branch):
        """ Rebase to target branch. """
        current_branch = self.repo.active_branch

        arguments = (
            ([self.config('git-up.rebase.arguments')] or []) +
            [target_branch.name]
        )
        try:
            self.run('rebase', *arguments)
        except GitError as e:
            raise RebaseError(current_branch.name, target_branch.name,
                              **e.__dict__)

    def config(self, key):
        """ Return `git config key` output or None. """
        try:
            return self.git.config(key)
        except GitCommandError:
            return None

    @property
    def change_count(self):
        """ The number of changes in the working directory. """
        status = self.git.status(porcelain=True, untracked_files='no').strip()
        if not status:
            return 0
        else:
            return len(status.split('\n'))

    @property
    def version(self):
        """
        Return git's version as a list of numbers.

        The original repo.git.version_info has problems with tome types of
        git version strings.
        """
        return re.search(r'\d+(\.\d+)+', self.git.version()).group(0)

    def is_version_min(self, required_version):
        """ Does git's version match the requirements? """
        return self.version.split('.') >= required_version.split('.')


###############################################################################
# GitError + subclasses
###############################################################################

class GitError(Exception):
    """
    Extension of the GitCommandError class.

    New:
    - stdout
    - details: a 'nested' exception with more details
    """

    def __init__(self, message=None, stderr=None, stdout=None, details=None):
        # super(GitError, self).__init__((), None, stderr)
        self.details = details
        self.message = message

        self.stderr = stderr
        self.stdout = stdout

    def __str__(self):  # pragma: no cover
        return self.message


class StashError(GitError):
    """
    Error while stashing
    """
    def __init__(self, **kwargs):
        kwargs.pop('message', None)
        GitError.__init__(self, 'Stashing failed!', **kwargs)


class UnstashError(GitError):
    """
    Error while unstashing
    """
    def __init__(self, **kwargs):
        kwargs.pop('message', None)
        GitError.__init__(self, 'Unstashing failed!', **kwargs)


class CheckoutError(GitError):
    """
    Error during checkout
    """
    def __init__(self, branch_name, **kwargs):
        kwargs.pop('message', None)
        GitError.__init__(self, 'Failed to checkout ' + branch_name,
                          **kwargs)


class RebaseError(GitError):
    """
    Error during rebase command
    """
    def __init__(self, current_branch, target_branch, **kwargs):
        # Remove kwargs we won't pass to GitError
        kwargs.pop('message', None)
        kwargs.pop('command', None)
        kwargs.pop('status', None)

        message = "Failed to rebase {1} onto {0}".format(
            current_branch, target_branch
        )
        GitError.__init__(self, message, **kwargs)
