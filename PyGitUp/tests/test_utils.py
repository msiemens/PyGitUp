from nose.tools import *

from PyGitUp import utils


def test_find():
    assert_equal(utils.find([1, 2, 3], lambda i: i == 3), 3)
    assert_equal(utils.find([1, 2, 3], lambda i: i == 4), None)


def test_uniq():
    assert_equal(utils.uniq([1, 1, 1, 2, 3]), [1, 2, 3])
    assert_equal(utils.uniq([1]), [1])
    assert_equal(utils.uniq([]), [])
