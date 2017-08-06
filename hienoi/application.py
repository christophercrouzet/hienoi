"""Glue for the different parts of the application.

Gets the modules running, connects them together through inter-process
messaging, and orchestrates the whole.
"""

import bisect
import collections
import cProfile
import logging
import multiprocessing
import os
import pstats
import sys
import tempfile
import timeit
import traceback

import hienoi._common
import hienoi.dynamics
import hienoi.gui
import hienoi.renderer
from hienoi._dynamicarray import DynamicArray


if sys.version_info[0] == 2:
    import Queue as queue

    def _iteritems(d, **kwargs):
        return d.iteritems(**kwargs)

    _range = xrange
else:
    import queue

    def _iteritems(d, **kwargs):
        return iter(d.items(**kwargs))

    _range = range


_clock = timeit.default_timer


class LoggingLevel(object):
    """Enumerator for the logging levels.

    Attributes
    ----------
    CRITICAL
    ERROR
    WARNING
    INFO
    DEBUG
    NOTSET
    """

    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    NOTSET = logging.NOTSET


class Status(object):
    """Enumerator for the return status codes.

    Attributes
    ----------
    Success
    Failure
    """

    SUCCESS = 0
    FAILURE = 1


_Configs = collections.namedtuple(
    '_Configs', (
        'application',
        'gui',
        'particle_simulation',
    ))


_InitialSimulationStates = collections.namedtuple(
    '_InitialSimulationStates', (
        'particle',
    ))


_Buffer = collections.namedtuple(
    '_Buffer', (
        'data',
        'metadata',
    ))


_BufferMetadata = collections.namedtuple(
    '_BufferMetadata', (
        'dtype',
    ))


_OnEventData = collections.namedtuple(
    'OnEventData', (
        'callbacks',
    ))


class OnEventData(_OnEventData):
    """Data to pass to the GUI's 'on event' callback.

    Attributes
    ----------
    callbacks : hienoi.application.Callbacks
        Inter-process callbacks.
    """

    __slots__ = ()


_Callbacks = collections.namedtuple(
    'Callbacks', (
        'particle_simulation',
    ))


class Callbacks(_Callbacks):
    """Inter-process callbacks.

    Attributes
    ----------
    particle_simulation : sequence of hienoi.application.Callback
        Callbacks to run just before the method
        :meth:`hienoi.dynamics.ParticleSimulation.step` is called.
    """

    __slots__ = ()

    def __new__(cls):
        base = super(Callbacks, cls)
        return base.__new__(cls, *([] for _ in base._fields))


_Callback = collections.namedtuple(
    'Callback', (
        'function',
        'args',
        'kwargs',
    ))
_Callback.__new__.__defaults__ = (
    None,  # args
    None,  # kwargs
)


class Callback(_Callback):
    """Inter-process callback.

    Attributes
    ----------
    function : function
        Callback function. It needs to declare ``obj``, the object specific to
        the target process' module, as first parameter. Additional parameters
        declared are passed the ``args`` and ``kwargs`` values.
    args : tuple
        Additional positional arguments to pass to the function.
    kwargs : dict
        Additional keyword arguments to pass to the function.
    """

    __slots__ = ()


_Process = collections.namedtuple(
    '_Process', (
        'instance',
        'output_queues',
        'output_pipes',
    ))


# Enumerator for the inter-process messages.
_MESSAGE_ERROR = 0
_MESSAGE_STOP = 1
_MESSAGE_QUIT = 2
_MESSAGE_REQUEST_SIM_UPDATE = 3
_MESSAGE_SIM_UPDATE = 4
_MESSAGE_RUN_CALLBACKS = 5
_MESSAGE__LAST = _MESSAGE_RUN_CALLBACKS


_Message = collections.namedtuple(
    '_Message', (
        'type',
    ))


_ErrorMessage = collections.namedtuple(
    '_ErrorMessage', (
        'type',
        'process_id',
        'process_name',
        'message',
    ))


_SimUpdateMessage = collections.namedtuple(
    '_SimUpdateMessage', (
        'type',
        'time',
    ))


_RunCallbacksMessage = collections.namedtuple(
    '_RunCallbacksMessage', (
        'type',
        'callbacks',
    ))


_MESSAGE_STRUCTS = {
    _MESSAGE_ERROR: _ErrorMessage,
    _MESSAGE_STOP: _Message,
    _MESSAGE_QUIT: _Message,
    _MESSAGE_REQUEST_SIM_UPDATE: _Message,
    _MESSAGE_SIM_UPDATE: _SimUpdateMessage,
    _MESSAGE_RUN_CALLBACKS: _RunCallbacksMessage,
}
assert len(_MESSAGE_STRUCTS) == _MESSAGE__LAST + 1


