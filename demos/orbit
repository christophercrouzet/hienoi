#!/usr/bin/env python

"""Particles orbiting around the origin.

Features:

- user attributes: particles are initialized within a radius from the
  origin and are, at each simulation step, updated to orbit around the origin.
- NumPy: operations are done directly on the particle data for increased
  performances.
"""

import math
import os
import sys

import numpy

_HERE = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(_HERE, os.pardir)))

import hienoi.application
from hienoi import Vector2f, Vector4f


# Mass of the central object around which particles are orbiting.
_CENTRAL_MASS = 50.0
# Number of particles.
_COUNT = 1000
# Minimum radius of the disc used to distribute the particles.
_MIN_RADIUS = 2.0
# Maximum radius of the disc used to distribute the particles.
_MAX_RADIUS = 30.0
# Mass of each particle.
_MASS = 2.0
# Mass variance for each particle.
_MASS_VARIANCE = 1.0
# Size of a particle, relative to its mass.
_SIZE = 0.2
# Squared distance to the origin where particles are drawn in the 'far color'.
_FAR_SQUARED_DISTANCE = 500.0
# Color to use for far particles.
_FAR_COLOR = Vector4f(0.0, 1.0, 1.0, 1.0)
# Color to use for near particles.
_NEAR_COLOR = Vector4f(1.0, 0.0, 0.0, 1.0)


def initialize_particle_simulation(sim):
    """Callback to initialize the particle simulation state.

    Parameters
    ----------
    sim : hienoi.dynamics.ParticleSimulation
        Particle simulation.
    """
    numpy.random.seed(_COUNT + 611)

    # Add a few particles at random positions within a given radius and with
    # initial velocities suitable for elliptical orbiting.
    particles = sim.add_particles(_COUNT)
    data = particles.data

    r = numpy.random.uniform(low=_MIN_RADIUS, high=_MAX_RADIUS, size=_COUNT)
    t = numpy.random.uniform(high=2.0 * numpy.pi, size=_COUNT)

    data['position'][:, 0] = r * numpy.cos(t)
    data['position'][:, 1] = r * numpy.sin(t)

    data['mass'] = numpy.random.uniform(low=_MASS - _MASS_VARIANCE,
                                        high=_MASS + _MASS_VARIANCE,
                                        size=_COUNT)

    speeds = numpy.sqrt(data['mass'] / r)
    data['velocity'][:, 0] = data['position'][:, 1] * speeds
    data['velocity'][:, 1] = -data['position'][:, 0] * speeds

    data['size'] = data['mass'] * _SIZE / _MASS


def update_particle_simulation(sim):
    """Callback to update the particle simulation state.

    Parameters
    ----------
    sim : hienoi.dynamics.ParticleSimulation
        Particle simulation.
    """
    data = sim.particles.data
    squared_distances = numpy.sum(data['position'][numpy.newaxis, :] ** 2,
                                  axis=-1)
    squared_distances = squared_distances.reshape(-1, 1)

    data['force'] -= (data['position']
                      * _CENTRAL_MASS
                      * data['mass'][:, numpy.newaxis]
                      / squared_distances)

    data['color'] = (_FAR_COLOR - _NEAR_COLOR)
    data['color'] *= squared_distances / _FAR_SQUARED_DISTANCE
    data['color'] += _NEAR_COLOR


def run():
    """Run the application."""
    return hienoi.application.run(
        gui = {
            'window_title': 'orbit',
            'show_grid': False,
        },
        particle_simulation={
            'initialize_callback': initialize_particle_simulation,
            'postsolve_callback': update_particle_simulation,
        })


if __name__ == '__main__':
    sys.exit(run())
