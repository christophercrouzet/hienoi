#!/usr/bin/env python

"""Collision of billard balls.

Implementation of the Ten Minute Physics tutorial number 3.
https://matthias-research.github.io/pages/tenMinutePhysics
"""

import math
import os
import sys

import numpy
import sdl2

_HERE = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(_HERE, os.pardir)))

import hienoi
import hienoi.application
from hienoi import Vector2f, Vector2i, Vector4f
from hienoi.application import Callback


# Initial size of the window.
_INITIAL_WINDOW_SIZE = Vector2i(480, 480)

# Number of particles.
_COUNT = 64
# Size of a particle.
_SIZE = 1.0
# Size variance for each particle.
_SIZE_VARIANCE = 0.5
# Velocity of a particle.
_VELOCITY = 5.0
# Velocity variance for each particle.
_VELOCITY_VARIANCE = 3.0
# Bounce energy.
_RESTITUTION = 1.0


def _compute_initial_canvas_bounds(window_size):
    """Compute the initial canvas bounds from the given windows size."""
    if window_size.x > window_size.y:
        upper_bound = Vector2f(50.0, 50.0 * window_size.y / window_size.x)
    else:
        upper_bound = Vector2f(50.0 * window_size.x / window_size.y, 50.0)

    return (-upper_bound, upper_bound)


def _set_canvas_bounds(sim, canvas_bounds):
    """Inter-process callback to set the bounds of the canvas.

    The first parameter of inter-process callbacks is always reserved for
    the object to operate on, here the particle simulation object. Remaining
    parameters are reserved to the user.
    """
    sim.user_data.canvas_bounds = canvas_bounds


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
    if gui.has_view_changed:
        window_size = gui.get_window_size()
        canvas_bounds = (
            gui.screen_to_world(Vector2i(0, window_size.y)),
            gui.screen_to_world(Vector2i(window_size.x, 0)),
        )
        callback = Callback(_set_canvas_bounds, args=(canvas_bounds,))
        data.callbacks.particle_simulation.append(callback)


def initialize_particle_simulation(sim):
    """Callback to initialize the particle simulation state.

    Parameters
    ----------
    sim : hienoi.dynamics.ParticleSimulation
        Particle simulation.
    """
    sim.user_data.canvas_bounds = _compute_initial_canvas_bounds(
        _INITIAL_WINDOW_SIZE
    )

    numpy.random.seed(_COUNT + 123)

    particles = sim.add_particles(_COUNT)
    data = particles.data

    data['size'] = numpy.random.uniform(
        low=_SIZE - _SIZE_VARIANCE,
        high=_SIZE + _SIZE_VARIANCE,
        size=_COUNT,
    )
    data['mass'] = data['size'] * data['size'] * math.pi
    data['position'][:, 0] = numpy.random.uniform(
        low=sim.user_data.canvas_bounds[0].x,
        high=sim.user_data.canvas_bounds[1].x,
        size=_COUNT,
    )
    data['position'][:, 1] = numpy.random.uniform(
        low=sim.user_data.canvas_bounds[0].y,
        high=sim.user_data.canvas_bounds[1].y,
        size=_COUNT,
    )
    data['velocity'][:, 0] = numpy.random.uniform(
        low=-_VELOCITY - _VELOCITY_VARIANCE,
        high=_VELOCITY + _VELOCITY_VARIANCE,
        size=_COUNT,
    )
    data['velocity'][:, 1] = numpy.random.uniform(
        low=-_VELOCITY - _VELOCITY_VARIANCE,
        high=_VELOCITY + _VELOCITY_VARIANCE,
        size=_COUNT,
    )


def update_particle_simulation(sim):
    """Callback to update the particle simulation state.

    Parameters
    ----------
    sim : hienoi.dynamics.ParticleSimulation
        Particle simulation.
    """
    lower_bounds, upper_bounds = sim.user_data.canvas_bounds

    for particle in sim.particles:
        # If the particle recently collided, it must have been colored red.
        # We want to progressively restore its color back to white.
        particle.color = Vector4f(
            min(particle.color.r + 0.05, 1.0),
            min(particle.color.g + 0.05, 1.0),
            min(particle.color.b + 0.05, 1.0),
            1.0,
        )

        # Bounce the particle if it went beyond the canvas' bounds.

        if particle.position.x < lower_bounds.x + particle.size:
            particle.position.x = lower_bounds.x + particle.size
            particle.velocity.x = -particle.velocity.x

        if particle.position.x > upper_bounds.x - particle.size:
            particle.position.x = upper_bounds.x - particle.size
            particle.velocity.x = -particle.velocity.x

        if particle.position.y < lower_bounds.y + particle.size:
            particle.position.y = lower_bounds.y + particle.size
            particle.velocity.y = -particle.velocity.y

        if particle.position.y > upper_bounds.y - particle.size:
            particle.position.y = upper_bounds.y - particle.size
            particle.velocity.y = -particle.velocity.y

        # Collide with other particles.

        neighbours = sim.get_neighbour_particles(
            particle.position,
            count=None,
            radius=2 * _SIZE + _SIZE_VARIANCE,
        )
        for neighbour in neighbours:
            if neighbour.particle.id == particle.id:
                continue

            if (
                neighbour.squared_distance
                > (particle.size + neighbour.particle.size) ** 2
            ):
                continue

            particle.color = Vector4f(1.0, 0.0, 0.0, 1.0)

            dir = neighbour.particle.position - particle.position
            dir.inormalize()

            corr = (
                (particle.size + neighbour.particle.size - neighbour.distance)
                * 0.5
            )
            particle.position -= dir.scale(corr)
            neighbour.particle.position += dir.scale(corr)

            v1 = particle.velocity.dot(dir)
            v2 = neighbour.particle.velocity.dot(dir)

            m1 = particle.mass
            m2 = neighbour.particle.mass

            new_v1 = (
                (m1 * v1 + m2 * v2 - m2 * (v1 - v2) * _RESTITUTION) / (m1 + m2)
            )
            new_v2 = (
                (m1 * v1 + m2 * v2 - m1 * (v2 - v1) * _RESTITUTION) / (m1 + m2)
            )

            particle.velocity += dir.scale(new_v1 - v1)
            neighbour.particle.velocity += dir.scale(new_v2 - v2)


def run():
    """Run the application."""
    return hienoi.application.run(
        gui={
            'window_title': 'billard',
            'window_size': _INITIAL_WINDOW_SIZE,
            'show_grid': False,
            'on_event_callback': on_gui_event,
        },
        particle_simulation={
            'initialize_callback': initialize_particle_simulation,
            'postsolve_callback': update_particle_simulation,
        })


if __name__ == '__main__':
    sys.exit(run())
