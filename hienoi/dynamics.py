"""Physics systems evolving over time."""

import itertools
import math
import sys

import numpy

import hienoi._common
import hienoi._numeric
from hienoi._common import UserData
from hienoi._dynamicarray import DynamicArray
from hienoi._kdtree import KDTree
from hienoi._nani import Bool, Number, READ_ONLY, PickableNaniStructure
from hienoi._numeric import Int32, Float32
from hienoi._orderedbuffer import OrderedBuffer
from hienoi._vectors import VECTOR2F


if sys.version_info[0] == 2:
    def _iteritems(d, **kwargs):
        return d.iteritems(**kwargs)

    _zip = itertools.izip
else:
    def _iteritems(d, **kwargs):
        return iter(d.items(**kwargs))

    _zip = zip


class ParticleSimulation(object):
    """Particle simulation.

    Such a system allows to have particles moving over time based on basic laws
    of motion.

    Each particle have attributes such as position, velocity, force, and mass.
    What the force attribute really represents is the acceleration force. When
    running the simulation, at each time interval `t` defined by the
    simulation's time step, the simulation is stepped, that is, its current
    state is solved to advance to the next state corresponding to a later point
    in time `t + time_step`.

    The solver's operation consists in integrating the [acceleration] force of
    each particle to retrieve their new velocity, and in turn integrating this
    velocity to obtain their new position. The particles end up moving over
    time according to the forces applied to them.

    Particles can be added, removed, and can have their attributes modified at
    any point in time through three hooks provided: ``initialize_callback``,
    ``presolve_callback``, and ``postsolve_callback``.

    Warning
    -------
    Any modification to the particle attributes is applied in-place, that is
    with immediate effect. However the addition and removal of particles is
    only really executed at a later time.

    This behaviour is noticable when querying the simulation's state: a
    particle just added isn't taken into account (it lives in a buffer), while
    one that has just been marked as 'not alive' is still queried.

    Another way to reason about this is to think of each callback as being part
    of a node graph. A callback is like a node which takes an upstream
    simulation state as input and outputs a new simulation state downstream.
    Whenever querying is required, it is being done on the set of particles
    available in the upstream state, and the downstream state is only written
    once the callback has finished evaluating.

    The method :meth:`consolidate` is the one responsible for processing all
    the additions and removals requested and is automatically run after
    each callback. It can also be called manually within the callbacks but it
    isn't a recommended approach since it comes with a drawbacks, see
    :meth:`consolidate`.

    Parameters
    ----------
    time_step : float
        See :attr:`ParticleSimulation.time_step`.
    initial_particle_capacity : int
        Initial number of elements allocated for the particle array.
    particle_bucket_buffer_capacity : int
        New particles cannot always be directly added to the array and
        therefore temporarily end up in a buffer until the function
        :func:`consolidate` is run. The given bucket buffer capacity
        represents the number of elements that a single bucket can hold.
    particle_attributes : sequence of hienoi.Field or compatible tuple
        Additional attributes to define for each particle.
    initialize_callback : function
        Callback function to initialize the simulation.
        It takes a single argument ``sim``, an instance of this class.
    presolve_callback : function
        Callback function executed before solving the simulation.
        It takes a single argument ``sim``, an instance of this class.
    postsolve_callback : function
        Callback function executed after solving the simulation.
        It takes a single argument ``sim``, an instance of this class.

    Attributes
    ----------
    time_step : float
        Amount by which the simulation time is being incremented by at each
        step. The lower the value, the more accurate the simulation is, but the
        more compute-intensive it becomes.
    time : float
        Simulation time.
    last_particle_id : int
        ID of the last particle created.
    particles : sequence of nani.Particle
        All the particles.
    user_data : object
        Attribute reserved for any user data.
    """

    _ATTRS = (
        ('id', Number(type=Int32, default=-1), READ_ONLY),
        ('alive', Bool(default=True)),
        ('position', hienoi._common.PARTICLE_ATTRS.position.nani),
        ('velocity', VECTOR2F),
        ('force', VECTOR2F),
        ('mass', Number(type=Float32, default=1.0)),
        ('size', hienoi._common.PARTICLE_ATTRS.size.nani),
        ('color', hienoi._common.PARTICLE_ATTRS.color.nani),
    )
    _ATTR_ID_NUMPY_TYPE = hienoi._numeric.to_numpy(_ATTRS[0][1].type)

    class Neighbours(object):
        """Neighbour sequence."""

        def __init__(self, neighbours, particles, particle_view):
            self._neighbours = neighbours
            self._particles = particles
            self._particle_view = particle_view

        def __len__(self):
            return len(self._neighbours)

        def __iter__(self):
            return (
                ParticleSimulation.Neighbour(
                    item, self._particle_view(self._particles[item['index']]))
                for item in self._neighbours)

        @property
        def data(self):
            return self._neighbours

    class Neighbour(object):
        """Neighbour object."""

        def __init__(self, data, particle):
            self._data = data
            self._particle = particle

        @property
        def particle(self):
            return self._particle

        @property
        def squared_distance(self):
            return self._data['squared_distance']

        @property
        def distance(self):
            return math.sqrt(self._data['squared_distance'])

    def __init__(self,
                 time_step=0.02,
                 initial_particle_capacity=512,
                 particle_bucket_buffer_capacity=256,
                 particle_attributes=None,
                 initialize_callback=None,
                 presolve_callback=None,
                 postsolve_callback=None):
        attrs = self._ATTRS
        if particle_attributes is not None:
            attrs += particle_attributes

        self._nani = PickableNaniStructure(attrs, 'Particle')

        self._presolve_callback = presolve_callback
        self._postsolve_callback = postsolve_callback

        self._time_step = time_step
        self._time = 0.0
        self._last_id = -1

        # Particles are stored in a contiguous, resizable, array.
        self._array = DynamicArray(initial_particle_capacity, self._nani.dtype)

        # New particles are always added into a temporary buffer until
        # consolidation.
        self._buffer = OrderedBuffer(particle_bucket_buffer_capacity,
                                     self._nani.dtype)

        self._kd_tree = None

        self.user_data = UserData()
        if initialize_callback:
            initialize_callback(self)
            self.consolidate()

    @property
    def time_step(self):
        return self._time_step

    @property
    def time(self):
        return self._time

    @property
    def last_particle_id(self):
        return self._last_id

    @property
    def particles(self):
        return self._nani.view(self._array.data)

    def add_particle(self, **kwargs):
        """Add a new particle.

        Any read-only attribute passed to the ``kwargs`` parameter, such as the
        'id' attribute, are discarded.

        Parameters
        ----------
        kwargs
            Keyword arguments to override the default attribute values.

        Returns
        -------
        nani.Particle
            The new particle.
        """
        kwargs = kwargs.copy()
        kwargs['id'] = self._last_id + 1
        particle = self._buffer.append(self._nani.default._replace(**kwargs))
        self._last_id = particle['id']
        return self._nani.element_view(particle)

    def add_particles(self, count):
        """Add a bunch of new particles.

        Parameters
        ----------
        count : int
            Number of particles to add.

        Returns
        -------
        sequence of nani.Particle
            The new particles.
        """
        array = numpy.empty(count, dtype=self._nani.dtype)
        array[:] = self._nani.default
        array['id'] = numpy.arange(self._last_id + 1,
                                   self._last_id + 1 + count)
        particles = self._buffer.extend(array)
        self._last_id = particles['id'][-1]
        return self._nani.view(particles)

    def get_particle(self, id):
        """Retrieve a particle.

        Parameters
        ----------
        id : int
            ID of the particle to retrieve.

        Returns
        -------
        nani.Particle
            The particle found.
        """
        # PRECONDITION: `self._array.data` sorted by id.
        id = self._ATTR_ID_NUMPY_TYPE(id)
        idx = numpy.searchsorted(self._array.data['id'], id)
        if idx < len(self._array) and self._array.data[idx]['id'] == id:
            return self._nani.element_view(self._array.data[idx])

        raise ValueError("No particle found with ID '%d'." % (id,))

    def get_neighbour_particles(self, point, count=1, radius=None, sort=False):
        """Retrieve the particles neighbour to a point."""
        if self._kd_tree is None:
            self._kd_tree = KDTree(self._array.data['position'])

        neighbours = self._kd_tree.search(point, count, radius, sort)
        return self.Neighbours(neighbours, self._array.data,
                               self._nani.element_view)

    def step(self):
        """Advance the simulation by one step.

        This is where the velocity and position for each particle are solved.
        """
        self._time += self.time_step

        if self._presolve_callback:
            self._presolve_callback(self)
            self.consolidate()

        particles = self._array.data
        _solve(particles, self.time_step)
        particles['force'] = 0

        if self._postsolve_callback:
            self._postsolve_callback(self)
            self.consolidate()

    def consolidate(self):
        """Execute the addition and removal of particles.

        Warning
        -------
        This operation is likely to invalidate any previous reference to
        particles or to query objects.

        >>> import hienoi.dynamics
        >>> sim = hienoi.dynamics.ParticleSimulation()
        >>> p0 = sim.add_particle()
        >>> sim.consolidate()
        >>> p0 = sim.get_particle(0)
        >>> p0.force = [1.0, 1.0]

        In the example above, the particle with ID 0 needs to be retrieved
        again after consolidation. Otherwise the new force set would have been
        applied to an invalid particle.
        """
        # POSTCONDITION: `self._array.data` sorted by id.
        chunks = ([self._array.data]
                  + [chunk for chunk in self._buffer.chunks])
        filters = [chunk['alive'] for chunk in chunks]
        counts = [numpy.count_nonzero(filter) for filter in filters]
        new_size = sum(counts)

        if (len(self._buffer) == 0
                and new_size == len(self._array)):
            return

        self._array.resize(new_size, copy=False)
        array = self._array.data

        i = 0
        for filter, chunk, count in _zip(filters, chunks, counts):
            if count == len(chunk):
                array[i:i + count] = chunk
            else:
                numpy.compress(filter, chunk, out=array[i:i + count])

            i += count

        self._buffer.clear()
        self._kd_tree = None


def _solve(particles, time_step):
    """Solve the particles."""
    # Implemented as a simple Euler integration.
    particles['velocity'] += (particles['force'] * time_step
                              / particles['mass'][:, numpy.newaxis])
    particles['position'] += particles['velocity'] * time_step
