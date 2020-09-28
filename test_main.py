import numpy as np
from dodo import (
    has_en,
    free,
    fit,
    empty as eee, blocked as bbb,
)


def test_has_en():
    assert has_en('lala')
    assert has_en('LALA')
    assert not has_en('עברית')
    assert has_en('עברית English')


def test_grid():
    grid = np.asarray([
        ['a', 'b', 'c'],
        ['a', 'b', 'c'],
        [eee, eee, bbb]
    ])

    assert not free(grid, (0, 0))
    assert not free(grid, (0, 1))
    assert not free(grid, (0, 2))
    assert not free(grid, (1, 2))
    assert free(grid, (-1, 2))
    assert free(grid, (1, -2))
    assert free(grid, (1, 6))
    assert free(grid, (6, 6))
    assert free(grid, (2, 0))
    assert free(grid, (2, 1))

    di = np.array([1, 0])
    dj = np.array([0, 1])
    assert fit(grid, np.array([0, 0]), di, 'aa')
    assert not fit(grid, np.array([0, 0]), dj, 'aa')

    assert fit(grid, np.array([0, 1]), di, 'bb')
    assert fit(grid, np.array([0, 1]), di, 'bbc')
    assert not fit(grid, np.array([0, 1]), di, 'ab')

    assert fit(grid, np.array([0, 2]), di, 'cc')
    assert not fit(grid, np.array([0, 2]), di, 'ccc')
