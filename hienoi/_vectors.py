"""Vector classes."""

__all__ = [
    'Vector2b', 'Vector2ub', 'Vector2s', 'Vector2us',
    'Vector2i', 'Vector2ui', 'Vector2f', 'Vector2d',
    'Vector3b', 'Vector3ub', 'Vector3s', 'Vector3us',
    'Vector3i', 'Vector3ui', 'Vector3f', 'Vector3d',
    'Vector4b', 'Vector4ub', 'Vector4s', 'Vector4us',
    'Vector4i', 'Vector4ui', 'Vector4f', 'Vector4d',
    'VECTOR2B', 'VECTOR2UB', 'VECTOR2S', 'VECTOR2US',
    'VECTOR2I', 'VECTOR2UI', 'VECTOR2F', 'VECTOR2D',
    'VECTOR3B', 'VECTOR3UB', 'VECTOR3S', 'VECTOR3US',
    'VECTOR3I', 'VECTOR3UI', 'VECTOR3F', 'VECTOR3D',
    'VECTOR4B', 'VECTOR4UB', 'VECTOR4S', 'VECTOR4US',
    'VECTOR4I', 'VECTOR4UI', 'VECTOR4F', 'VECTOR4D',
    'COLOR3UB', 'COLOR3F', 'COLOR4UB', 'COLOR4F',
]

import math
import sys

import hienoi._nani
import hienoi._numeric


if sys.version_info[0] == 2:
    def _iteritems(d, **kwargs):
        return d.iteritems(**kwargs)
else:
    def _iteritems(d, **kwargs):
        return iter(d.items(**kwargs))


_PATTERN = 'Vector%d'
_CTYPE_PATTERN = 'Vector%d%s'
_VIEW_PATTERN = 'Vector%d%sView'
_TOLERANCE = 1e-6


