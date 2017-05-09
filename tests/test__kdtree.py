#!/usr/bin/env python

import os
import sys
import unittest

import numpy

_HERE = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(_HERE, os.pardir)))

from hienoi._kdtree import KDTree


class KDTreeTest(unittest.TestCase):

    def test_search_1(self):
        dtype = numpy.dtype((numpy.float32, 2))
        a = numpy.array([
            ( 1.1,  1.5),
            ( 1.2, -1.6),
            (-1.3, -1.7),
            (-1.4,  1.8),
            ( 0.5,  0.5),
        ], dtype=dtype)

        suite = [
            {
                'searches': [(((2.0, 4.0),), {'count': n, 'radius': None, 'sort': True}) for n in range(len(a) + 1)],
                'expected_indices': [0, 4, 3, 1, 2],
                'expected_squared_distances': [7.06, 14.5, 16.4, 32.0, 43.38],
            },
            {
                'searches': [(((0.6, -0.7),), {'count': n, 'radius': None, 'sort': True}) for n in range(len(a) + 1)],
                'expected_indices': [1, 4, 2, 0, 3],
                'expected_squared_distances': [1.17, 1.45, 4.61, 5.09, 10.25],
            },
            {
                'searches': [(((-0.2, 0.4),), {'count': len(a), 'radius': 1.0, 'sort': True})],
                'expected_indices': [4],
                'expected_squared_distances': [0.5],
            },
            {
                'searches': [(((-0.2, 0.4),), {'count': len(a), 'radius': 2.0, 'sort': True})],
                'expected_indices': [4, 0, 3],
                'expected_squared_distances': [0.5, 2.9, 3.4],
            },
            {
                'searches': [(((-0.2, 0.4),), {'count': len(a), 'radius': 3.0, 'sort': True})],
                'expected_indices': [4, 0, 3, 2, 1],
                'expected_squared_distances': [0.5, 2.9, 3.4, 5.62, 5.96],
            },
        ]

        trees = [KDTree(a, bucket_size=size) for size in range(1, len(a) + 1)]
        for tree in trees:
            self._test_search_suite(tree, suite)

    def test_search_2(self):
        dtype = numpy.dtype((numpy.float32, 2))
        a = numpy.array([
            ( 1.1,  1.5),
            ( 1.2,  0.5),
            (-1.3,  0.5),
            (-1.4,  1.8),
            ( 0.5,  0.5),
        ], dtype=dtype)

        suite = [
            {
                'searches': [(((-0.2, -1.5),), {'count': n, 'radius': None, 'sort': True}) for n in range(len(a) + 1)],
                'expected_indices': [4, 2, 1, 0, 3],
                'expected_squared_distances': [4.49, 5.21, 5.96, 10.69, 12.33],
            },
            {
                'searches': [(((1.3, -0.1),), {'count': n, 'radius': None, 'sort': True}) for n in range(len(a) + 1)],
                'expected_indices': [1, 4, 0, 2, 3],
                'expected_squared_distances': [0.37, 1.0, 2.6, 7.12, 10.9],
            },
            {
                'searches': [(((2.1, 0.7),), {'count': len(a), 'radius': 1.0, 'sort': True})],
                'expected_indices': [1],
                'expected_squared_distances': [0.85],
            },
            {
                'searches': [(((2.1, 0.7),), {'count': len(a), 'radius': 2.0, 'sort': True})],
                'expected_indices': [1, 0, 4],
                'expected_squared_distances': [0.85, 1.64, 2.6],
            },
            {
                'searches': [(((2.1, 0.7),), {'count': len(a), 'radius': 3.0, 'sort': True})],
                'expected_indices': [1, 0, 4],
                'expected_squared_distances': [0.85, 1.64, 2.6],
            },
            {
                'searches': [(((2.1, 0.7),), {'count': len(a), 'radius': 4.0, 'sort': True})],
                'expected_indices': [1, 0, 4, 2, 3],
                'expected_squared_distances': [0.85, 1.64, 2.6, 11.6, 13.46],
            },
        ]

        trees = [KDTree(a, bucket_size=size) for size in range(1, len(a) + 1)]
        for tree in trees:
            self._test_search_suite(tree, suite)

    def _test_search_suite(self, tree, suite):
        for case in suite:
            for search in case['searches']:
                args, kwargs = search[0], search[1]
                n = min(len(case['expected_indices']), kwargs['count'])

                neighbours = tree.search(*args, **kwargs)
                self.assertEqual(len(neighbours), n)
                self.assertEqual(neighbours['index'].tolist(), case['expected_indices'][:n])
                self.assertEqual([round(d, 3) for d in neighbours['squared_distance']], case['expected_squared_distances'][:n])


if __name__ == '__main__':
    from tests.run import run
    run('__main__')
