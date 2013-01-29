################################################################################
# PyGitUp
# ------------------------------------------------------------------------------
# FILE: utils.py
# DESCRIPTION: Some methods not associated with git
# AUTHOR: Markus Siemens <markus@m-siemens.de>
# URL: https://github.com/msiemens/PyGitUp
################################################################################

import os


def find(seq, f):
    """ Return first item in sequence where f(item) == True """
    for item in seq:
        if f(item):
            return item


def uniq(seq):
    """ Return a copy of seq without duplicates. """
    seen = set()
    return [x for x in seq if str(x) not in seen and not seen.add(str(x))]


def execute(cmd):
    """ Execute a command and return it's output. """
    return os.popen(cmd).readlines()[0].strip()
