#!/usr/bin/env python

"""Emit particles based on the mouse's motion.

Features:

- user attributes: new attributes are defined both globally at the simulation
  level and on each particle to respectively define the properties of the
  emitter and to allow particles to die after a given amount of time.
- GUI event callback: trigger the spawning of new particles whenever the mouse
  is in motion.
- simulation callbacks: initialize the user attributes then, at each simulation
  step, update the particle ages and colors, and spawn new ones as per the GUI
  event callback.
"""

import math
import os
import random
import sys

import sdl2

_HERE = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(_HERE, os.pardir)))

import hienoi.application
from hienoi import Float32, Number, Vector2i, Vector2f, Vector4f
from hienoi.application import Callback


if sys.version_info[0] == 2:
    _range = xrange
else:
    _range = range


# Lifespan of each particle.
_EMITTER_LIFE = 1.0
# Lifespan variance for each particle.
_EMITTER_LIFE_VARIANCE = 0.5
# Strength of the velocity to inherit from the emitter.
_EMITTER_INHERIT_VELOCITY = 0.25
# Strength of the random velocity component.
_EMITTER_RANDOM_VELOCITY = 5.0
# Strength variance for the random velocity component.
_EMITTER_RANDOM_VELOCITY_VARIANCE = 2.5
# Approximate distance between spawn location for long strokes.
_STEP_LENGTH = 0.5
# Velocity needed for particles to be painted in the 'fast color'.
_FAST_VELOCITY = 100.0
# Color to use for fast particles.
_FAST_COLOR = Vector4f(1.0, 1.0, 0.0, 1.0)
# Color to use for slow particles.
_SLOW_COLOR = Vector4f(1.0, 0.0, 0.0, 1.0)


def _rand(seed=None):
    """Generate a pseudo-random number ranging from 0.0 to 1.0."""
    random.seed(seed)
    return random.random()


def _rand_0(seed=None):
    """Generate a pseudo-random number around 0, ranging from -1.0 to 1.0."""
    random.seed(seed)
    return random.random() * 2.0 - 1.0


def _remap_clamped(value, from_1, to_1, from_2, to_2):
    """Remap a value from a range to another.

    If the resulting value is outside the bounds of the target range, then it
    is clamped.
    """
    result = ((value - from_1) / (to_1 - from_1)) * (to_2 - from_2) + from_2
    return sorted((from_2, result, to_2))[1]


def _get_particle_color(velocity, normalized_age):
    """Color to be applied to a particle depending on its speed and age."""
    speed = min(1.0, velocity.length() / _FAST_VELOCITY)
    color = Vector4f.lerp(_SLOW_COLOR, _FAST_COLOR, speed)
    color.iscale(_remap_clamped(normalized_age, 0.0, 1.0, 1.0, 0.5))
    return color


def _set_emitter_position(sim, position):
    """Inter-process callback to set a new emitter position.

    The first parameter of inter-process callbacks is always reserved for
    the object to operate on, here the particle simulation object. Remaining
    parameters are reserved to the user.
    """
    if position is None:
        sim.user_data.emitter_position = None
        sim.user_data.previous_emitter_position = None
        sim.user_data.previous_emitter_velocity = Vector2f(0.0, 0.0)

    sim.user_data.emitter_position = position


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
        # Passing `None` to the `_set_emitter_position` callback resets the
        # emitter states, which is what we need here otherwise we might end up
        # with crazy values coming out of the navigation actions.
        callback = Callback(_set_emitter_position, args=(None,))
        data.callbacks.particle_simulation.append(callback)
    elif event.type == sdl2.SDL_MOUSEMOTION:
        motion_event = event.motion
        mouse_position = Vector2i(motion_event.x, motion_event.y)
        position = gui.screen_to_world(mouse_position)
        callback = Callback(_set_emitter_position, args=(position,))
        data.callbacks.particle_simulation.append(callback)


