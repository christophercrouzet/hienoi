"""Bucket buffer based on NumPy."""

import collections
import itertools
import sys

import numpy


if sys.version_info[0] == 2:
    _range = xrange
    _zip = itertools.izip
else:
    _range = range
    _zip = zip


_Bunch = collections.namedtuple(
    '_Bunch', (
        'position',
        'data',
    ))


class OrderedBuffer(object):
    """Ordered buffer based on NumPy.

    Prevents reallocation and hence invalidation of previously added elements.
    """

    def __init__(self, bucket_capacity, dtype):
        if bucket_capacity < 1:
            raise ValueError("A minimum bucket capacity of 1 is expected.")

        self._dtype = dtype

        self._buckets = []
        self._bucket_capacity = bucket_capacity
        self._pos = [0, 0]

        self._bunchs = []

    def __len__(self):
        return (self._bucket_capacity * self._pos[0] + self._pos[1]
                + sum(len(bunch.data) for bunch in self._bunchs))

    @property
    def chunks(self):
        out = []
        i, j = (0, 0)
        bunchs = self._bunchs + [_Bunch(position=self._pos, data=[])]
        for bunch in bunchs:
            m, n = bunch.position
            while i < m:
                out.append(self._buckets[i][j:])
                i += 1
                j = 0

            if j < n:
                out.append(self._buckets[i][j:n])

            if len(bunch.data):
                out.append(bunch.data)

            i, j = bunch.position

        return out

    @property
    def bucket_capacity(self):
        return self._bucket_capacity

    @property
    def dtype(self):
        return self._dtype

    def append(self, data):
        """Append a new element."""
        return self._push(data, 1)[0]

    def extend(self, data):
        """Append a bunch of new elements."""
        size = len(data)
        if size < 1:
            return numpy.empty(0, dtype=self._dtype)

        return self._push(numpy.asarray(data, dtype=self._dtype), size)

    def clear(self):
        """Clear the data."""
        self._pos = [0, 0]
        self._bunchs = []

    def _push(self, data, size):
        """Add new element(s) at the end."""
        i, j = self._pos
        if self._bucket_capacity - j >= size:
            if i == len(self._buckets):
                self._buckets.append(
                    numpy.empty(self._bucket_capacity, dtype=self._dtype))

            self._buckets[i][j:j + size] = data
            out = self._buckets[i][j:j + size]

            j = (j + size) % self._bucket_capacity
            self._pos = [i + 1 if j == 0 else i, j]
        else:
            self._bunchs.append(_Bunch(position=self._pos, data=data))
            out = data

        return out