_Time = collections.namedtuple(
    '_Time', (
        'value',
        'unit',
    ))


def run(application=None, gui=None, particle_simulation=None):
    """Main entry point to get the application running.

    Parameters
    ----------
    application: dict
        Keyword arguments for the configuration of the application:

        - logging_level : :class:`LoggingLevel`
            Logging messages having a lower threshold than the given level are
            ignored.
        - profile : bool
            ``True`` to enable a profiler to monitor the performances of the
            application. Each process is reported separately.
        - time_step : float
            Amount by which all the simulation times are being incremented by
            at each step. The lower the value, the more accurate the
            simulations are, but the more compute-intensive they become. This
            global time step overrides any time step set in the parameter
            ``particle_simulation``.
        - capture : bool
            ``True`` to write a ``.bmp`` snapshot for each frame to the
            destination pointed by ``capture_filename``.
        - capture_filename : str
            Filename of the snapshots to write. The frame number can be defined
            through Python's formatting syntax. For example, the pattern
            ``/destination/directory/{frame:04}.bmp`` outputs filenames with 4
            digits padded with zeroes, such as ``0009.bmp``, ``0085.bmp``, and
            so on. If ``None``, the snapshots are outputted in a temporary
            folder.
        - capture_increment : int
            Capture a snapshot every n-th frame.
    gui : dict
        Keyword arguments for the configuration of the GUI. See the parameters
        for the class :class:`hienoi.gui.GUI`.
    particle_simulation : dict
        Keyword arguments for the configuration of the particle simulation. See
        the parameters for the class
        :class:`hienoi.dynamics.ParticleSimulation`.

    Returns
    -------
    int
        A value of :attr:`Status.SUCCESS` if successful, or
        :attr:`Status.FAILURE` otherwise.
    """
    configs = {
        'application': {
            'logging_level': LoggingLevel.NOTSET,
            'profile': False,
            'time_step': 0.02,
            'capture': False,
            'capture_filename': None,
            'capture_increment': 1,
        },
        'gui': gui,
        'particle_simulation': particle_simulation,
    }
    configs = {key: {} if value is None else value
               for key, value in _iteritems(configs)}
    configs['application'].update({} if application is None else application)
    configs['particle_simulation']['time_step'] = (
        configs['application']['time_step'])
    configs = _Configs(**configs)

    if configs.application['profile']:
        return _run_profiler(_run, configs)

    return _run(configs)


def _run(configs):
    """Implementation for the `run()` function."""
    logger = multiprocessing.log_to_stderr()
    logger.setLevel(configs.application['logging_level'])

    # Messages from the main process to the child ones.
    downwards_queue = multiprocessing.Queue()
    # Messages from the child processes to the main one.
    upwards_queue = multiprocessing.Queue()
    # Messages from the GUI process to the particle simulation one.
    gui_to_psim_pipe = multiprocessing.Pipe(duplex=False)
    # Messages from the particle simulation process to the GUI one.
    psim_to_gui_pipe = multiprocessing.Pipe(duplex=False)

    if (configs.application['capture']
            and configs.application['capture_filename'] is None):
        directory = tempfile.mkdtemp()
        logger.info("Created a temporary directory for the snapshots: %s"
                    % (directory,))
        configs.application['capture_filename'] = os.path.join(
            directory, '{frame:04}.bmp')

    initial_sim_states = _InitialSimulationStates(
        particle=hienoi.dynamics.ParticleSimulation(
            **configs.particle_simulation))

    # The application is spawning child processes which comes with an overhead
    # mostly in the form of extra copies of data states needing to be made and
    # inter-process messaging latency, which may or may not impact the
    # execution speed. Since Hienoi aims at being of educational value,
    # performances implications have been disregarded here in favour of
    # demonstrating a multiprocessing approach.
    processes = (
        _Process(
            instance=_create_process(
                _gui_process, 'gui',
                args=(gui_to_psim_pipe[1], upwards_queue, psim_to_gui_pipe[0],
                      downwards_queue, initial_sim_states, configs),
                kwargs={},
                upwards=upwards_queue,
                profile=configs.application['profile']),
            output_queues=(upwards_queue,),
            output_pipes=(gui_to_psim_pipe[0],)),
        _Process(
            instance=_create_process(
                _particle_simulation_process, 'particle_simulation',
                args=(psim_to_gui_pipe[1], gui_to_psim_pipe[0],
                      downwards_queue, initial_sim_states, configs),
                kwargs={},
                upwards=upwards_queue,
                profile=configs.application['profile']),
            output_queues=(upwards_queue,),
            output_pipes=(psim_to_gui_pipe[0],)),
    )

    try:
        for process in processes:
            process.instance.start()

        return_code = _main_process(logger, downwards_queue, upwards_queue,
                                    len(processes), configs)
    finally:
        for process in processes:
            while process.instance.is_alive():
                # Any data pushed into the queues by a child process needs
                # to be flushed before being able to join that process.
                for q in process.output_queues:
                    _flush_queue(q)

                # Sometimes pipes also need to be flushed to unblock a process
                # that started sending a large chunk a data to another process
                # that has stopped in the meantime.
                for c in process.output_pipes:
                    _flush_pipe(c)

            if process.instance.pid != None:
                process.instance.join()

    return return_code


