"""OpenGL renderer."""

import collections
import ctypes
import itertools
import math
import operator
import os
import sys

import numpy
import OpenGL
import OpenGL.GL as gl

import hienoi._common
import hienoi._numeric
from hienoi._common import GraphicsAPI, GLProfile, ParticleDisplay
from hienoi._vectors import Vector2f


if sys.version_info[0] == 2:
    def _accumulate(iterable, function=operator.add):
        iterator = iter(iterable)
        try:
            total = next(iterator)
        except StopIteration:
            return

        yield total
        for element in iterator:
            total = function(total, element)
            yield total
else:
    _accumulate = itertools.accumulate


OpenGL.ERROR_CHECKING = False
OpenGL.ERROR_ON_COPY = True


class VertexLayout(object):
    """Enumerator for the OpenGL vertex layouts.

    Attributes
    ----------
    INTERLEAVED
    PACKED
    """

    INTERLEAVED = 0
    PACKED = 1


_VertexFormat = collections.namedtuple(
    '_VertexFormat', (
        'vao',
        'vbo',
        'attributes',
        'size',
        'dtype',
    ))


_VertexAttribute = collections.namedtuple(
    '_VertexAttribute', (
        'name',
        'location',
        'count',
        'type',
        'size',
        'normalized',
        'divisor',
    ))


_Info = collections.namedtuple(
    'Info', (
        'api',
        'major_version',
        'minor_version',
        'profile',
    ))


class Info(_Info):
    """Renderer info.

    Attributes
    ----------
    api : int
        Graphics API. It is set to :attr:`GraphicsAPI.OPENGL`.
    major_version : int
        Major version.
    minor_version : int
        Minor version.
    profile : int
        Context profile. Available values are enumerated in the
        :class:`GLProfile` class.
    """

    __slots__ = ()


_INFO = Info(
    api=GraphicsAPI.OPENGL,
    major_version=3,
    minor_version=3,
    profile=GLProfile.CORE)

_BUFFERS = (
    {
        'type': 'vao',
        'names': ('dummy', 'particles', 'point_particles'),
    },
    {
        'type': 'vbo',
        'names': ('particles',),
    },
)

_PROGRAMS = (
    {
        'name': 'grid',
        'shaders': (
            {
                'type': gl.GL_VERTEX_SHADER,
                'filepath': 'shaders/grid.vert',
            },
            {
                'type': gl.GL_FRAGMENT_SHADER,
                'filepath': 'shaders/grid.frag',
            },
        ),
    },
    {
        'name': 'particles',
        'shaders': (
            {
                'type': gl.GL_VERTEX_SHADER,
                'filepath': 'shaders/particles.vert',
            },
            {
                'type': gl.GL_FRAGMENT_SHADER,
                'filepath': 'shaders/particles.frag',
            },
        ),
    },
    {
        'name': 'point_particles',
        'shaders': (
            {
                'type': gl.GL_VERTEX_SHADER,
                'filepath': 'shaders/point_particles.vert',
            },
            {
                'type': gl.GL_FRAGMENT_SHADER,
                'filepath': 'shaders/point_particles.frag',
            },
        ),
    },
)

_UNIFORMS = (
    {
        'program': 'grid',
        'names': ('origin', 'unit', 'color', 'origin_color'),
    },
    {
        'program': 'particles',
        'names': ('projection', 'half_edge_feather', 'half_stroke_width',
                  'fill',),
    },
    {
        'program': 'point_particles',
        'names': ('projection',),
    },
)

_VERTEX_FORMATS = (
    {
        'name': 'particle',
        'vao': 'particles',
        'vbo': 'particles',
        'attributes': (
            {
                'name': 'position',
                'location': 0,
                'count': hienoi._common.PARTICLE_ATTRS.position.count,
                'type': hienoi._numeric.to_gl(
                    hienoi._common.PARTICLE_ATTRS.position.element_type),
                'normalized': gl.GL_FALSE,
                'divisor': 1,
            },
            {
                'name': 'size',
                'location': 1,
                'count': hienoi._common.PARTICLE_ATTRS.size.count,
                'type': hienoi._numeric.to_gl(
                    hienoi._common.PARTICLE_ATTRS.size.element_type),
                'normalized': gl.GL_FALSE,
                'divisor': 1,
            },
            {
                'name': 'color',
                'location': 2,
                'count': hienoi._common.PARTICLE_ATTRS.color.count,
                'type': hienoi._numeric.to_gl(
                    hienoi._common.PARTICLE_ATTRS.color.element_type),
                'normalized': gl.GL_FALSE,
                'divisor': 1,
            },
        ),
    },
    {
        'name': 'point_particle',
        'vao': 'point_particles',
        'vbo': 'particles',
        'attributes': (
            {
                'name': 'position',
                'location': 0,
                'count': hienoi._common.PARTICLE_ATTRS.position.count,
                'type': hienoi._numeric.to_gl(
                    hienoi._common.PARTICLE_ATTRS.position.element_type),
                'normalized': gl.GL_FALSE,
            },
            {
                'name': 'color',
                'location': 1,
                'count': hienoi._common.PARTICLE_ATTRS.color.count,
                'type': hienoi._numeric.to_gl(
                    hienoi._common.PARTICLE_ATTRS.color.element_type),
                'normalized': gl.GL_FALSE,
            },
        ),
    },
)


