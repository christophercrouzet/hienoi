#!/usr/bin/env python

import os
import sys
import unittest

_HERE = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(_HERE, os.pardir)))

import hienoi.dynamics
from hienoi import Vector2f


class ParticleSimulationTest(unittest.TestCase):

    def test_constructor_1(self):
        sim = hienoi.dynamics.ParticleSimulation()
        self.assertEqual(sim.time, 0.0)
        self.assertEqual(sim.last_particle_id, -1)
        self.assertEqual(len(sim.particles), 0)

    def test_constructor_2(self):
        def initialize(sim):
            p0 = sim.add_particle()
            p1 = sim.add_particle()
            p2 = sim.add_particle()
            p1.alive = False

            self.assertEqual(sim.time, 0.0)
            self.assertEqual(sim.last_particle_id, 2)
            self.assertEqual(len(sim.particles), 0)
            self.assertEqual(len(list(iter(sim.particles))), 0)
            self.assertTrue(p0.alive)
            self.assertFalse(p1.alive)
            self.assertTrue(p2.alive)

        sim = hienoi.dynamics.ParticleSimulation(initialize_callback=initialize)
        self.assertEqual(sim.time, 0.0)
        self.assertEqual(sim.last_particle_id, 2)
        self.assertEqual(len(sim.particles), 2)
        self.assertEqual(len(list(iter(sim.particles))), 2)
        for particle in sim.particles:
            self.assertTrue(particle.alive)

    def test_add_particle(self):
        sim = hienoi.dynamics.ParticleSimulation(particle_bucket_buffer_capacity=2)

        p0 = sim.add_particle(size=2.0)
        self.assertEqual(len(sim.particles), 0)
        self.assertEqual(len(list(iter(sim.particles))), 0)
        self.assertEqual(sim.last_particle_id, 0)
        self.assertEqual(p0.id, 0)
        self.assertEqual(p0.size, 2.0)
        self.assertTrue(p0.alive)

        p1 = sim.add_particle(id=99)
        self.assertEqual(len(sim.particles), 0)
        self.assertEqual(len(list(iter(sim.particles))), 0)
        self.assertEqual(sim.last_particle_id, 1)
        self.assertEqual(p1.id, 1)
        self.assertTrue(p1.alive)

        p2 = sim.add_particle()
        self.assertEqual(len(sim.particles), 0)
        self.assertEqual(len(list(iter(sim.particles))), 0)
        self.assertEqual(sim.last_particle_id, 2)
        self.assertEqual(p2.id, 2)
        self.assertTrue(p2.alive)

        sim.consolidate()
        self.assertEqual(len(sim.particles), 3)
        self.assertEqual(len(list(iter(sim.particles))), 3)
        self.assertEqual(sim.last_particle_id, 2)

    def test_add_particles(self):
        sim = hienoi.dynamics.ParticleSimulation(particle_bucket_buffer_capacity=3)

        bunch = sim.add_particles(2)
        self.assertEqual(len(bunch), 2)
        self.assertEqual([particle.id for particle in bunch], [0, 1])
        self.assertEqual(len(sim.particles), 0)
        self.assertEqual(len(list(iter(sim.particles))), 0)
        self.assertEqual(sim.last_particle_id, 1)

        bunch = sim.add_particles(5)
        self.assertEqual(len(bunch), 5)
        self.assertEqual([particle.id for particle in bunch], [2, 3, 4, 5, 6])
        self.assertEqual(len(sim.particles), 0)
        self.assertEqual(len(list(iter(sim.particles))), 0)
        self.assertEqual(sim.last_particle_id, 6)

        sim.consolidate()
        self.assertEqual(len(sim.particles), 7)
        self.assertEqual(len(list(iter(sim.particles))), 7)
        self.assertEqual(sim.last_particle_id, 6)
        self.assertEqual([particle.id for particle in sim.particles], [0, 1, 2, 3, 4, 5, 6])

    def test_kill_particle(self):
        sim = hienoi.dynamics.ParticleSimulation()
        sim.add_particle()
        sim.add_particle()
        sim.consolidate()

        p0 = sim.get_particle(0)
        p1 = sim.get_particle(1)

        p2 = sim.add_particle()
        p3 = sim.add_particle()
        p4 = sim.add_particle()

        p0.alive = False
        p3.alive = False

        self.assertFalse(p0.alive)
        self.assertTrue(p1.alive)
        self.assertTrue(p2.alive)
        self.assertFalse(p3.alive)
        self.assertEqual(len(sim.particles), 2)

        sim.consolidate()
        self.assertEqual(len(sim.particles), 3)
        self.assertEqual([particle.id for particle in sim.particles], [1, 2, 4])

    def test_get_particle(self):
        sim = hienoi.dynamics.ParticleSimulation()

        sim.add_particle()
        sim.add_particle()
        self.assertRaises(ValueError, sim.get_particle, 0)
        self.assertRaises(ValueError, sim.get_particle, 1)

        sim.consolidate()
        sim.add_particle()
        sim.add_particle()
        self.assertEqual(sim.get_particle(0).id, 0)
        self.assertEqual(sim.get_particle(1).id, 1)
        self.assertRaises(ValueError, sim.get_particle, 2)
        self.assertRaises(ValueError, sim.get_particle, 3)

    def test_step(self):
        sim = hienoi.dynamics.ParticleSimulation(time_step=0.5)
        sim.add_particle(force=(1.0, 0.0))
        sim.add_particle(force=(2.0, 0.0))
        sim.consolidate()
        p0 = sim.get_particle(0)
        p1 = sim.get_particle(1)
        p2 = sim.add_particle(force=(3.0, 0.0))

        sim.step()
        self.assertEqual(p0.force, (0.0, 0.0))
        self.assertEqual(p1.force, (0.0, 0.0))
        self.assertEqual(p2.force, (3.0, 0.0))
        self.assertEqual(p0.velocity, (0.5, 0.0))
        self.assertEqual(p1.velocity, (1.0, 0.0))
        self.assertEqual(p2.velocity, (0.0, 0.0))
        self.assertEqual(p0.position, (0.25, 0.0))
        self.assertEqual(p1.position, (0.5, 0.0))
        self.assertEqual(p2.position, (0.0, 0.0))

        sim.step()
        self.assertEqual(p0.force, (0.0, 0.0))
        self.assertEqual(p1.force, (0.0, 0.0))
        self.assertEqual(p2.force, (3.0, 0.0))
        self.assertEqual(p0.velocity, (0.5, 0.0))
        self.assertEqual(p1.velocity, (1.0, 0.0))
        self.assertEqual(p2.velocity, (0.0, 0.0))
        self.assertEqual(p0.position, (0.5, 0.0))
        self.assertEqual(p1.position, (1.0, 0.0))
        self.assertEqual(p2.position, (0.0, 0.0))

    def test_consolidate(self):
        sim = hienoi.dynamics.ParticleSimulation()

        sim.consolidate()
        self.assertEqual(len(sim.particles), 0)
        self.assertEqual([particle.id for particle in sim.particles], [])

        p0 = sim.add_particle()
        p1 = sim.add_particle()
        p2 = sim.add_particle()
        p1.alive = False
        sim.consolidate()
        self.assertEqual(len(sim.particles), 2)
        self.assertEqual([particle.id for particle in sim.particles], [0, 2])

        sim.add_particle()
        sim.consolidate()
        self.assertEqual(len(sim.particles), 3)
        self.assertEqual([particle.id for particle in sim.particles], [0, 2, 3])


if __name__ == '__main__':
    from tests.run import run
    run('__main__')
