from PyGitUp import utils


def test_find():
    assert utils.find([1, 2, 3], lambda i: i == 3) == 3
    assert utils.find([1, 2, 3], lambda i: i == 4) is None


def test_uniq():
    assert utils.uniq([1, 1, 1, 2, 3]) == [1, 2, 3]
    assert utils.uniq([1]) == [1]
    assert utils.uniq([]) == []