def initialize_particle_simulation(sim):
    """Callback to initialize the particle simulation state.

    Parameters
    ----------
    sim : hienoi.dynamics.ParticleSimulation
        Particle simulation.
    """
    # Create a new global attribute for the position of the emitter but let's
    # leave it uninitialized until a mouse motion event is recorded.
    sim.user_data.emitter_position = None

    # And a couple more for its previous position and previous velocity.
    sim.user_data.previous_emitter_position = None
    sim.user_data.previous_emitter_velocity = Vector2f(0.0, 0.0)


def update_particle_simulation(sim):
    """Callback to update the particle simulation state.

    Parameters
    ----------
    sim : hienoi.dynamics.ParticleSimulation
        Particle simulation.
    """
    seed = sim.last_particle_id + 0.293

    # By overriding the `particle_attributes` value for the particle simulation
    # in the `run()` function below, each particle comes with extras 'age' and
    # 'life' attributes.

    for particle in sim.particles:
        # At each simulation step, the particles are aged accordingly.
        particle.age += sim.time_step

        if particle.age > particle.life:
            # The particle's age is greater than its lifespan, kill it.
            particle.alive = False
        else:
            particle.color = _get_particle_color(particle.velocity,
                                                 particle.age / particle.life)

    # Source any new particles.
    emitter_position = sim.user_data.emitter_position
    previous_emitter_position = sim.user_data.previous_emitter_position
    previous_emitter_velocity = sim.user_data.previous_emitter_velocity
    if previous_emitter_position is not None:
        # Retrieve the trajectory of the latests emitter positions recorded,
        # which are derived from the mouse motions, then spawn new particles
        # along that trajecotry, with each spawn location being separated from
        # the previous one by a 'step' measure.
        translation = emitter_position - previous_emitter_position
        emitter_velocity = translation.scale(1.0 / sim.time_step)
        distance = translation.length()
        step_count = int(math.ceil(distance / _STEP_LENGTH))
        for i in _range(step_count):
            step = float(i) / step_count

            # The age is relative to the current step position. The further the
            # step is from the latest emitter position, the more the older the
            # particle should be.
            age = step * sim.time_step
            life = (_EMITTER_LIFE
                    + _EMITTER_LIFE_VARIANCE
                    * _rand_0(seed=seed + i + 0.084))

            # A random velocity vector is defined with its length set as per
            # the given constants.
            velocity = Vector2f(_rand_0(seed=seed + i + 0.318),
                                _rand_0(seed=seed + i + 0.702))
            velocity.inormalize()
            velocity.iscale(_EMITTER_RANDOM_VELOCITY
                            + _EMITTER_RANDOM_VELOCITY_VARIANCE
                            * _rand_0(seed=seed + i + 0.775))

            # The final velocity for the particle is computed by adding the
            # velocity of the emitter, blended with its previous velocity
            # depending on the current step, to the random velocity.
            velocity += Vector2f.lerp(
                emitter_velocity, previous_emitter_velocity, step).iscale(
                    _EMITTER_INHERIT_VELOCITY)

            # The particle is spawned at the current step position and is then
            # pushed along its velocity according to its age.
            position = emitter_position + translation.scale(-step)
            position += velocity.scale(age)

            # Initialize each particle's color relatively to its speed and age.
            color = _get_particle_color(velocity, age / life)

            sim.add_particle(position=position,
                             velocity=velocity,
                             age=age,
                             life=life,
                             size=_rand(seed=seed + i + 0.855),
                             color=color)

        sim.user_data.previous_emitter_velocity = emitter_velocity

    sim.user_data.previous_emitter_position = emitter_position


def run():
    """Run the application."""
    return hienoi.application.run(
        gui={
            'window_title': 'trail',
            'show_grid': False,
            'on_event_callback': on_gui_event,
        },
        particle_simulation={
            'particle_attributes': (
                ('age', Number(type=Float32, default=0.0)),
                ('life', Number(type=Float32, default=1.0)),
            ),
            'initialize_callback': initialize_particle_simulation,
            'postsolve_callback': update_particle_simulation,
        })


if __name__ == '__main__':
    sys.exit(run())
