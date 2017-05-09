#!/usr/bin/env python

import argparse
import bisect
import collections
import os
import sys
import timeit
import unittest


_clock = timeit.default_timer


# Usage's syntax based on docopt.
_USAGE = "%(prog)s [<name>...]"
_DESCRIPTION = (
    "Runs the benchmarks that have their name containing either one of the "
    "'name' arguments passed. If no 'name' argument is passed, all the "
    "benchmarks are run."
)


# Enumerator for the internal messages.
_MESSAGE_SUITE_SETUP = 0
_MESSAGE_SUITE_TEARDOWN = 1


_Message = collections.namedtuple(
    '_Message', (
        'type',
        'value',
    )
)


class DummyResult(object):

    def wasSuccessful(self):
        return True


class BenchLoader(unittest.TestLoader):
    testMethodPrefix = 'bench'


class BenchRunner(object):

    def run(self, bench):
        stack = collections.deque((bench,))
        while stack:
            obj = stack.popleft()
            if isinstance(obj, _Message):
                if obj.type == _MESSAGE_SUITE_SETUP:
                    obj.value.setUpClass()
                elif obj.type == _MESSAGE_SUITE_TEARDOWN:
                    obj.value.tearDownClass()
            elif isinstance(obj, unittest.TestSuite):
                suites = [suite for suite in obj
                          if isinstance(suite, unittest.TestSuite)]
                cases = [case for case in obj
                         if not isinstance(case, unittest.TestSuite)]

                stack.extend(suites)

                seen = set()
                classes = [type(case) for case in cases
                           if type(case) not in seen
                           and seen.add(type(case)) is None]
                for cls in classes:
                    stack.append(_Message(type=_MESSAGE_SUITE_SETUP,
                                          value=cls))
                    stack.extend(case for case in cases
                                 if type(case) is cls)
                    stack.append(_Message(type=_MESSAGE_SUITE_TEARDOWN,
                                          value=cls))
            else:
                function = getattr(obj, _get_bench_name(obj))

                obj.setUp()
                start = _clock()
                elapsed = function()
                elapsed = _clock() - start if elapsed is None else elapsed
                obj.tearDown()

                elapsed, unit = _pick_time_unit(elapsed)
                print("%s (%s.%s) ... %.3f %s"
                      % (_get_bench_name(obj), type(obj).__module__,
                         type(obj).__name__, elapsed, unit))

        return DummyResult()


def _pick_time_unit(value):
    bounds = (1e-9, 1e-6, 1e-3)
    units = 'num'
    if value >= 1.0:
        out = (value, 's')
    elif value <= bounds[0] * 1e-3:
        out = (0.0, '%ss' % (units[0],))
    else:
        i = max(0, bisect.bisect(bounds, value) - 1)
        out = (value / bounds[i], '%ss' % (units[i],))

    return out


def _find_benchs(path, selectors=None):
    if selectors is None:
        def filter(bench):
            return True
    else:
        def filter(bench):
            return any(selector in _get_bench_full_name(bench)
                       for selector in selectors)

    out = []
    loader = BenchLoader()
    if path == '__main__':
        root_bench = loader.loadTestsFromModule(sys.modules[path])
    else:
        root_bench = loader.discover(path, pattern='bench*.py')

    stack = collections.deque((root_bench,))
    while stack:
        obj = stack.popleft()
        if isinstance(obj, unittest.TestSuite):
            stack.extend(bench for bench in obj)
        elif type(obj).__name__ == 'ModuleImportFailure':
            try:
                # This should always throw an ImportError exception.
                getattr(obj, _get_bench_name(obj))()
            except ImportError as e:
                sys.exit(e.message.strip())
        elif filter(obj):
            out.append(obj)

    return out


def _get_bench_name(bench):
    return bench._testMethodName


def _get_bench_full_name(bench):
    return '%s.%s.%s' % (type(bench).__module__, type(bench).__name__,
                         _get_bench_name(bench))


def run(start_path):
    parser = argparse.ArgumentParser(usage=_USAGE, description=_DESCRIPTION)
    parser.add_argument('name', nargs='*',
                        help='partial benchmark names to search')
    args = parser.parse_args()
    selectors = args.name if args.name else None
    benchs = _find_benchs(start_path, selectors)
    suite = BenchLoader().suiteClass(benchs)
    BenchRunner().run(suite)


if __name__ == "__main__":
    run(os.path.abspath(os.path.dirname(__file__)))
