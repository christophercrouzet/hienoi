"""Dynamic array based on NumPy."""

import math

import numpy


_GROW_FACTOR = 1.5
assert _GROW_FACTOR > 1.0


class DynamicArray(object):
    """Dynamic array based on NumPy.

    This represents a dynamic contiguous array along the lines of the C++
    ``std::vector`` container.
    """

    @classmethod
    def from_buffer(cls, buf, dtype):
        """Unpack a buffer object into a new array."""
        this = DynamicArray(0, dtype)
        this._array = numpy.frombuffer(buf, dtype)
        this._size = len(this._array)
        return this

    def __init__(self, capacity, dtype):
        self._array = numpy.empty(capacity, dtype=dtype)
        self._size = 0

    def __len__(self):
        return self._size

    @property
    def data(self):
        return self._array[:self._size]

    @property
    def capacity(self):
        return len(self._array)

    @property
    def dtype(self):
        return self._array.dtype

    def copy_from(self, data):
        """Replace the data with a copy of some other data."""
        size = len(data)
        self.grow(size, copy=False)
        for field in self._array.dtype.fields:
            self._array[field][:size] = data[field]

        self._size = size

    def grow(self, requested, copy=True):
        """Increase the storage's capacity if needed."""
        if requested <= len(self._array):
            return

        capacity = max(requested,
                       int(max(len(self._array) * _GROW_FACTOR,
                               math.ceil(1.0 / (_GROW_FACTOR - 1.0)) * 2)))
        array = numpy.empty(capacity, dtype=self._array.dtype)
        if copy:
            array[:self._size] = self._array[:self._size]
        else:
            self._size = 0

        self._array = array

    def resize(self, requested, copy=True):
        """Change the size of the array."""
        self.grow(requested, copy=copy)
        self._size = requested

    def append(self, data):
        """Append a new element."""
        new_size = self._size + 1
        self.grow(new_size)
        self._array[self._size] = data
        out = self._array[self._size]
        self._size = new_size
        return out

    def extend(self, data):
        """Append multiple elements."""
        new_size = self._size + len(data)
        self.grow(new_size)
        self._array[self._size:new_size] = data
        out = self._array[self._size:new_size]
        self._size = new_size
        return out

    def clear(self):
        """Clear the data."""
        self._size = 0
