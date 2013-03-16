# coding=utf-8
"""
Some simple, generic usefull methods.
"""

import os


def find(seq, test):
    """ Return first item in sequence where test(item) == True """
    for item in seq:
        if test(item):
            return item


def uniq(seq):
    """ Return a copy of seq without duplicates. """
    seen = set()
    return [x for x in seq if str(x) not in seen and not seen.add(str(x))]


def execute(cmd):
    """ Execute a command and return it's output. """
    return os.popen(cmd).readlines()[0].strip()