_State = collections.namedtuple(
    'State', (
        'window_size',
        'view_position',
        'view_zoom',
        'origin',
        'initial_view_aperture_x',
        'view_aperture',
        'grid_density',
        'grid_adaptive_threshold',
        'background_color',
        'grid_color',
        'grid_origin_color',
        'show_grid',
        'particle_display',
        'point_size',
        'edge_feather',
        'stroke_width',
    ))


class State(_State):
    """Renderer state.

    Attributes
    ----------
    window_size : hienoi.Vector2i
        Size of the window.
    view_position : hienoi.Vector2f
        Position of the view (camera).
    view_zoom : float
        Current zoom value for the view.
    origin : hienoi.Vector2f
        Origin in screen coordinates.
    initial_view_aperture_x : float
        Initial length in world units to be shown on the X axis.
    view_aperture : hienoi.Vector2f
        Area in world units covered by the view.
    grid_density : float
        Density of the grid.
        A density of 10.0 means that there are around 10 grid divisions
        displayed on the X axis. A grid division unit represents a fixed length
        in world units, meaning that the actual grid density changes depending
        on the view's zoom.
    grid_adaptive_threshold : float
        Threshold at which the grid division level is readjusted.
        A ratio of 2.0 means that the upper bound of a division level is
        2 times more dense that its lower bound. The division level is
        updated when the grid density reaches either end of this range.
    background_color : hienoi.Vector4f
        Color for the background.
    grid_color : hienoi.Vector4f
        Color for the grid.
    grid_origin_color : hienoi.Vector4f
        Color for the origin axis of the grid.
    show_grid : bool
        True to show the grid.
    particle_display : int
        Display mode for the particles. Available values are enumerated in the
        :class:`~hienoi.ParticleDisplay` class.
    point_size : int
        Size of the particles in pixels when the display mode is set to
        :attr:`~hienoi.ParticleDisplay.POINT`.
    edge_feather : float
        Feather fall-off in pixels to apply to objects drawn with displays such
        as :attr:`~hienoi.ParticleDisplay.CIRCLE` or
        :attr:`~hienoi.ParticleDisplay.DISC`.
    stroke_width : float
        Width of the stroke in pixels to apply to objects drawn with displays
        such as  :attr:`~hienoi.ParticleDisplay.CIRCLE`.
    """

    __slots__ = ()


_SceneState = collections.namedtuple(
    'SceneState', (
        'time',
        'particles',
    ))


class SceneState(_SceneState):
    """Scene state.

    Attributes
    ----------
    time : float
        Time.
    particles : numpy.ndarray
        Particles.
    """

    __slots__ = ()

    @property
    def lower_bounds(self):
        return Vector2f(*numpy.amin(self.particles['position'], axis=0))

    @property
    def upper_bounds(self):
        return Vector2f(*numpy.amax(self.particles['position'], axis=0))


_Pixels = collections.namedtuple(
    'Pixels', (
        'data',
        'width',
        'height',
    ))


class Pixels(_Pixels):
    """Pixels data.

    Attributes
    ----------
    data : str
        Data as an unsigned byte string.
    width : int
        Width of the pixel rectangle.
    height : int
        Heght of the pixel rectangle.
    """

    __slots__ = ()


