#!/usr/bin/env python

"""Introductory demo showing a basic set-up.

Features:

- simulation callbacks: spawn a single particle then, at each simulation
  step, add a force towards the origin proportional to its distance to it.
"""

import os
import sys

_HERE = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(_HERE, os.pardir)))

import hienoi.application
from hienoi import Vector2f


def initialize_particle_simulation(sim):
    """Callback to initialize the particle simulation state.

    Parameters
    ----------
    sim : hienoi.dynamics.ParticleSimulation
        Particle simulation.
    """
    # Let's add a single particle to the simulation. Since in the `run()`
    # function below we override the applications's configuration attribute
    # `view_aperture` with a value of 80.0, then the view is set to initially
    # show 80 world units in the X axis. By setting the initial X position of
    # the particle to 30.0, it should spawn at the 3/4th location of the
    # screen's right half.
    sim.add_particle(position=Vector2f(30.0, 0.0))


def update_particle_simulation(sim):
    """Callback to update the particle simulation state.

    Parameters
    ----------
    sim : hienoi.dynamics.ParticleSimulation
        Particle simulation.
    """
    # Because this function is passed to the particle simulation's
    # `postsolve_callback`, it runs at the end of each simulation step. As a
    # result, the changes applied here are rendered as-is until the next
    # simulation step. If we'd want to have our changes to the force and
    # velocity attributes to be immediately solved by the integrator then we'd
    # use `presolve_callback` instead.

    # Now let's retrieve the particle created during initialization and apply
    # an attractive force towards the origin to it. But before doing so,
    # reading some explanations provided with the class
    # `hienoi.dynamics.ParticleSimulation` might prove useful.

    # To attract the particle to the origin, we need a force, defined as a 2D
    # vector, that starts at the current particle's position and that is
    # directed towards the origin. An example of such a force is the vector
    # (origin.x - position.x, origin.y - position.y), which can be simplified
    # to (-position.x, -position.y) since the origin has coordinates (0, 0).
    # The vector could be further scaled to increase or decrease its magnitude,
    # thus influencing how fast the particle moves towards its goal.
    particle = sim.particles[0]
    particle.force -= particle.position


def run():
    """Run the application."""
    # Each module in Hienoi provides a configuration object that we can use to
    # hook our code into the framework but also to override default settings
    # such as the simulation's time step.
    return hienoi.application.run(
        gui={
            'window_title': 'intro',
            'view_aperture_x': 80.0,
            'grid_density': 8.0,
        },
        particle_simulation={
            'time_step': 0.01,
            'initialize_callback': initialize_particle_simulation,
            'postsolve_callback': update_particle_simulation,
        })


if __name__ == '__main__':
    sys.exit(run())
