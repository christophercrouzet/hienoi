#!/usr/bin/env python

import os
import sys
import unittest

_HERE = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(_HERE, os.pardir)))

import hienoi._nani
from hienoi._numeric import Float32


_PY2 = sys.version_info[0] == 2


class NaniTest(unittest.TestCase):

    def test_basics(self):
        data_type = hienoi._nani.Bool(default=True)
        self.assertIsNotNone(hienoi._nani.resolve(data_type))

        data_type = hienoi._nani.Object(default=[])
        self.assertIsNotNone(hienoi._nani.resolve(data_type))

        data_type = hienoi._nani.Number(type=Float32, default=1.23)
        self.assertIsNotNone(hienoi._nani.resolve(data_type))

        if _PY2:
            data_type = hienoi._nani.String(length=8, default='abc')
            self.assertIsNotNone(hienoi._nani.resolve(data_type))
        else:
            data_type = hienoi._nani.Unicode(length=8, default='abc')
            self.assertIsNotNone(hienoi._nani.resolve(data_type))

        data_type = hienoi._nani.String(length=8, default=b'abc')
        self.assertIsNotNone(hienoi._nani.resolve(data_type))

        data_type = hienoi._nani.Unicode(length=8, default=u'abc')
        self.assertIsNotNone(hienoi._nani.resolve(data_type))

        data_type = hienoi._nani.Array(element_type=hienoi._nani.Number(), shape=1)
        self.assertIsNotNone(hienoi._nani.resolve(data_type))

        data_type = hienoi._nani.Structure(
            fields=(
                ('number', hienoi._nani.Number()),
            )
        )
        self.assertIsNotNone(hienoi._nani.resolve(data_type))


if __name__ == '__main__':
    from tests.run import run
    run('__main__')