class Renderer(object):
    """Renderer.

    Parameters
    ----------
    vertex_layout : int
        OpenGL vertex layout. Available values are enumerated in the
        :class:`VertexLayout` class.
    """

    def __init__(self,
                 vertex_layout=VertexLayout.INTERLEAVED):
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        self._bufs = _generate_buffers(_BUFFERS)
        self._programs = _create_programs(_PROGRAMS)
        self._uniforms = _get_uniform_locations(_UNIFORMS, self._programs)
        self._vertex_formats = _get_vertex_formats(_VERTEX_FORMATS, self._bufs)

        self._vbo_capacities = {vbo: 0 for vbo in self._bufs.vbo}
        self._vertex_layout = vertex_layout

        for vertex_format in self._vertex_formats:
            _set_vertex_attributes(vertex_format, self._vertex_layout, 0)

    def render(self, state, scene_state):
        """Render a new frame.

        Parameters
        ----------
        state : hienoi.renderer.State
            Renderer state.
        scene_state : hienoi.renderer.SceneState
            Scene state.
        """
        gl.glClearColor(*state.background_color)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        if state.show_grid:
            self._draw_grid(state)

        projection = _get_projection_matrix(
            state.window_size, state.view_position, state.view_zoom,
            state.view_aperture, state.initial_view_aperture_x)
        self._draw_particles(scene_state.particles, projection, state)

    def resize(self, width, height):
        """Resize the OpenGL viewport.

        Parameters
        ----------
        width : int
            Width.
        height : int
            Height.
        """
        gl.glViewport(0, 0, width, height)

    def cleanup(self):
        """Cleanup the OpenGL resources."""
        for program in self._programs:
            gl.glDeleteProgram(program)

        gl.glDeleteBuffers(len(self._bufs.vbo), self._bufs.vbo)
        gl.glDeleteBuffers(len(self._bufs.vao), self._bufs.vao)

    def read_pixels(self):
        """Read the pixels from the buffer.

        Returns
        -------
        hienoi.renderer.Pixels
            Pixels data.
        """
        _, _, width, height = gl.glGetIntegerv(gl.GL_VIEWPORT)
        data = gl.glReadPixels(0, 0,
                               width, height,
                               gl.GL_RGBA, gl.GL_UNSIGNED_BYTE)
        return Pixels(data=data,
                      width=int(width),
                      height=int(height))

    def _draw_grid(self, state):
        """Draw the grid."""
        unit = _get_screen_space_grid_unit(state)

        # The grid drawing logic mostly happens in the fragment shader, on a
        # billboard of the size of the screen. The billboard is generated by
        # sending 4 vertices to the vertex shader which then sets their
        # position. Since no vertex attributes are required, no VBOs are
        # passed, and only a dummy (empty) VAO is being used.
        gl.glUseProgram(self._programs.grid)
        gl.glBindVertexArray(self._bufs.vao.dummy)
        gl.glUniform2i(self._uniforms.grid.origin,
                       state.origin.x, state.window_size.y - state.origin.y)
        gl.glUniform1f(self._uniforms.grid.unit, unit)
        gl.glUniform4f(self._uniforms.grid.color, *state.grid_color)
        gl.glUniform4f(self._uniforms.grid.origin_color,
                       *state.grid_origin_color)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)

    def _draw_particles(self, particles, projection, state):
        """Draw the particles."""
        particle_count = len(particles)
        if state.particle_display == ParticleDisplay.POINT:
            program = self._programs.point_particles
            vao = self._bufs.vao.point_particles
            vbo = self._bufs.vbo.particles
            uniforms = self._uniforms.point_particles
            vertex_format = self._vertex_formats.point_particle
        else:
            program = self._programs.particles
            vao = self._bufs.vao.particles
            vbo = self._bufs.vbo.particles
            uniforms = self._uniforms.particles
            vertex_format = self._vertex_formats.particle

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
        vbo_capacity = self._vbo_capacities[vbo]

        size = vertex_format.size * particle_count
        if size > vbo_capacity:
            vbo_capacity = _grow_capacity(size, vbo_capacity, 2.0)
            self._reserve_vbo(vbo_capacity)
            self._vbo_capacities[vbo] = vbo_capacity

        if self._vertex_layout == VertexLayout.INTERLEAVED:
            vertex_data = numpy.ascontiguousarray(
                _view_array_fields(
                    particles,
                    *(attr.name for attr in vertex_format.attributes)),
                dtype=vertex_format.dtype)
            gl.glBufferSubData(gl.GL_ARRAY_BUFFER, 0, size, vertex_data)
        elif self._vertex_layout == VertexLayout.PACKED:
            vertex_capacity = int(vbo_capacity / vertex_format.size)
            offset = 0
            for attr in vertex_format.attributes:
                vertex_data = particles[attr.name]
                gl.glBufferSubData(gl.GL_ARRAY_BUFFER, offset,
                                   attr.size * particle_count,
                                   vertex_data)
                offset += attr.size * vertex_capacity

        gl.glUseProgram(program)
        gl.glBindVertexArray(vao)
        gl.glUniformMatrix4fv(uniforms.projection, 1, gl.GL_FALSE, projection)

        if state.particle_display == ParticleDisplay.POINT:
            gl.glPointSize(state.point_size)
            gl.glDrawArrays(gl.GL_POINTS, 0, particle_count)
        else:
            # The particles could have be drawn using `GL_POINTS` and
            # `gl_PointCoord` from the fragment shader but the point size limit
            # imposed by the GL implementations can be rather small for our
            # needs. Also some implementations cause clipping as soon as the
            # centre of the point exits the rendering area, without considering
            # its size. Instead, a billboard is generated by sending 4 vertices
            # for each particle with their position defined in the vertex
            # shader.
            pixel_size = state.view_aperture.x / state.window_size.x
            gl.glUniform1f(uniforms.half_edge_feather,
                           state.edge_feather * 0.5 * pixel_size)
            gl.glUniform1f(uniforms.half_stroke_width,
                           state.stroke_width * 0.5 * pixel_size)
            gl.glUniform1i(uniforms.fill,
                           state.particle_display == ParticleDisplay.DISC)
            if particle_count > 0:
                gl.glDrawArraysInstanced(gl.GL_TRIANGLE_STRIP, 0, 4,
                                         particle_count)

    def _reserve_vbo(self, capacity):
        """Increase the capacity of the OpenGL VBO buffer currently bound."""
        gl.glBufferData(gl.GL_ARRAY_BUFFER, capacity, None, gl.GL_DYNAMIC_DRAW)
        if self._vertex_layout == VertexLayout.PACKED:
            # The vertex attribute offsets need to be recomputed whenever a VBO
            # with a packed layout is resized.
            for vertex_format in self._vertex_formats:
                vertex_capacity = int(capacity / vertex_format.size)
                _set_vertex_attributes(vertex_format, VertexLayout.PACKED,
                                       vertex_capacity)