def _main_process(logger, downwards, upwards, process_count, configs):
    """Main process."""
    try:
        while True:
            message = _receive_message(upwards, block=True)
            if message.type == _MESSAGE_ERROR:
                logger.error("Process '%s' [%d]:\n%s" % (
                    message.process_name, message.process_id, message.message))
                return Status.FAILURE
            elif message.type == _MESSAGE_QUIT:
                break
    finally:
        for _ in _range(process_count):
            _send_message(downwards, _MESSAGE_STOP)

        downwards.close()

    return Status.SUCCESS


def _gui_process(to_psim, upwards, from_psim, downwards, sims, configs):
    """GUI process."""
    gui = None
    try:
        gui = hienoi.gui.GUI(**configs.gui)
        time_step = configs.application['time_step']
        capture = configs.application['capture']
        capture_filename = configs.application['capture_filename']
        capture_increment = configs.application['capture_increment']

        current_state = hienoi.renderer.SceneState(
            time=0.0,
            particles=sims.particle.particles.data)
        del sims

        # Because the initial simulation state is already available, the first
        # partial state is to be assembled at the next time step.
        partial_state = {'time': time_step}
        next_state = None

        request_sim_updates = True
        frame = 0
        render = True
        accumulator = 0.0
        previous_time = 0.0
        elapsed_time = 0.0
        time_start = _clock()
        while True:
            message = _receive_message(downwards)
            if message is None:
                pass
            elif message.type == _MESSAGE_STOP:
                break

            on_event_data = OnEventData(callbacks=Callbacks())
            gui.poll_events(current_state, data=on_event_data)
            if gui.quit:
                _send_message(upwards, _MESSAGE_QUIT)
                break

            if on_event_data.callbacks.particle_simulation:
                _send_message(
                    to_psim, _MESSAGE_RUN_CALLBACKS,
                    callbacks=on_event_data.callbacks.particle_simulation)

            if next_state is None:
                if request_sim_updates:
                    _send_message(to_psim, _MESSAGE_REQUEST_SIM_UPDATE)
                    request_sim_updates = False

                if 'particles' not in partial_state:
                    message = _receive_message(from_psim)
                    if message is None:
                        pass
                    elif message.type == _MESSAGE_SIM_UPDATE:
                        assert (abs(message.time - partial_state['time'])
                                < time_step * 0.1)
                        buf = _receive_buffer(from_psim)
                        particles = _buffer_to_array(buf)
                        partial_state['particles'] = particles.data

            if _is_scene_state_complete(partial_state):
                next_state = hienoi.renderer.SceneState(**partial_state)
                request_sim_updates = True

            accumulator += elapsed_time
            if accumulator >= time_step and next_state is not None:
                current_state = next_state
                partial_state = {'time': current_state.time + time_step}
                next_state = None
                accumulator = 0.0
                render = True

            if render:
                gui.render(current_state)
                if capture and frame % capture_increment == 0:
                    filename = capture_filename.format(frame=frame)
                    gui.write_snapshot(filename)

                frame += 1
                render = False

            current_time = _clock() - time_start
            elapsed_time = current_time - previous_time
            previous_time = current_time
    finally:
        to_psim.close()
        if gui is not None:
            gui.terminate()


