#!/usr/bin/env python

import os
import sys
import unittest

import numpy

_HERE = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(_HERE, os.pardir)))

from hienoi._dynamicarray import DynamicArray


class DynamicArrayTest(unittest.TestCase):

    def test_constructor(self):
        a = DynamicArray(0, numpy.dtype(numpy.float32))
        self.assertEqual(len(a), 0)
        self.assertEqual(a.capacity, 0)
        self.assertEqual(len(a.data), 0)
        self.assertEqual(len(a.data.base), 0)
        self.assertEqual(a.data.tolist(), [])

        a = DynamicArray(256, numpy.dtype(numpy.float32))
        self.assertEqual(len(a), 0)
        self.assertEqual(a.capacity, 256)
        self.assertEqual(len(a.data), 0)
        self.assertEqual(len(a.data.base), 256)
        self.assertEqual(a.data.tolist(), [])

    def test_data(self):
        a = DynamicArray(256, numpy.dtype(numpy.int8))
        a.extend([0, 1, 4, 9])
        self.assertEqual(a.data.tolist(), [0, 1, 4, 9])
        self.assertEqual(len(a.data.base), 256)

    def test_capacity(self):
        a = DynamicArray(0, numpy.dtype(numpy.float32))
        self.assertEqual(a.capacity, 0)
        a.extend([0, 1, 4, 9])
        self.assertGreaterEqual(a.capacity, 4)

        a = DynamicArray(256, numpy.dtype(numpy.float32))
        self.assertEqual(a.capacity, 256)
        a.extend([1, 0, 1, 4, 9])
        self.assertEqual(a.capacity, 256)

    def test_copy_from(self):
        a = DynamicArray(0, numpy.dtype([
            ('a', numpy.int8),
            ('b', numpy.float32),
            ('c', numpy.float64),
        ]))
        a.extend([
            (4, 3.932, 902.345),
            (7, 1.016, 548.229),
            (2, 0.542, 771.031),
            (8, 5.429, 858.063),
        ])
        b = DynamicArray(0, numpy.dtype([
            ('a', numpy.int8),
            ('c', numpy.float64),
        ]))
        b.copy_from(a.data)
        self.assertEqual(len(b), 4)
        self.assertEqual(b.data.tolist(), [(4, 902.345), (7, 548.229), (2, 771.031), (8, 858.063),])

    def test_grow(self):
        a = DynamicArray(0, numpy.dtype(numpy.int8))
        self.assertEqual(len(a), 0)
        self.assertEqual(len(a.data), 0)

        a.grow(4)
        self.assertEqual(len(a), 0)
        self.assertEqual(len(a.data), 0)
        self.assertGreaterEqual(a.capacity, 4)

        a.extend([0, 1, 4, 9])
        self.assertEqual(len(a), 4)
        self.assertEqual(len(a.data), 4)
        self.assertEqual(a.data.tolist(), [0, 1, 4, 9])

        a.grow(2)
        self.assertEqual(len(a), 4)
        self.assertEqual(len(a.data), 4)
        self.assertGreaterEqual(a.capacity, 4)
        self.assertEqual(a.data.tolist(), [0, 1, 4, 9])

        request = a.capacity * 2
        a.grow(request)
        self.assertEqual(len(a), 4)
        self.assertEqual(len(a.data), 4)
        self.assertGreaterEqual(a.capacity, request)
        self.assertEqual(a.data.tolist(), [0, 1, 4, 9])

        request = a.capacity * 2
        a.grow(request, copy=False)
        self.assertEqual(len(a), 0)
        self.assertEqual(len(a.data), 0)
        self.assertGreaterEqual(a.capacity, request)
        self.assertEqual(a.data.tolist(), [])

    def test_resize(self):
        a = DynamicArray(0, numpy.dtype(numpy.int8))
        a.extend([0, 1, 4, 9])
        self.assertEqual(len(a), 4)
        self.assertEqual(len(a.data), 4)
        self.assertEqual(a.data.tolist(), [0, 1, 4, 9])

        a.resize(2)
        self.assertEqual(len(a), 2)
        self.assertEqual(len(a.data), 2)
        self.assertEqual(a.data.tolist(), [0, 1])

        request = a.capacity * 2
        a.resize(request)
        self.assertEqual(len(a), request)
        self.assertEqual(len(a.data), request)
        self.assertGreaterEqual(a.capacity, request)
        self.assertEqual(a.data.tolist()[:2], [0, 1])

    def test_append(self):
        a = DynamicArray(0, numpy.dtype(numpy.int8))
        self.assertEqual(len(a), 0)
        self.assertEqual(len(a.data), 0)

        data = a.append(0)
        self.assertEqual(data, 0)
        self.assertIsInstance(data, numpy.int8)
        self.assertEqual(len(a), 1)
        self.assertEqual(a.data.tolist(), [0])

        data = a.append(1)
        self.assertEqual(data, 1)
        self.assertIsInstance(data, numpy.int8)
        self.assertEqual(len(a), 2)
        self.assertEqual(a.data.tolist(), [0, 1])

        data = a.append(4)
        self.assertEqual(data, 4)
        self.assertIsInstance(data, numpy.int8)
        self.assertEqual(len(a), 3)
        self.assertEqual(a.data.tolist(), [0, 1, 4])

        data = a.append(9)
        self.assertEqual(data, 9)
        self.assertIsInstance(data, numpy.int8)
        self.assertEqual(len(a), 4)
        self.assertEqual(a.data.tolist(), [0, 1, 4, 9])

    def test_extend(self):
        a = DynamicArray(0, numpy.dtype(numpy.int8))
        self.assertEqual(len(a), 0)
        self.assertEqual(len(a.data), 0)

        a.extend([0, 1, 4, 9])
        self.assertEqual(len(a), 4)
        self.assertEqual(a.data.tolist(), [0, 1, 4, 9])

        a.extend([2, 4, 6, 8])
        self.assertEqual(len(a), 8)
        self.assertEqual(a.data.tolist(), [0, 1, 4, 9, 2, 4, 6, 8])

        a.extend(numpy.arange(4))
        self.assertEqual(len(a), 12)
        self.assertEqual(a.data.tolist(), [0, 1, 4, 9, 2, 4, 6, 8, 0, 1, 2, 3])

    def test_clear(self):
        a = DynamicArray(0, numpy.dtype(numpy.int8))
        a.extend([0, 1, 4, 9])
        self.assertEqual(len(a), 4)
        self.assertEqual(a.data.tolist(), [0, 1, 4, 9])

        a.clear()
        self.assertEqual(len(a), 0)
        self.assertEqual(a.data.tolist(), [])


if __name__ == '__main__':
    from tests.run import run
    run('__main__')