def get_info():
    """Retrieve some information about the renderer.

    Returns
    -------
    hienoi.renderer.Info
        The renderer information.
    """
    return _INFO


def _generate_buffers(bufs_data):
    """Generate the OpenGL buffers."""
    bufs = {}
    for buf_data in bufs_data:
        buf_type = buf_data['type']
        buf_names = buf_data['names']
        if buf_type == 'vao':
            gen_function = gl.glGenVertexArrays
            struct = collections.namedtuple('_Buffers_vao', buf_names)
        elif buf_type == 'vbo':
            gen_function = gl.glGenBuffers
            struct = collections.namedtuple('_Buffers_vbo', buf_names)

        count = len(buf_names)
        if count == 1:
            bufs[buf_type] = struct(gen_function(1))
        elif count > 1:
            bufs[buf_type] = struct(*gen_function(count))
        else:
            bufs[buf_type] = struct()

    struct = collections.namedtuple('_Buffers', bufs.keys())
    return struct(**bufs)


def _create_programs(programs_data):
    """Create the OpenGL programs."""
    programs = {}
    for program_data in programs_data:
        program = gl.glCreateProgram()

        shaders = []
        shaders_data = program_data['shaders']
        for shader_data in shaders_data:
            shader = _create_shader_from_file(shader_data['filepath'],
                                              shader_data['type'])
            gl.glAttachShader(program, shader)
            shaders.append(shader)

        gl.glLinkProgram(program)
        if gl.glGetProgramiv(program, gl.GL_LINK_STATUS) != gl.GL_TRUE:
            raise RuntimeError(gl.glGetProgramInfoLog(program).decode())

        for shader in shaders:
            gl.glDeleteShader(shader)

        program_name = program_data['name']
        programs[program_name] = program

    struct = collections.namedtuple('_Programs', programs.keys())
    return struct(**programs)


def _get_uniform_locations(uniforms_data, programs):
    """Retrieve the OpenGL uniform locations for the specified programs."""
    uniforms = {}
    for uniform_data in uniforms_data:
        program_name = uniform_data['program']
        program = getattr(programs, program_name, None)
        if program is None:
            raise RuntimeError("No program with the name '%s' was defined."
                               % program_name)

        uniform_names = uniform_data['names']

        program_uniforms = {}
        for uniform_name in uniform_names:
            location = gl.glGetUniformLocation(program, uniform_name)
            program_uniforms[uniform_name] = location

        struct = collections.namedtuple('_Uniforms_%s' % program_name,
                                        uniform_names)
        uniforms[program_name] = struct(**program_uniforms)

    struct = collections.namedtuple('_Uniforms', uniforms.keys())
    return struct(**uniforms)


