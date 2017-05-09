#!/usr/bin/env python

import os
import sys
import unittest

import numpy

_HERE = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(_HERE, os.pardir)))

from hienoi._orderedbuffer import OrderedBuffer


class OrderedBufferTest(unittest.TestCase):

    def test_constructor(self):
        b = OrderedBuffer(256, numpy.dtype(numpy.float32))
        self.assertEqual(len(b), 0)
        self.assertEqual(b.bucket_capacity, 256)
        self.assertEqual(b.chunks, [])
        self.assertEqual([chunk for chunk in b.chunks], [])

    def test_append(self):
        b = OrderedBuffer(3, numpy.dtype(numpy.int8))

        data = b.append(9)
        self.assertEqual(data, 9)
        self.assertIsInstance(data, numpy.int8)
        self.assertEqual(len(b), 1)
        self.assertEqual([chunk.tolist() for chunk in b.chunks], [[9]])

        data = b.append(1)
        self.assertIsInstance(data, numpy.int8)
        self.assertEqual(len(b), 2)
        self.assertEqual([chunk.tolist() for chunk in b.chunks], [[9, 1]])

        data = b.append(4)
        self.assertIsInstance(data, numpy.int8)
        self.assertEqual(len(b), 3)
        self.assertEqual([chunk.tolist() for chunk in b.chunks], [[9, 1, 4]])

        data = b.append(0)
        self.assertIsInstance(data, numpy.int8)
        self.assertEqual(len(b), 4)
        self.assertEqual([chunk.tolist() for chunk in b.chunks], [[9, 1, 4], [0]])

    def test_extend(self):
        b = OrderedBuffer(3, numpy.dtype(numpy.int8))

        # Add an empty bunch.
        bunch = b.extend([])
        self.assertEqual(bunch.tolist(), [])
        self.assertEqual(len(bunch), 0)
        self.assertIsNone(bunch.base)
        self.assertEqual(len(b), 0)
        self.assertEqual([chunk.tolist() for chunk in b.chunks], [])

        # Fill the first bucket.
        bunch = b.extend([9, 1, 4])
        self.assertEqual(bunch.tolist(), [9, 1, 4])
        self.assertEqual(len(bunch), 3)
        self.assertEqual(len(bunch.base), 3)
        self.assertEqual(len(b), 3)
        self.assertEqual([chunk.tolist() for chunk in b.chunks], [[9, 1, 4]])

        # Partly fill the second bucket.
        bunch = b.extend([0, 7])
        self.assertEqual(bunch.tolist(), [0, 7])
        self.assertEqual(len(bunch), 2)
        self.assertEqual(len(bunch.base), 3)
        self.assertEqual(len(b), 5)
        self.assertEqual([chunk.tolist() for chunk in b.chunks], [[9, 1, 4], [0, 7]])

        # This doesn't fit without overflowing the second bucket so it is
        # stored as a bunch.
        bunch = b.extend([5, 2])
        self.assertEqual(len(bunch), 2)
        self.assertIsNone(bunch.base)
        self.assertEqual(len(b), 7)
        self.assertEqual([chunk.tolist() for chunk in b.chunks], [[9, 1, 4], [0, 7], [5, 2]])

        # Finish filling the second bucket while preserving the order.
        bunch = b.extend([3])
        self.assertEqual(len(bunch), 1)
        self.assertEqual(len(bunch.base), 3)
        self.assertEqual(len(b), 8)
        self.assertEqual([chunk.tolist() for chunk in b.chunks], [[9, 1, 4], [0, 7], [5, 2], [3]])

        # Partly fill a third bucket.
        bunch = b.extend([6])
        self.assertEqual(len(bunch), 1)
        self.assertEqual(len(bunch.base), 3)
        self.assertEqual(len(b), 9)
        self.assertEqual([chunk.tolist() for chunk in b.chunks], [[9, 1, 4], [0, 7], [5, 2], [3], [6]])

        # Add a bunch larger than the bucket capacity.
        bunch = b.extend([1, 2, 3, 4, 5])
        self.assertEqual(len(bunch), 5)
        self.assertIsNone(bunch.base)
        self.assertEqual(len(b), 14)
        self.assertEqual([chunk.tolist() for chunk in b.chunks], [[9, 1, 4], [0, 7], [5, 2], [3], [6], [1, 2, 3, 4, 5]])

        # Finish filling the third bucket.
        bunch = b.extend([7, 8])
        self.assertEqual(len(bunch), 2)
        self.assertEqual(len(bunch.base), 3)
        self.assertEqual(len(b), 16)
        self.assertEqual([chunk.tolist() for chunk in b.chunks], [[9, 1, 4], [0, 7], [5, 2], [3], [6], [1, 2, 3, 4, 5], [7, 8]])

        # Partly fill a fourth bucket.
        bunch = b.extend([9])
        self.assertEqual(len(bunch), 1)
        self.assertEqual(len(bunch.base), 3)
        self.assertEqual(len(b), 17)
        self.assertEqual([chunk.tolist() for chunk in b.chunks], [[9, 1, 4], [0, 7], [5, 2], [3], [6], [1, 2, 3, 4, 5], [7, 8], [9]])

        # Finish filling the fourth bucket.
        bunch = b.extend([8, 7])
        self.assertEqual(len(bunch), 2)
        self.assertEqual(len(bunch.base), 3)
        self.assertEqual(len(b), 19)
        self.assertEqual([chunk.tolist() for chunk in b.chunks], [[9, 1, 4], [0, 7], [5, 2], [3], [6], [1, 2, 3, 4, 5], [7, 8], [9, 8, 7]])

    def test_clear(self):
        b = OrderedBuffer(3, numpy.dtype(numpy.int8))
        b.extend([9, 1])
        b.extend([1, 2, 3, 4, 5])
        b.append(4)
        self.assertEqual(len(b), 8)
        self.assertEqual([chunk.tolist() for chunk in b.chunks], [[9, 1], [1, 2, 3, 4, 5], [4]])

        b.clear()
        self.assertEqual(len(b), 0)
        self.assertEqual([chunk.tolist() for chunk in b.chunks], [])

        b.append(0)
        b.extend([7, 8, 9])
        b.append(1)
        b.extend([2])
        self.assertEqual(len(b), 6)
        self.assertEqual([chunk.tolist() for chunk in b.chunks], [[0], [7, 8, 9], [1, 2]])


if __name__ == '__main__':
    from tests.run import run
    run('__main__')
