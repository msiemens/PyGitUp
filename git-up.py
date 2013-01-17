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

import atexit
import subprocess

import colorama
from termcolor import colored

from git import *


colorama.init(autoreset=True)

def exit_handler():
    colorama.deinit()

atexit.register(exit_handler)


path = os.getcwd()
repo = Repo(path)
git = repo.git


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


class memorize:
    """ Memorize a function call return value """

    def __init__(self, f):
        self.f = f
        self.mem = {}

    def __call__(self, *args, **kwargs):
        if (args, str(kwargs)) in self.mem:
            return self.mem[args, str(kwargs)]
        else:
            tmp = self.f(*args, **kwargs)
            self.mem[args, str(kwargs)] = tmp
            return tmp


################################################################################


def run():
    # Fetch remote information
    fetch_args = {'multiple': True, 'all': True, 'output_stream': sys.stdout}

    if prune():
        fetch_args['prune'] = True

    git.fetch(**fetch_args)

    with stash():
        with returning_to_current_branch():
            rebase_all_branches()


class stash(object):
    stashed = False

    def __enter__(self):
        if repo.is_dirty():
            print colored('stashing {} changes'.format(change_count()), 'magenta')
            git.stash()
            self.stashed = True

    def __exit__(self, *ignored):
        if self.stashed:
            print colored('unstashing', 'magenta')
            git.stash('pop')


class returning_to_current_branch(object):
    def __enter__(self):
        if repo.head.is_detached:
            print colored("ou're not currently on a branch. "
            "I'm exiting in case you're in the middle of something.", 'red')
            sys.exit(1)

        self.branch_name = repo.active_branch.name

    def __exit__(self, *ignored):
        print colored('returning to {}'.format(self.branch_name), 'magenta')


def rebase_all_branches():
    repo.config_reader('repository').get('branch "master"', 'remote')
    col_width = max([len(b.name) for b in branches()]) + 1

    for branch in branches():
        remote = remote_map()[branch.name]
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


@memorize
def branches():
    branches = [
        branch for branch in repo.branches
            if branch.name in remote_map().keys()
    ]
    branches.sort(key=lambda b: b.name)
    return branches


@memorize
def remotes():
    return uniq([r.name.split('/', 2) for r in remote_map().values()])


@memorize
def remote_map():
    remote_map = dict()

    for branch in repo.branches:
        remote = remote_ref_for_branch(branch)
        if remote:
            remote_map[branch.name] = remote

    return remote_map


def remote_ref_for_branch(branch):
    try:
        remote_name = git.config('branch.{}.remote'.format(branch.name))
    except:
        remote_name = 'origin'

    try:
        remote_branch = git.config('branch.{}.merge'.format(branch.name))
    except:
        remote_branch = branch.name

    remote_branch = remote_branch.split('refs/heads/').pop()

    remote = find(repo.remotes, lambda remote: remote.name == remote_name)
    return find(
        remote.refs,
        lambda ref: ref.name == "{}/{}".format(remote_name, remote_branch)
    )


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


def change_count():
    return len(git.status(porcelain=True, untracked_files='no').split('\n'))


def merge_base(a, b):
    return git.merge_base(a, b).strip()


def checkout(branch_name):
    find(repo.branches, lambda b: b.name == branch_name).checkout()


def log(branch, remote):
    log_hook = config('rebase.log-hook')
    if log_hook:
        subprocess.call(
            [log_hook, 'git-up', branch.name, remote.name],
            shell=True
        )


def rebase(target_branch):
    # current_branch = repo.active_branch
    arguments = config('rebase.arguments')
    if arguments:
        git.execute(['git', 'rebase', arguments, target_branch.name])
    else:
        git.execute(['git', 'rebase', target_branch.name])


def on_branch(branch_name):
    return not repo.head.is_detached and repo.active_branch.name == branch_name


def config(key):
    try:
        return git.config('git-up.{}'.format(key))
    except GitCommandError:
        return None


def git_version_min(required_version):
    return git_version().split('.') >= required_version.split('.')


def git_version():
    return re.search(r'\d+(\.\d+)+', repo.git.version()).group(0)

run()
