#!/usr/bin/env python

"""Aggregation of particles around the origin.

Features:

- simulation callbacks: particles are initialized within a radius from the
  origin and are, at each simulation step, updated to move towards the origin
  while keeping a separation distance from each other.
- GUI event callback: on each left mouse button click, a new particle is added
  to the simulation under the mouses's location.
- neighbouring: each particle retrieve the neighbours within a radius to keep
  itself separated from the others.
"""

import math
import os
import random
import sys

import sdl2

_HERE = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(_HERE, os.pardir)))

import hienoi
import hienoi.application
from hienoi import Vector2f, Vector4f
from hienoi.application import Callback
from hienoi.gui import NavigationAction


if sys.version_info[0] == 2:
    _range = xrange
else:
    _range = range


# Number of particles.
_COUNT = 8
# Radius of the disc used to distribute the particles.
_RADIUS = 30.0
# Size of a particle.
_SIZE = 1.0
# Strength of the attraction towards the origin.
_ATTRACTION_FORCE = 1.0
# Threshold distance below which a particle starts separating from another.
_SEPARATION_DISTANCE = 5.0
# Strength of the separation force.
_SEPARATION_FORCE = 50.0


def _rand(seed=None):
    """Generate a pseudo-random number ranging from 0.0 to 1.0."""
    random.seed(seed)
    return random.random()


def _rand_0(seed=None):
    """Generate a pseudo-random number around 0, ranging from -1.0 to 1.0."""
    random.seed(seed)
    return random.random() * 2.0 - 1.0


def _remap_clamped(value, from_1, to_1, from_2, to_2):
    """Remap a value from a range to another."""
    result = ((value - from_1) / (to_1 - from_1)) * (to_2 - from_2) + from_2
    return sorted((from_2, result, to_2))[1]


def _add_particle(sim, position):
    """Inter-process callback to add a new particle to the simulation.

    The first parameter of inter-process callbacks is always reserved for
    the object to operate on, here the particle simulation object. Remaining
    parameters are reserved to the user.
    """
    sim.add_particle(position=position, size=_SIZE)


def on_gui_event(gui, data, event):
    """Callback to react to GUI events.

    Parameters
    ----------
    gui : hienoi.gui.GUI
        GUI.
    data : hienoi.application.OnEventData
        Data.
    event : sdl2.SDL_Event
        GUI event.
    """
    if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
        button_event = event.button
        if (button_event.button == sdl2.SDL_BUTTON_LEFT
                and gui.navigation_action == NavigationAction.NONE):
            # Create an 'add_particle' callback to be run by the particle
            # simulation object.
            mouse_position = gui.get_mouse_position()
            position = gui.screen_to_world(mouse_position)
            callback = Callback(_add_particle, args=(position,))
            data.callbacks.particle_simulation.append(callback)


def initialize_particle_simulation(sim):
    """Callback to initialize the particle simulation state.

    Parameters
    ----------
    sim : hienoi.dynamics.ParticleSimulation
        Particle simulation.
    """
    # Add a few particles at random positions within a given radius and with
    # random velocities having a magnitude ranging from -1.0 to 1.0.
    for i in _range(_COUNT):
        r = _rand(seed=i + 0.827) * _RADIUS
        t = _rand(seed=i + 0.301) * 2.0 * math.pi
        sim.add_particle(position=Vector2f(r * math.cos(t), r * math.sin(t)),
                         size=_SIZE)


def update_particle_simulation(sim):
    """Callback to update the particle simulation state.

    Parameters
    ----------
    sim : hienoi.dynamics.ParticleSimulation
        Particle simulation.
    """
    for particle in sim.particles:
        # Compute the attractive force.
        force = -particle.position - particle.velocity
        force.iscale(_ATTRACTION_FORCE)
        particle.force += force

        # Compute the separative force.
        highest_proximity = 0.0
        radius = _SIZE * 2.0 + _SEPARATION_DISTANCE
        squared_radius = radius ** 2
        neighbours = sim.get_neighbour_particles(
            particle.position, count=None, radius=radius)
        for neighbour in neighbours:
            if neighbour.particle.id == particle.id:
                continue

            if neighbour.squared_distance > squared_radius:
                continue

            proximity = _remap_clamped(neighbour.distance,
                                       particle.size, radius,
                                       1.0, 0.0)
            highest_proximity = max(proximity, highest_proximity)

            force = particle.position - neighbour.particle.position
            force.iscale(proximity * _SEPARATION_FORCE)
            particle.force += force

        # Color the particle according to how near it is to any other particle.
        particle.color = Vector4f(1.0,
                                  1.0 - highest_proximity,
                                  1.0 - highest_proximity,
                                  1.0)


def run():
    """Run the application."""
    return hienoi.application.run(
        gui={
            'window_title': 'equilibrium',
            'show_grid': False,
            'on_event_callback': on_gui_event,
        },
        particle_simulation={
            'initialize_callback': initialize_particle_simulation,
            'postsolve_callback': update_particle_simulation,
        })


if __name__ == '__main__':
    sys.exit(run())
