"""Common data structures, enumerators, and constants."""

import collections

import hienoi._nani
from hienoi._numeric import Float32
from hienoi._vectors import VECTOR2F, COLOR4F


class ParticleDisplay(object):
    """Enumerator for the displays available to draw particles.

    Attributes
    ----------
    POINT
    CIRCLE
    DISC
    """

    POINT = 0
    CIRCLE = 1
    DISC = 2
    _LAST = DISC


class GraphicsAPI(object):
    """Enumerator for the graphics APIs supported."""

    OPENGL = 0


class GLProfile(object):
    """Enumerator for the OpenGL profiles supported."""

    CORE = 0


class UserData(object):
    """Placeholder for user data."""
    pass


_ParticleAttributes = collections.namedtuple(
    'ParticleAttributes', (
        'position',
        'size',
        'color',
    ))


class ParticleAttributes(_ParticleAttributes):
    """Particle attributes to be used by the renderer."""

    __slots__ = ()


_Attribute = collections.namedtuple(
    'Attribute', (
        'nani',
        'element_type',
        'count',
    ))


class Attribute(_Attribute):
    """Attribute."""

    __slots__ = ()


PARTICLE_ATTRS = ParticleAttributes(
    position=Attribute(
        nani=VECTOR2F,
        element_type=VECTOR2F.element_type.type,
        count=2),
    size=Attribute(
        nani=hienoi._nani.Number(type=Float32, default=1.0),
        element_type=Float32,
        count=1),
    color=Attribute(
        nani=COLOR4F,
        element_type=COLOR4F.element_type.type,
        count=4))

PARTICLE_NANI = hienoi._nani.resolve(
    hienoi._nani.Structure(
        fields=[(field, getattr(PARTICLE_ATTRS, field).nani)
                for field in PARTICLE_ATTRS._fields],
        name='Particle'))