def _particle_simulation_process(to_gui, from_gui, downwards, sims, configs):
    """Particle simulation process."""
    try:
        sim = sims.particle
        particles = DynamicArray(0, hienoi._common.PARTICLE_NANI.dtype)
        callbacks = None

        # Step the simulation without sending the initial state over to the
        # GUI process since it already has initialized its own copy.
        step = True
        send = False
        while True:
            message = _receive_message(downwards)
            if message is None:
                pass
            elif message.type == _MESSAGE_STOP:
                break

            while True:
                message = _receive_message(from_gui)
                if message is None:
                    break
                elif message.type == _MESSAGE_REQUEST_SIM_UPDATE:
                    send = True
                elif message.type == _MESSAGE_RUN_CALLBACKS:
                    callbacks = message.callbacks

            if step:
                if callbacks is not None:
                    _run_callbacks(sim, callbacks)
                    sim.consolidate()
                    callbacks = None

                sim.step()
                step = False

            if send:
                _send_message(to_gui, _MESSAGE_SIM_UPDATE, time=sim.time)

                # Copy only the relevant rendering attributes of the simulation
                # state into a contiguous array.
                particles.copy_from(sim.particles.data)

                _send_buffer(to_gui, _array_to_buffer(particles))
                step = True
                send = False
    finally:
        to_gui.close()


def _run_profiler(function, *args, **kwargs):
    """Run a profiler on the specified function."""
    profiler = cProfile.Profile()
    profiler.enable()
    result = function(*args, **kwargs)
    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats('cumtime')
    stats.print_stats()
    return result


def _create_process(target, name, args, kwargs, upwards, profile):
    """Create a new process."""
    process = multiprocessing.Process(
        target=_process_wrapper,
        name=name,
        args=(target, upwards, profile) + args,
        kwargs=kwargs)
    process.daemon = False
    return process


def _process_wrapper(function, upwards, profile, *args, **kwargs):
    """Wrap a process with additional features."""
    try:
        if profile:
            _run_profiler(function, *args, **kwargs)
        else:
            function(*args, **kwargs)
    except Exception:
        process = multiprocessing.current_process()
        info = sys.exc_info()
        exception = traceback.format_exception(
            info[0], info[1], info[2].tb_next)
        _send_message(upwards, _MESSAGE_ERROR,
                      process_id=process.pid,
                      process_name=process.name,
                      message=''.join(exception).rstrip())
    finally:
        upwards.close()


def _is_scene_state_complete(state):
    """Check if a scene state dictionary has a complete definition."""
    return all(field in state for field in hienoi.renderer.SceneState._fields)


def _run_callbacks(obj, callbacks):
    """Run a sequence of inter-process callbacks."""
    for callback in callbacks:
        args = () if callback.args is None else callback.args
        kwargs = {} if callback.kwargs is None else callback.kwargs
        callback.function(obj, *args, **kwargs)


def _buffer_to_array(buf):
    """Unpack a buffer object into an array."""
    return DynamicArray.from_buffer(buf.data, buf.metadata.dtype)


def _array_to_buffer(array):
    """Pack an array into a buffer object."""
    return _Buffer(data=array.data,
                   metadata=_BufferMetadata(dtype=array.dtype))


def _send_message(c, type, **kwargs):
    """Send a message."""
    message = _MESSAGE_STRUCTS[type](type=type, **kwargs)
    if isinstance(c, multiprocessing.queues.Queue):
        c.put(message, block=True)
    else:
        c.send(message)


def _receive_message(c, block=False):
    """Receive a message."""
    if isinstance(c, multiprocessing.queues.Queue):
        try:
            message = c.get(block=block)
        except queue.Empty:
            return None
    else:
        if not block and not c.poll():
            return None

        try:
            message = c.recv()
        except EOFError:
            return None

    return message


def _send_buffer(c, buf):
    """Send a buffer object to a pipe connection."""
    c.send(buf.metadata)
    c.send_bytes(buf.data)


def _receive_buffer(c):
    """Receive a buffer object from a pipe connection."""
    metadata = c.recv()
    data = c.recv_bytes()
    return _Buffer(
        data=data,
        metadata=metadata)


def _flush_queue(q):
    """Flush the content of a queue."""
    try:
        while True:
            q.get(block=False)
    except queue.Empty:
        pass


def _flush_pipe(c):
    """Flush the content of a pipe."""
    try:
        while c.poll():
            c.recv_bytes()
    except EOFError:
        pass


def _pick_time_unit(value):
    """Pick the most readable time unit."""
    bounds = (1e-9, 1e-6, 1e-3)
    units = 'num'
    if value >= 1.0:
        out = _Time(value=value, unit='s')
    elif value <= bounds[0] * 1e-3:
        out = _Time(value=0.0, unit='%ss' % (units[0],))
    else:
        i = max(0, bisect.bisect(bounds, value) - 1)
        out = _Time(value=value / bounds[i], unit='%ss' % (units[i],))

    return out
