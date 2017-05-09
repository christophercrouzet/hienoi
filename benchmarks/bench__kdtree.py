#!/usr/bin/env python

import os
import sys
import timeit
import unittest

import numpy

_HERE = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(_HERE, os.pardir)))

from hienoi._kdtree import KDTree


_clock = timeit.default_timer


def _generate_uniform_2D_data(count, seed):
    numpy.random.seed(seed=seed)
    data = numpy.empty(count, dtype=(numpy.float32, 2))
    data[:, 0] = numpy.random.uniform(-1.0, 1.0, count)
    data[:, 1] = numpy.random.uniform(-1.0, 1.0, count)
    return data


def _generate_2D_point(seed):
    numpy.random.seed(seed=seed)
    return (numpy.float32(numpy.random.random() * 2.0 - 1.0),
            numpy.float32(numpy.random.random() * 2.0 - 1.0))


class KDTreeBench(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._trees = {
            1: KDTree(_generate_uniform_2D_data(1, 391)),
            10: KDTree(_generate_uniform_2D_data(10, 813)),
            100: KDTree(_generate_uniform_2D_data(100, 571)),
            1000: KDTree(_generate_uniform_2D_data(1000, 600)),
            10000: KDTree(_generate_uniform_2D_data(10000, 427)),
            100000: KDTree(_generate_uniform_2D_data(100000, 180)),
            1000000: KDTree(_generate_uniform_2D_data(1000000, 425)),
        }

    def bench_build_uniform_100(self):
        data = _generate_uniform_2D_data(100, 968)
        start = _clock()
        tree = KDTree(data)
        return _clock() - start

    def bench_build_uniform_10000(self):
        data = _generate_uniform_2D_data(10000, 441)
        start = _clock()
        tree = KDTree(data)
        return _clock() - start

    def bench_build_uniform_1000000(self):
        data = _generate_uniform_2D_data(1000000, 96)
        start = _clock()
        tree = KDTree(data)
        return _clock() - start

    def bench_search_uniform_1_nearests_in_100_points_tree_100_times(self):
        numpy.random.seed(seed=192)
        k = 1
        r = None
        n = 100
        count = 100
        tree = self._trees[n]
        points = [_generate_2D_point(seed) for seed in numpy.random.randint(999, size=count)]
        start = _clock()
        for point in points:
            tree.search(point, count=k, radius=r, sort=True)

        return _clock() - start

    def bench_search_uniform_100_nearests_in_100_points_tree_100_times(self):
        numpy.random.seed(seed=501)
        k = 100
        r = None
        n = 100
        count = 100
        tree = self._trees[n]
        points = [_generate_2D_point(seed) for seed in numpy.random.randint(999, size=count)]
        start = _clock()
        for point in points:
            tree.search(point, count=k, radius=r, sort=True)

        return _clock() - start

    def bench_search_uniform_1_nearests_in_10000_points_tree_100_times(self):
        numpy.random.seed(seed=495)
        k = 1
        r = None
        n = 10000
        count = 100
        tree = self._trees[n]
        points = [_generate_2D_point(seed) for seed in numpy.random.randint(999, size=count)]
        start = _clock()
        for point in points:
            tree.search(point, count=k, radius=r, sort=True)

        return _clock() - start

    def bench_search_uniform_100_nearests_in_10000_points_tree_100_times(self):
        numpy.random.seed(seed=201)
        k = 100
        r = None
        n = 10000
        count = 100
        tree = self._trees[n]
        points = [_generate_2D_point(seed) for seed in numpy.random.randint(999, size=count)]
        start = _clock()
        for point in points:
            tree.search(point, count=k, radius=r, sort=True)

        return _clock() - start

    def bench_search_uniform_1_nearests_in_1000000_points_tree_100_times(self):
        numpy.random.seed(seed=597)
        k = 1
        r = None
        n = 1000000
        count = 100
        tree = self._trees[n]
        points = [_generate_2D_point(seed) for seed in numpy.random.randint(999, size=count)]
        start = _clock()
        for point in points:
            tree.search(point, count=k, radius=r, sort=True)

        return _clock() - start

    def bench_search_uniform_100_nearests_in_1000000_points_tree_100_times(self):
        numpy.random.seed(seed=109)
        k = 100
        r = None
        n = 1000000
        count = 100
        tree = self._trees[n]
        points = [_generate_2D_point(seed) for seed in numpy.random.randint(999, size=count)]
        start = _clock()
        for point in points:
            tree.search(point, count=k, radius=r, sort=True)

        return _clock() - start

    def bench_search_uniform_all_within_0_25_radius_in_100_points_tree_100_times(self):
        numpy.random.seed(seed=220)
        k = None
        r = 0.25
        n = 100
        count = 100
        tree = self._trees[n]
        points = [_generate_2D_point(seed) for seed in numpy.random.randint(999, size=count)]
        start = _clock()
        for point in points:
            tree.search(point, count=k, radius=r, sort=True)

        return _clock() - start

    def bench_search_uniform_all_within_0_75_radius_in_100_points_tree_100_times(self):
        numpy.random.seed(seed=384)
        k = None
        r = 0.75
        n = 100
        count = 100
        tree = self._trees[n]
        points = [_generate_2D_point(seed) for seed in numpy.random.randint(999, size=count)]
        start = _clock()
        for point in points:
            tree.search(point, count=k, radius=r, sort=True)

        return _clock() - start

    def bench_search_uniform_all_within_0_25_radius_in_10000_points_tree_100_times(self):
        numpy.random.seed(seed=471)
        k = None
        r = 0.25
        n = 10000
        count = 100
        tree = self._trees[n]
        points = [_generate_2D_point(seed) for seed in numpy.random.randint(999, size=count)]
        start = _clock()
        for point in points:
            tree.search(point, count=k, radius=r, sort=True)

        return _clock() - start

    def bench_search_uniform_all_within_0_75_radius_in_10000_points_tree_100_times(self):
        numpy.random.seed(seed=173)
        k = None
        r = 0.75
        n = 10000
        count = 100
        tree = self._trees[n]
        points = [_generate_2D_point(seed) for seed in numpy.random.randint(999, size=count)]
        start = _clock()
        for point in points:
            tree.search(point, count=k, radius=r, sort=True)

        return _clock() - start

    def bench_search_uniform_all_within_0_25_radius_in_1000000_points_tree_100_times(self):
        numpy.random.seed(seed=28)
        k = None
        r = 0.25
        n = 1000000
        count = 100
        tree = self._trees[n]
        points = [_generate_2D_point(seed) for seed in numpy.random.randint(999, size=count)]
        start = _clock()
        for point in points:
            tree.search(point, count=k, radius=r, sort=True)

        return _clock() - start

    def bench_search_uniform_all_within_0_75_radius_in_1000000_points_tree_100_times(self):
        numpy.random.seed(seed=850)
        k = None
        r = 0.75
        n = 1000000
        count = 100
        tree = self._trees[n]
        points = [_generate_2D_point(seed) for seed in numpy.random.randint(999, size=count)]
        start = _clock()
        for point in points:
            tree.search(point, count=k, radius=r, sort=True)

        return _clock() - start


if __name__ == '__main__':
    from benchmarks.run import run
    run('__main__')