class _BaseMixin(object):
    """Vector's base mixin."""

    @classmethod
    def Vector2_lerp(cls, a, b, blend):
        return cls._class(a[0] + (b[0] - a[0]) * blend,
                          a[1] + (b[1] - a[1]) * blend)
        a + (b - a) * blend

    @classmethod
    def Vector3_lerp(cls, a, b, blend):
        return cls._class(a[0] + (b[0] - a[0]) * blend,
                          a[1] + (b[1] - a[1]) * blend,
                          a[2] + (b[2] - a[2]) * blend)

    @classmethod
    def Vector4_lerp(cls, a, b, blend):
        return cls._class(a[0] + (b[0] - a[0]) * blend,
                          a[1] + (b[1] - a[1]) * blend,
                          a[2] + (b[2] - a[2]) * blend,
                          a[3] + (b[3] - a[3]) * blend)

    def Vector2___repr__(self):
        return "%s(%s, %s)" % (self._class.__name__, self[0], self[1])

    def Vector3___repr__(self):
        return "%s(%s, %s, %s)" % (self._class.__name__,
                                   self[0], self[1], self[2])

    def Vector4___repr__(self):
        return "%s(%s, %s, %s, %s)" % (self._class.__name__,
                                       self[0], self[1], self[2], self[3])

    def Vector2___eq__(self, other):
        return self[0] == other[0] and self[1] == other[1]

    def Vector3___eq__(self, other):
        return (self[0] == other[0] and self[1] == other[1]
                and self[2] == other[2])

    def Vector4___eq__(self, other):
        return (self[0] == other[0] and self[1] == other[1]
                and self[2] == other[2] and self[3] == other[3])

    def Vector2___ne__(self, other):
        return self[0] != other[0] or self[1] != other[1]

    def Vector3___ne__(self, other):
        return (self[0] != other[0] or self[1] != other[1]
                or self[2] != other[2])

    def Vector4___ne__(self, other):
        return (self[0] != other[0] or self[1] != other[1]
                or self[2] != other[2] or self[3] != other[3])

    def Vector2___add__(self, other):
        return self._class(self[0] + other[0], self[1] + other[1])

    def Vector3___add__(self, other):
        return self._class(self[0] + other[0], self[1] + other[1],
                           self[2] + other[2])

    def Vector4___add__(self, other):
        return self._class(self[0] + other[0], self[1] + other[1],
                           self[2] + other[2], self[3] + other[3])

    def Vector2___sub__(self, other):
        return self._class(self[0] - other[0], self[1] - other[1])

    def Vector3___sub__(self, other):
        return self._class(self[0] - other[0], self[1] - other[1],
                           self[2] - other[2])

    def Vector4___sub__(self, other):
        return self._class(self[0] - other[0], self[1] - other[1],
                           self[2] - other[2], self[3] - other[3])

    def Vector2___mul__(self, other):
        return self._class(self[0] * other[0], self[1] * other[1])

    def Vector3___mul__(self, other):
        return self._class(self[0] * other[0], self[1] * other[1],
                           self[2] * other[2])

    def Vector4___mul__(self, other):
        return self._class(self[0] * other[0], self[1] * other[1],
                           self[2] * other[2], self[3] * other[3])

    def Vector2___truediv__(self, other):
        return self._class(self[0] / other[0], self[1] / other[1])

    def Vector3___truediv__(self, other):
        return self._class(self[0] / other[0], self[1] / other[1],
                           self[2] / other[2])

    def Vector4___truediv__(self, other):
        return self._class(self[0] / other[0], self[1] / other[1],
                           self[2] / other[2], self[3] / other[3])

    def Vector2___floordiv__(self, other):
        return self._class(self[0] // other[0], self[1] // other[1])

    def Vector3___floordiv__(self, other):
        return self._class(self[0] // other[0], self[1] // other[1],
                           self[2] // other[2])

    def Vector4___floordiv__(self, other):
        return self._class(self[0] // other[0], self[1] // other[1],
                           self[2] // other[2], self[3] // other[3])

    Vector2___div__ = Vector2___truediv__
    Vector3___div__ = Vector3___truediv__
    Vector4___div__ = Vector4___truediv__

    Vector2___radd__ = Vector2___add__
    Vector3___radd__ = Vector3___add__
    Vector4___radd__ = Vector4___add__

    def Vector2___rsub__(self, other):
        return self._class(other[0] - self[0], other[1] - self[1])

    def Vector3___rsub__(self, other):
        return self._class(other[0] - self[0], other[1] - self[1],
                           other[2] - self[2])

    def Vector4___rsub__(self, other):
        return self._class(other[0] - self[0], other[1] - self[1],
                           other[2] - self[2], other[3] - self[3])

    Vector2___rmul__ = Vector2___mul__
    Vector3___rmul__ = Vector3___mul__
    Vector4___rmul__ = Vector4___mul__

    def Vector2___rtruediv__(self, other):
        return self._class(other[0] / self[0], other[1] / self[1])

    def Vector3___rtruediv__(self, other):
        return self._class(other[0] / self[0], other[1] / self[1],
                           other[2] / self[2])

    def Vector4___rtruediv__(self, other):
        return self._class(other[0] / self[0], other[1] / self[1],
                           other[2] / self[2], other[3] / self[3])

    def Vector2___rfloordiv__(self, other):
        return self._class(other[0] // self[0], other[1] // self[1])

    def Vector3___rfloordiv__(self, other):
        return self._class(other[0] // self[0], other[1] // self[1],
                           other[2] // self[2])

    def Vector4___rfloordiv__(self, other):
        return self._class(other[0] // self[0], other[1] // self[1],
                           other[2] // self[2], other[3] // self[3])

    Vector2___rdiv__ = Vector2___rtruediv__
    Vector3___rdiv__ = Vector3___rtruediv__
    Vector4___rdiv__ = Vector4___rtruediv__

    def Vector2___iadd__(self, other):
        self[0] += other[0]
        self[1] += other[1]
        return self

    def Vector3___iadd__(self, other):
        self[0] += other[0]
        self[1] += other[1]
        self[2] += other[2]
        return self

    def Vector4___iadd__(self, other):
        self[0] += other[0]
        self[1] += other[1]
        self[2] += other[2]
        self[3] += other[3]
        return self

    def Vector2___isub__(self, other):
        self[0] -= other[0]
        self[1] -= other[1]
        return self

    def Vector3___isub__(self, other):
        self[0] -= other[0]
        self[1] -= other[1]
        self[2] -= other[2]
        return self

    def Vector4___isub__(self, other):
        self[0] -= other[0]
        self[1] -= other[1]
        self[2] -= other[2]
        self[3] -= other[3]
        return self

    def Vector2___imul__(self, other):
        self[0] *= other[0]
        self[1] *= other[1]
        return self

    def Vector3___imul__(self, other):
        self[0] *= other[0]
        self[1] *= other[1]
        self[2] *= other[2]
        return self

    def Vector4___imul__(self, other):
        self[0] *= other[0]
        self[1] *= other[1]
        self[2] *= other[2]
        self[3] *= other[3]
        return self

    def Vector2___itruediv__(self, other):
        self[0] /= other[0]
        self[1] /= other[1]
        return self

    def Vector3___itruediv__(self, other):
        self[0] /= other[0]
        self[1] /= other[1]
        self[2] /= other[2]
        return self

    def Vector4___itruediv__(self, other):
        self[0] /= other[0]
        self[1] /= other[1]
        self[2] /= other[2]
        self[3] /= other[3]
        return self

    def Vector2___ifloordiv__(self, other):
        self[0] //= other[0]
        self[1] //= other[1]
        return self

    def Vector3___ifloordiv__(self, other):
        self[0] //= other[0]
        self[1] //= other[1]
        self[2] //= other[2]
        return self

    def Vector4___ifloordiv__(self, other):
        self[0] //= other[0]
        self[1] //= other[1]
        self[2] //= other[2]
        self[3] //= other[3]
        return self

    Vector2___idiv__ = Vector2___itruediv__
    Vector3___idiv__ = Vector3___itruediv__
    Vector4___idiv__ = Vector4___itruediv__

    def Vector2___neg__(self):
        return self._class(-self[0], -self[1])

    def Vector3___neg__(self):
        return self._class(-self[0], -self[1], -self[2])

    def Vector4___neg__(self):
        return self._class(-self[0], -self[1], -self[2], -self[3])

    def Vector2___pos__(self):
        return self._class(+self[0], +self[1])

    def Vector3___pos__(self):
        return self._class(+self[0], +self[1], +self[2])

    def Vector4___pos__(self):
        return self._class(+self[0], +self[1], +self[2], +self[3])

    def Vector2___abs__(self):
        return self._class(abs(self[0]), abs(self[1]))

    def Vector3___abs__(self):
        return self._class(abs(self[0]), abs(self[1]), abs(self[2]))

    def Vector4___abs__(self):
        return self._class(abs(self[0]), abs(self[1]), abs(self[2]),
                           abs(self[3]))

    def Vector2_offset(self, value):
        return self._class(self[0] + value, self[1] + value)

    def Vector3_offset(self, value):
        return self._class(self[0] + value, self[1] + value, self[2] + value)

    def Vector4_offset(self, value):
        return self._class(self[0] + value, self[1] + value, self[2] + value,
                           self[3] + value)

    def Vector2_scale(self, value):
        return self._class(self[0] * value, self[1] * value)

    def Vector3_scale(self, value):
        return self._class(self[0] * value, self[1] * value, self[2] * value)

    def Vector4_scale(self, value):
        return self._class(self[0] * value, self[1] * value, self[2] * value,
                           self[3] * value)

    def Vector2_ioffset(self, value):
        self[0] += value
        self[1] += value
        return self

    def Vector3_ioffset(self, value):
        self[0] += value
        self[1] += value
        self[2] += value
        return self

    def Vector4_ioffset(self, value):
        self[0] += value
        self[1] += value
        self[2] += value
        self[3] += value
        return self

    def Vector2_iscale(self, value):
        self[0] *= value
        self[1] *= value
        return self

    def Vector3_iscale(self, value):
        self[0] *= value
        self[1] *= value
        self[2] *= value
        return self

    def Vector4_iscale(self, value):
        self[0] *= value
        self[1] *= value
        self[2] *= value
        self[3] *= value
        return self

    def Vector2_length(self):
        return math.sqrt(self[0] ** 2 + self[1] ** 2)

    def Vector3_length(self):
        return math.sqrt(self[0] ** 2 + self[1] ** 2 + self[2] ** 2)

    def Vector4_length(self):
        return math.sqrt(self[0] ** 2 + self[1] ** 2 + self[2] ** 2
                         + self[3] ** 2)

    def Vector2_squared_length(self):
        return self[0] ** 2 + self[1] ** 2

    def Vector3_squared_length(self):
        return self[0] ** 2 + self[1] ** 2 + self[2] ** 2

    def Vector4_squared_length(self):
        return self[0] ** 2 + self[1] ** 2 + self[2] ** 2 + self[3] ** 2

    def Vector2_dot(self, other):
        return self[0] * other[0] + self[1] * other[1]

    def Vector3_dot(self, other):
        return self[0] * other[0] + self[1] * other[1] + self[2] * other[2]

    def Vector4_dot(self, other):
        return (self[0] * other[0] + self[1] * other[1] + self[2] * other[2]
                + self[3] * other[3])


class _FloatingPointMixin(object):
    """Vector's floating-point mixin."""

    def Vector2_is_almost_equal(self, other, tolerance=_TOLERANCE):
        return (abs(self[0] - other[0]) <= tolerance
                and abs(self[1] - other[1]) <= tolerance)

    def Vector3_is_almost_equal(self, other, tolerance=_TOLERANCE):
        return (abs(self[0] - other[0]) <= tolerance
                and abs(self[1] - other[1]) <= tolerance
                and abs(self[2] - other[2]) <= tolerance)

    def Vector4_is_almost_equal(self, other, tolerance=_TOLERANCE):
        return (abs(self[0] - other[0]) <= tolerance
                and abs(self[1] - other[1]) <= tolerance
                and abs(self[2] - other[2]) <= tolerance
                and abs(self[3] - other[3]) <= tolerance)

    def Vector2_normalize(self):
        length = self.length()
        if abs(length) <= _TOLERANCE:
            return self._class(self[0], self[1])

        return self._class(self[0] / length, self[1] / length)

    def Vector3_normalize(self):
        length = self.length()
        if abs(length) <= _TOLERANCE:
            return self._class(self[0], self[1], self[2])

        return self._class(self[0] / length, self[1] / length,
                           self[2] / length)

    def Vector4_normalize(self):
        length = self.length()
        if abs(length) <= _TOLERANCE:
            return self._class(self[0], self[1], self[2], self[3])

        return self._class(self[0] / length, self[1] / length,
                           self[2] / length, self[3] / length)

    def Vector2_inormalize(self):
        length = self.length()
        if abs(length) <= _TOLERANCE:
            return self

        self[0] /= length
        self[1] /= length
        return self

    def Vector3_inormalize(self):
        length = self.length()
        if abs(length) <= _TOLERANCE:
            return self

        self[0] /= length
        self[1] /= length
        self[2] /= length
        return self

    def Vector4_inormalize(self):
        length = self.length()
        if abs(length) <= _TOLERANCE:
            return self

        self[0] /= length
        self[1] /= length
        self[2] /= length
        self[3] /= length
        return self


class _CtypeMixin(object):
    """Vector's ctype mixin."""

    @property
    def Vector2_x(self):
        return self[0]

    @property
    def Vector3_x(self):
        return self[0]

    @property
    def Vector4_x(self):
        return self[0]

    @Vector2_x.setter
    def Vector2_x(self, value):
        self[0] = value

    @Vector3_x.setter
    def Vector3_x(self, value):
        self[0] = value

    @Vector4_x.setter
    def Vector4_x(self, value):
        self[0] = value

    @property
    def Vector2_y(self):
        return self[1]

    @property
    def Vector3_y(self):
        return self[1]

    @property
    def Vector4_y(self):
        return self[1]

    @Vector2_y.setter
    def Vector2_y(self, value):
        self[1] = value

    @Vector3_y.setter
    def Vector3_y(self, value):
        self[1] = value

    @Vector4_y.setter
    def Vector4_y(self, value):
        self[1] = value

    @property
    def Vector3_z(self):
        return self[2]

    @property
    def Vector4_z(self):
        return self[2]

    @Vector3_z.setter
    def Vector3_z(self, value):
        self[2] = value

    @Vector4_z.setter
    def Vector4_z(self, value):
        self[2] = value

    @property
    def Vector4_w(self):
        return self[3]

    @Vector4_w.setter
    def Vector4_w(self, value):
        self[3] = value

    Vector3_r = Vector3_x
    Vector4_r = Vector4_x

    Vector3_g = Vector3_y
    Vector4_g = Vector4_y

    Vector3_b = Vector3_z
    Vector4_b = Vector4_z

    Vector4_a = Vector4_w

    def Vector2_assign(self, other):
        self[0] = other[0]
        self[1] = other[1]

    def Vector3_assign(self, other):
        self[0] = other[0]
        self[1] = other[1]
        self[2] = other[2]

    def Vector4_assign(self, other):
        self[0] = other[0]
        self[1] = other[1]
        self[2] = other[2]
        self[3] = other[3]

    def Vector2_set(self, x, y):
        self[:] = (x, y)

    def Vector3_set(self, x, y, z):
        self[:] = (x, y, z)

    def Vector4_set(self, x, y, z, w):
        self[:] = (x, y, z, w)


class _ViewMixin(object):
    """Vector's view mixin."""

    Vector2___slots__ = ('_data',)
    Vector3___slots__ = ('_data',)
    Vector4___slots__ = ('_data',)

    def Vector2___init__(self, data):
        self._data = data

    def Vector3___init__(self, data):
        self._data = data

    def Vector4___init__(self, data):
        self._data = data

    def Vector2___len__(self):
        return 2

    def Vector3___len__(self):
        return 3

    def Vector4___len__(self):
        return 4

    def Vector2___getitem__(self, idx):
        return self._data[idx]

    def Vector3___getitem__(self, idx):
        return self._data[idx]

    def Vector4___getitem__(self, idx):
        return self._data[idx]

    def Vector2___setitem__(self, idx, value):
        self._data[idx] = value

    def Vector3___setitem__(self, idx, value):
        self._data[idx] = value

    def Vector4___setitem__(self, idx, value):
        self._data[idx] = value

    @property
    def Vector2_x(self):
        return self._data[0]

    @property
    def Vector3_x(self):
        return self._data[0]

    @property
    def Vector4_x(self):
        return self._data[0]

    @Vector2_x.setter
    def Vector2_x(self, value):
        self._data[0] = value

    @Vector3_x.setter
    def Vector3_x(self, value):
        self._data[0] = value

    @Vector4_x.setter
    def Vector4_x(self, value):
        self._data[0] = value

    @property
    def Vector2_y(self):
        return self._data[1]

    @property
    def Vector3_y(self):
        return self._data[1]

    @property
    def Vector4_y(self):
        return self._data[1]

    @Vector2_y.setter
    def Vector2_y(self, value):
        self._data[1] = value

    @Vector3_y.setter
    def Vector3_y(self, value):
        self._data[1] = value

    @Vector4_y.setter
    def Vector4_y(self, value):
        self._data[1] = value

    @property
    def Vector3_z(self):
        return self._data[2]

    @property
    def Vector4_z(self):
        return self._data[2]

    @Vector3_z.setter
    def Vector3_z(self, value):
        self._data[2] = value

    @Vector4_z.setter
    def Vector4_z(self, value):
        self._data[2] = value

    @property
    def Vector4_w(self):
        return self._data[3]

    @Vector4_w.setter
    def Vector4_w(self, value):
        self._data[3] = value

    Vector3_r = Vector3_x
    Vector4_r = Vector4_x

    Vector3_g = Vector3_y
    Vector4_g = Vector4_y

    Vector3_b = Vector3_z
    Vector4_b = Vector4_z

    Vector4_a = Vector4_w

    def Vector2_assign(self, other):
        self._data[:] = other._data

    def Vector3_assign(self, other):
        self._data[:] = other._data

    def Vector4_assign(self, other):
        self._data[:] = other._data

    def Vector2_set(self, x, y):
        self._data[:] = (x, y)

    def Vector3_set(self, x, y, z):
        self._data[:] = (x, y, z)

    def Vector4_set(self, x, y, z, w):
        self._data[:] = (x, y, z, w)


_VECTOR_MIXINS = {
    hienoi._numeric.Int8: (_BaseMixin,),
    hienoi._numeric.UInt8: (_BaseMixin,),
    hienoi._numeric.Int16: (_BaseMixin,),
    hienoi._numeric.UInt16: (_BaseMixin,),
    hienoi._numeric.Int32: (_BaseMixin,),
    hienoi._numeric.UInt32: (_BaseMixin,),
    hienoi._numeric.Float32: (_BaseMixin, _FloatingPointMixin),
    hienoi._numeric.Float64: (_BaseMixin, _FloatingPointMixin),
}


def _define_vectors(size):
    """Define a triplet of objects describing a vector."""
    out = {}
    for element_type in hienoi._numeric.get_types():
        mixins = _VECTOR_MIXINS[type] = _VECTOR_MIXINS[element_type]
        literal = hienoi._numeric.get_type_literal(element_type)
        ctype_name = _CTYPE_PATTERN % (size, literal)
        ctype = _define_ctype(ctype_name, element_type, mixins, size)
        view_name = _VIEW_PATTERN % (size, literal)
        view = _define_view(view_name, ctype, mixins, size)
        nani = _define_nani(element_type, view, size)
        out[element_type] = (ctype, view, nani)

    return out


def _define_ctype(name, element_type, mixins, size):
    """Define a vector's ctype."""
    element_type = hienoi._numeric.to_ctype(element_type)
    mixins = (_CtypeMixin,) + mixins
    definition = _get_definition(mixins, size)

    # Required for Python 2.
    definition.update({
        '_length_': size,
        '_type_': element_type,
    })

    out = type(name, (element_type * size,), definition)
    out._class = out
    return out


def _define_view(name, ctype, mixins, size):
    """Define a vector's view."""
    mixins = (_ViewMixin,) + mixins
    definition = _get_definition(mixins, size)
    out = type(name, (), definition)
    out._class = ctype
    return out


def _define_nani(element_type, view, size):
    """Define a vector's nani."""
    return hienoi._nani.Array(
        element_type=hienoi._nani.Number(type=element_type),
        shape=size,
        view=view)


def _get_definition(mixins, size):
    """Retrieve a vector's definition."""
    out = {}
    prefix = _PATTERN % (size,)
    prefix_length = len(prefix)
    for mixin in mixins:
        out.update({key[prefix_length + 1:]: value
                    for key, value in _iteritems(mixin.__dict__)
                    if key.startswith(prefix)})

    return out


_VECTORS2 = _define_vectors(2)
Vector2b, Vector2bView, VECTOR2B = _VECTORS2[hienoi._numeric.Int8]
Vector2ub, Vector2ubView, VECTOR2UB = _VECTORS2[hienoi._numeric.UInt8]
Vector2s, Vector2sView, VECTOR2S = _VECTORS2[hienoi._numeric.Int16]
Vector2us, Vector2usView, VECTOR2US = _VECTORS2[hienoi._numeric.UInt16]
Vector2i, Vector2iView, VECTOR2I = _VECTORS2[hienoi._numeric.Int32]
Vector2ui, Vector2uiView, VECTOR2UI = _VECTORS2[hienoi._numeric.UInt32]
Vector2f, Vector2fView, VECTOR2F = _VECTORS2[hienoi._numeric.Float32]
Vector2d, Vector2dView, VECTOR2D = _VECTORS2[hienoi._numeric.Float64]

_VECTORS3 = _define_vectors(3)
Vector3b, Vector3bView, VECTOR3B = _VECTORS3[hienoi._numeric.Int8]
Vector3ub, Vector3ubView, VECTOR3UB = _VECTORS3[hienoi._numeric.UInt8]
Vector3s, Vector3sView, VECTOR3S = _VECTORS3[hienoi._numeric.Int16]
Vector3us, Vector3usView, VECTOR3US = _VECTORS3[hienoi._numeric.UInt16]
Vector3i, Vector3iView, VECTOR3I = _VECTORS3[hienoi._numeric.Int32]
Vector3ui, Vector3uiView, VECTOR3UI = _VECTORS3[hienoi._numeric.UInt32]
Vector3f, Vector3fView, VECTOR3F = _VECTORS3[hienoi._numeric.Float32]
Vector3d, Vector3dView, VECTOR3D = _VECTORS3[hienoi._numeric.Float64]

_VECTORS4 = _define_vectors(4)
Vector4b, Vector4bView, VECTOR4B = _VECTORS4[hienoi._numeric.Int8]
Vector4ub, Vector4ubView, VECTOR4UB = _VECTORS4[hienoi._numeric.UInt8]
Vector4s, Vector4sView, VECTOR4S = _VECTORS4[hienoi._numeric.Int16]
Vector4us, Vector4usView, VECTOR4US = _VECTORS4[hienoi._numeric.UInt16]
Vector4i, Vector4iView, VECTOR4I = _VECTORS4[hienoi._numeric.Int32]
Vector4ui, Vector4uiView, VECTOR4UI = _VECTORS4[hienoi._numeric.UInt32]
Vector4f, Vector4fView, VECTOR4F = _VECTORS4[hienoi._numeric.Float32]
Vector4d, Vector4dView, VECTOR4D = _VECTORS4[hienoi._numeric.Float64]

# Color aliases.
COLOR3UB = VECTOR3UB._replace(
    element_type=VECTOR3UB.element_type._replace(default=255))
COLOR3F = VECTOR3F._replace(
    element_type=VECTOR3F.element_type._replace(default=1.0))
COLOR4UB = VECTOR4UB._replace(
    element_type=VECTOR4UB.element_type._replace(default=255))
COLOR4F = VECTOR4F._replace(
    element_type=VECTOR4F.element_type._replace(default=1.0))