def _get_vertex_formats(vertex_formats_data, bufs):
    """Retrieve the OpenGL vertex formats."""
    def get_gl_type_size(gl_type):
        return hienoi._numeric.get_type_size(hienoi._numeric.from_gl(gl_type))

    def gl_to_numpy_type(gl_type):
        return hienoi._numeric.to_numpy(hienoi._numeric.from_gl(gl_type))

    formats = {}
    for vertex_format_data in vertex_formats_data:
        vertex_format_name = vertex_format_data['name']
        attrs = tuple(
            _VertexAttribute(
                name=attr['name'],
                location=attr['location'],
                count=attr['count'],
                type=attr['type'],
                size=get_gl_type_size(attr['type']) * attr['count'],
                normalized=attr['normalized'],
                divisor=attr.get('divisor', 0))
            for attr in vertex_format_data['attributes'])
        dtype = numpy.dtype([
            (attr['name'], (gl_to_numpy_type(attr['type']), attr['count']))
            for attr in vertex_format_data['attributes']])
        formats[vertex_format_name] = _VertexFormat(
            vao=getattr(bufs.vao, vertex_format_data['vao']),
            vbo=getattr(bufs.vbo, vertex_format_data['vbo']),
            attributes=attrs,
            size=sum(attr.size for attr in attrs),
            dtype=dtype)

    struct = collections.namedtuple('_VertexFormats', formats.keys())
    return struct(**formats)


def _set_vertex_attributes(vertex_format, layout, vbo_vertex_capacity):
    """Set the OpenGL vertex attributes."""
    gl.glBindVertexArray(vertex_format.vao)
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vertex_format.vbo)

    if layout == VertexLayout.INTERLEAVED:
        stride = sum(attr.size for attr in vertex_format.attributes)
        offsets = [0] + list(_accumulate([
            attr.size for attr in vertex_format.attributes[:-1]]))
    elif layout == VertexLayout.PACKED:
        stride = 0
        offsets = [0] + list(_accumulate([
            attr.size * vbo_vertex_capacity
            for attr in vertex_format.attributes[:-1]]))

    for i, attr in enumerate(vertex_format.attributes):
        gl.glEnableVertexAttribArray(attr.location)
        gl.glVertexAttribPointer(
            attr.location, attr.count, attr.type,
            attr.normalized, stride, ctypes.c_voidp(offsets[i]))
        gl.glVertexAttribDivisor(attr.location, attr.divisor)


def _create_shader_from_file(filepath, shader_type):
    """Create an OpenGL shader from a file."""
    here = os.path.abspath(os.path.dirname(__file__))
    filepath = os.path.abspath(os.path.join(here, filepath))
    with open(filepath, 'r') as shader_file:
        shader = gl.glCreateShader(shader_type)
        gl.glShaderSource(shader, shader_file.read())
        gl.glCompileShader(shader)
        if gl.glGetShaderiv(shader, gl.GL_COMPILE_STATUS) != gl.GL_TRUE:
            raise RuntimeError(gl.glGetShaderInfoLog(shader).decode())

        return shader

    return 0


def _get_projection_matrix(window_size, view_position, view_zoom,
                           view_aperture, initial_view_aperture_x):
    """Retrieve the projection matrix."""
    scale = 2.0 * view_zoom / initial_view_aperture_x
    return (ctypes.c_float * 16)(
        scale,
        0.0,
        0.0,
        0.0,

        0.0,
        scale * window_size.x / window_size.y,
        0.0,
        0.0,

        0.0,
        0.0,
        1.0,
        0.0,

        -2.0 * view_position.x / view_aperture.x,
        -2.0 * view_position.y / view_aperture.y,
        0.0,
        1.0)


def _get_screen_space_grid_unit(state):
    """Retrieve the unit of length of the grid in screen space."""
    level = pow(state.grid_adaptive_threshold,
                math.floor(0.5 + math.log(state.view_zoom,
                                          state.grid_adaptive_threshold)))
    return (state.window_size.x * state.view_zoom
            / (level * state.grid_density))


def _grow_capacity(requested, current, grow_factor):
    """Recommended a new capacity value for when a buffer needs to grow."""
    return max(requested,
               int(max(current * grow_factor,
                       math.ceil(1.0 / (grow_factor - 1.0)) * 2)))


def _view_array_fields(array, *fields):
    """View the fields data from a NumPy array."""
    return array.getfield(numpy.dtype(
        {field: array.dtype.fields[field] for field in fields}))
