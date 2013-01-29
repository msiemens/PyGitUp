#!/usr/bin/env python

################################################################################
# GIT-UP.py
#
# TODOS:
# - Error handling
# - Run from subdirectory
################################################################################

################################################################################
# IMPORTS and LIBRARIES SETUP
################################################################################


import sys
import os
import re

import subprocess
from contextlib import contextmanager

import colorama
from termcolor import colored

from git import *

colorama.init(autoreset=True)

try:
    path = os.popen('git rev-parse --show-toplevel').readlines()[0].strip()
except Exception, e:
    # TODO: Better handling
    print colored("We don't seem to be in a git repository.", 'red')
    sys.exit(1)


repo = Repo(path, odbt=GitCmdObjectDB)


################################################################################
# GENERAL METHODS
################################################################################

def find(seq, f):
    """ Return first item in sequence where f(item) == True """
    for item in seq:
        if f(item):
            return item


def uniq(seq):
    """ Return a copy of seq without duplicates"""
    seen = set()
    return [x for x in seq if str(x) not in seen and not seen.add(str(x))]


################################################################################
# HELPER CLASSES
################################################################################

class git_wrapper():
    """
    A wrapper for repo.git, providing better stdout handling.

    It is preferred to repo.git because it doesn't print to stdout
    in real time. In addition, this wrapper provides better error
    handling (it provides stdout messages inside the exception, too).
    """

    def run(self, name, *args, **kwargs):
        tostdout = kwargs.pop('tostdout', False)
        stdout = ''

        # Execute command
        cmd = getattr(repo.git, name)(as_process=True, *args, **kwargs)

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

git = git_wrapper()

################################################################################
# HELPER METHODS
################################################################################


@contextmanager
def stash():
    """
    A stashing contextmanager.
    It  stashes all changes inside and unstashed when done.
    """
    stashed = False

    if repo.is_dirty():
        print colored('stashing {} changes'.format(change_count), 'magenta')
        git.stash()
        stashed = True

    yield

    if stashed:
        print colored('unstashing', 'magenta')
        git.stash('pop')


@contextmanager
def returning_to_current_branch():
    """ A contextmanager returning to the current branch. """
    if repo.head.is_detached:
        print colored("ou're not currently on a branch. "
        "I'm exiting in case you're in the middle of something.", 'red')
        sys.exit(1)

    branch_name = repo.active_branch.name

    yield

    print colored('returning to {}'.format(branch_name), 'magenta')


def remote_ref_for_branch(branch):
    """ Get the remote reference for a local branch. """

    # Get name of the remote containing the branch
    try:
        remote_name = git.config('branch.{}.remote'.format(branch.name))
    except:
        # TODO: Will it ever throw?
        remote_name = 'origin'

    # Get name of the remote branch
    try:
        remote_branch = git.config('branch.{}.merge'.format(branch.name))
    except:
        remote_branch = branch.name

    remote_branch = remote_branch.split('refs/heads/').pop()

    # Search the remote reference
    remote = find(repo.remotes, lambda remote: remote.name == remote_name)
    return find(
        remote.refs,
        lambda ref: ref.name == "{}/{}".format(remote_name, remote_branch)
    )

################################################################################
# SETUP VARIABLES
################################################################################

# remote_map: map local branch names to remote branches
remote_map = dict()

for branch in repo.branches:
    remote = remote_ref_for_branch(branch)
    if remote:
        remote_map[branch.name] = remote

# branches: list all local branches that has a corresponding remote branch
branches = [
    branch for branch in repo.branches
        if branch.name in remote_map.keys()
]
branches.sort(key=lambda b: b.name)

# remotes: list all remotes that are associated with local branches
remotes = uniq([r.name.split('/', 2)[0] for r in remote_map.values()])

# change_count
change_count = len(git.status(porcelain=True, untracked_files='no').split('\n'))

################################################################################
# THE MAIN CODE
################################################################################


def run():
    try:
        fetch()

        with stash():
            with returning_to_current_branch():
                rebase_all_branches()

    except GitCommandError as error:
        raise error  # TODO: error handling


def rebase_all_branches():
    col_width = max([len(b.name) for b in branches]) + 1

    for branch in branches:
        remote = remote_map[branch.name]
        print colored(branch.name.ljust(col_width), attrs=['bold']),

        if remote.commit.hexsha == branch.commit.hexsha:
            print colored('up to date', 'green')
            continue

        base = merge_base(branch.name, remote.name)

        if base == remote.commit.hexsha:
            print colored('ahead of upstream', 'green')
            continue

        if base == branch.commit.hexsha:
            print colored('fast-forwarding...', 'yellow')
        elif config('rebase.auto') == 'false':
            print colored('diverged', 'red')
            continue
        else:
            print colored('rebasing', 'yellow')

        log(branch, remote)
        checkout(branch.name)
        rebase(remote)

################################################################################
# GIT COMMANDS
################################################################################


def fetch():
    fetch_kwargs = {'multiple': True}
    fetch_args = []

    if prune():
        fetch_kwargs['prune'] = True

    if config('fetch.all'):
        fetch_kwargs['all'] = True
    else:
        fetch_args.append(remotes)

    git.fetch(tostdout=True, *fetch_args, **fetch_kwargs)


def checkout(branch_name):
    find(repo.branches, lambda b: b.name == branch_name).checkout()


def rebase(target_branch):
    # current_branch = repo.active_branch
    arguments = config('rebase.arguments')
    if arguments:
        git.execute(['git', 'rebase', arguments, target_branch.name])
    else:
        git.execute(['git', 'rebase', target_branch.name])


def prune():
    required_version = "1.6.6"
    config_value = config("fetch.prune")

    if git_version_min(required_version):
        return config_value != 'false'
    else:
        if config_value == 'true':
            print colored("Warning: fetch.prune is set to 'true' but your git "
                "version doesn't seem to support it ({} < {}). Defaulting to"
                "'false'.".format(git_version(), required_version), 'yellow')


def merge_base(a, b):
    return git.merge_base(a, b).strip()


def on_branch(branch_name):
    return not repo.head.is_detached and repo.active_branch.name == branch_name

################################################################################
# MISC
################################################################################


def log(branch, remote):
    log_hook = config('rebase.log-hook')
    if log_hook:
        subprocess.call(
            [log_hook, 'git-up', branch.name, remote.name],
            shell=True
        )


def config(key):
    try:
        return git.config('git-up.{}'.format(key))
    except GitCommandError:
        return None


def git_version_min(required_version):
    return git_version().split('.') >= required_version.split('.')


def git_version():
    return re.search(r'\d+(\.\d+)+', repo.git.version()).group(0)


if __name__ == '__main__':
    run()
