"""Glue for numeric data types from different modules."""

__all__ = ['Int8', 'UInt8', 'Int16', 'UInt16', 'Int32', 'UInt32', 'Float32',
           'Float64']

import ctypes

import numpy
import OpenGL.GL as gl


class Int8(object):
    """8-bit int type."""

    pass


class UInt8(object):
    """8-bit unsigned int type."""

    pass


class Int16(object):
    """16-bit int type."""

    pass


class UInt16(object):
    """16-bit unsigned int type."""

    pass


class Int32(object):
    """32-bit int type."""

    pass


class UInt32(object):
    """32-bit unsigned int type."""

    pass


class Float32(object):
    """32-bit floating-point type."""

    pass


class Float64(object):
    """64-bit floating-point type."""

    pass


_TYPES_DATA = {
    Int8: {
        'size': 1,
        'literal': 'b',
        'ctype': ctypes.c_int8,
        'gl': gl.GL_BYTE,
        'numpy': numpy.int8,
    },
    UInt8: {
        'size': 1,
        'literal': 'ub',
        'ctype': ctypes.c_uint8,
        'gl': gl.GL_UNSIGNED_BYTE,
        'numpy': numpy.uint8,
    },
    Int16: {
        'size': 2,
        'literal': 's',
        'ctype': ctypes.c_int16,
        'gl': gl.GL_SHORT,
        'numpy': numpy.int16,
    },
    UInt16: {
        'size': 2,
        'literal': 'us',
        'ctype': ctypes.c_uint16,
        'gl': gl.GL_UNSIGNED_SHORT,
        'numpy': numpy.uint16,
    },
    Int32: {
        'size': 4,
        'literal': 'i',
        'ctype': ctypes.c_int32,
        'gl': gl.GL_INT,
        'numpy': numpy.int32,
    },
    UInt32: {
        'size': 4,
        'literal': 'ui',
        'ctype': ctypes.c_uint32,
        'gl': gl.GL_UNSIGNED_INT,
        'numpy': numpy.uint32,
    },
    Float32: {
        'size': 4,
        'literal': 'f',
        'ctype': ctypes.c_float,
        'gl': gl.GL_FLOAT,
        'numpy': numpy.float32,
    },
    Float64: {
        'size': 8,
        'literal': 'd',
        'ctype': ctypes.c_double,
        'gl': gl.GL_DOUBLE,
        'numpy': numpy.float64,
    },
}

_TYPES = tuple(_TYPES_DATA.keys())

_CTYPE_TO_THIS = {_TYPES_DATA[this_type]['ctype']: this_type
                  for this_type in _TYPES}

_GL_TO_THIS = {_TYPES_DATA[this_type]['gl']: this_type
               for this_type in _TYPES}

_NUMPY_TO_THIS = {_TYPES_DATA[this_type]['numpy']: this_type
                  for this_type in _TYPES}


def get_types():
    """Retrieve all the numeric types supported by hienoi."""
    return _TYPES


def get_type_size(this_type):
    """Retrieve the size in bytes of a hienoi type."""
    return _TYPES_DATA[this_type]['size']


def get_type_literal(this_type):
    """Retrieve the string literal of a hienoi type."""
    return _TYPES_DATA[this_type]['literal']


def from_ctype(ctype_type):
    """Convert a C type to its hienoi equivalent."""
    return _CTYPE_TO_THIS[ctype_type]


def from_gl(gl_type):
    """Convert an OpenGL type to its hienoi equivalent."""
    return _GL_TO_THIS[gl_type]


def from_numpy(numpy_type):
    """Convert a NumPy type to its hienoi equivalent."""
    return _NUMPY_TO_THIS[numpy_type]


def to_ctype(this_type):
    """Convert a hienoi type to its ctypes equivalent."""
    return _TYPES_DATA[this_type]['ctype']


def to_gl(this_type):
    """Convert a hienoi type to its OpenGL equivalent."""
    return _TYPES_DATA[this_type]['gl']


def to_numpy(this_type):
    """Convert a hienoi type to its NumPy equivalent."""
    return _TYPES_DATA[this_type]['numpy']
