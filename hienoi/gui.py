"""Graphical user interface."""

import collections
import ctypes

import sdl2

import hienoi.renderer
from hienoi._common import GLProfile, GraphicsAPI, ParticleDisplay, UserData
from hienoi._vectors import Vector2i, Vector2f, Vector4f


class NavigationAction(object):
    """Enumerator for the current nagivation action.

    Attributes
    ----------
    NONE
    MOVE
    ZOOM
    """

    NONE = 0
    MOVE = 1
    ZOOM = 2


_Handles = collections.namedtuple(
    '_Handles', (
        'window',
        'renderer',
    ))


_GLHandles = collections.namedtuple(
    '_GLHandles', (
        'context',
    ))


_RGBMasks = collections.namedtuple(
    '_RGBMasks', (
        'red',
        'green',
        'blue',
    ))


_FIT_VIEW_REL_PADDING = 2.0

if sdl2.SDL_BYTEORDER == sdl2.SDL_LIL_ENDIAN:
    _RGB_MASKS = _RGBMasks(red=0x000000FF, green=0x0000FF00, blue=0x00FF0000)
else:
    _RGB_MASKS = _RGBMasks(red=0x00FF0000, green=0x0000FF00, blue=0x000000FF)


class GUI(object):
    """GUI.

    Parameters
    ----------
    window_title : str
        Title for the window.
    window_position : hienoi.Vector2i
        Initial window position.
    window_size : hienoi.Vector2i
        Initial window size.
    window_flags : int
        SDL2 window flags.
    view_aperture_x : float
        Initial length in world units to be shown on the X axis.
    view_zoom_range : hienoi.Vector2f
        Zoom value range for the view.
    mouse_wheel_step : float
        Coefficient value for each mouse wheel step.
    grid_density : float
        See :attr:`GUI.grid_density`.
    grid_adaptive_threshold : float
        See :attr:`GUI.grid_adaptive_threshold`.
    show_grid : bool
        See :attr:`GUI.show_grid`.
    background_color : hienoi.Vector4f
        See :attr:`GUI.background_color`.
    grid_color : hienoi.Vector4f
        See :attr:`GUI.grid_color`.
    grid_origin_color : hienoi.Vector4f
        See :attr:`GUI.grid_origin_color`.
    particle_display : int
        See :attr:`GUI.particle_display`.
    point_size : int
        See :attr:`GUI.point_size`.
    edge_feather : float
        See :attr:`GUI.edge_feather`.
    stroke_width : float
        See :attr:`GUI.stroke_width`.
    initialize_callback : function
        Callback function to initialize any GUI state.
        It takes a single argument ``gui``, an instance of this class.
    on_event_callback : function
        Callback function ran during the event polling.
        It takes 3 arguments: ``gui``, an instance of this class,
        ``data``, some data to pass back and forth between the caller and this
        callback function, and ``event``, the event fired.
    renderer : dict
        Keyword arguments for the configuration of the renderer. See the
        parameters for the class :class:`hienoi.renderer.Renderer`.

    Attributes
    ----------
    view_position : hienoi.Vector2f
        Position of the view (camera).
    view_zoom : float
        Current zoom value for the view.
    grid_density : float
        Density of the grid.
        A density of 10.0 means that there are around 10 grid divisions
        displayed on the X axis. A grid division unit represents a fixed length
        in world units, meaning that the actual grid density changes depending
        on the view's zoom.
    show_grid : bool
        True to show the grid.
    background_color : hienoi.Vector4f
        Color for the background.
    grid_color : hienoi.Vector4f
        Color for the grid.
    grid_origin_color : hienoi.Vector4f
        Color for the origin axis of the grid.
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
        such as :attr:`~hienoi.ParticleDisplay.CIRCLE`.
    quit : bool
        ``True`` to signal to the application that it should quit.
    has_view_changed : bool
        ``True`` if the view state has just been changed following an event. It
        is reset to ``False`` whenever :meth:`poll_events` is called.
    user_data : object
        Attribute reserved for any user data.
    """

    def __init__(self,
                 window_title='hienoi',
                 window_position=Vector2i(sdl2.SDL_WINDOWPOS_CENTERED,
                                          sdl2.SDL_WINDOWPOS_CENTERED),
                 window_size=Vector2i(800, 600),
                 window_flags=sdl2.SDL_WINDOW_RESIZABLE,
                 view_aperture_x=100.0,
                 view_zoom_range=Vector2f(1e-6, 1e+6),
                 mouse_wheel_step=0.01,
                 grid_density=10.0,
                 grid_adaptive_threshold=3.0,
                 show_grid=True,
                 background_color=Vector4f(0.15, 0.15, 0.15, 1.0),
                 grid_color=Vector4f(0.85, 0.85, 0.85, 0.05),
                 grid_origin_color=Vector4f(0.85, 0.25, 0.25, 0.25),
                 particle_display=ParticleDisplay.DISC,
                 point_size=4,
                 edge_feather=2.0,
                 stroke_width=0.0,
                 initialize_callback=None,
                 on_event_callback=None,
                 renderer=None):
        renderer = {} if renderer is None else renderer

        if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) != 0:
            raise RuntimeError(sdl2.SDL_GetError().decode())

        renderer_info = hienoi.renderer.get_info()
        if renderer_info.api == GraphicsAPI.OPENGL:
            sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_MAJOR_VERSION,
                                     renderer_info.major_version)
            sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_MINOR_VERSION,
                                     renderer_info.minor_version)
            if renderer_info.profile == GLProfile.CORE:
                sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_CONTEXT_PROFILE_MASK,
                                         sdl2.SDL_GL_CONTEXT_PROFILE_CORE)

        self._handles = _create_handles(window_title, window_position,
                                        window_size, window_flags,
                                        renderer_info)
        self._renderer = hienoi.renderer.Renderer(**renderer)

        self._initial_view_aperture_x = view_aperture_x
        self._view_zoom_range = view_zoom_range
        self._mouse_wheel_step = mouse_wheel_step
        self._grid_adaptive_threshold = grid_adaptive_threshold
        self._on_event_callback = on_event_callback
        self._listen_for_navigation = False
        self._is_view_manipulated = False

        self.view_position = Vector2f(0.0, 0.0)
        self._view_zoom = 1.0
        self.grid_density = grid_density
        self.show_grid = show_grid
        self.background_color = background_color
        self.grid_color = grid_color
        self.grid_origin_color = grid_origin_color
        self.particle_display = particle_display
        self.point_size = point_size
        self.edge_feather = edge_feather
        self.stroke_width = stroke_width
        self._navigation_action = NavigationAction.NONE
        self.quit = False

        self.user_data = UserData()
        if initialize_callback:
            initialize_callback(self)

    @property
    def view_zoom(self):
        return self._view_zoom

    @view_zoom.setter
    def view_zoom(self, value):
        self._view_zoom = max(self._view_zoom_range[0],
                              min(self._view_zoom_range[1], value))

    @property
    def navigation_action(self):
        return self._navigation_action

    @property
    def has_view_changed(self):
        return self._has_view_changed

    def poll_events(self, scene_state, data=None):
        """Process each event in the queue.

        Parameters
        ----------
        scene_state : hienoi.renderer.SceneState
            Scene state.
        data : object
            Data to pass back and forth between the caller and the function set
            for the 'on event' callback.
        """
        self._has_view_changed = False

        event = sdl2.SDL_Event()
        while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
            event_type = event.type
            if event_type == sdl2.SDL_QUIT:
                self._on_quit_event(event.quit)
            elif event_type == sdl2.SDL_WINDOWEVENT:
                self._on_window_event(event.window)
            elif event_type == sdl2.SDL_KEYDOWN:
                self._on_key_down_event(event.key, scene_state)
            elif event_type == sdl2.SDL_KEYUP:
                self._on_key_up_event(event.key)
            elif event_type == sdl2.SDL_MOUSEBUTTONDOWN:
                self._on_mouse_button_down_event(event.button)
            elif event_type == sdl2.SDL_MOUSEBUTTONUP:
                self._on_mouse_button_up_event(event.button)
            elif event_type == sdl2.SDL_MOUSEWHEEL:
                self._on_mouse_wheel_event(event.wheel)
            elif event_type == sdl2.SDL_MOUSEMOTION:
                self._on_mouse_motion_event(event.motion)

            if self._on_event_callback:
                self._on_event_callback(self, data, event)

            if self.quit:
                break

    def render(self, scene_state):
        """Render a new frame.

        Parameters
        ----------
        scene_state : hienoi.renderer.SceneState
            Scene state.
        """
        renderer_state = hienoi.renderer.State(
            window_size=self.get_window_size(),
            view_position=self.view_position,
            view_zoom=self._view_zoom,
            origin=self.world_to_screen(Vector2f(0.0, 0.0)),
            initial_view_aperture_x=self._initial_view_aperture_x,
            view_aperture=self.get_view_aperture(),
            grid_density=self.grid_density,
            grid_adaptive_threshold=self._grid_adaptive_threshold,
            background_color=self.background_color,
            grid_color=self.grid_color,
            grid_origin_color=self.grid_origin_color,
            show_grid=self.show_grid,
            particle_display=self.particle_display,
            point_size=self.point_size,
            edge_feather=self.edge_feather,
            stroke_width=self.stroke_width,
        )

        self._renderer.render(renderer_state, scene_state)

        if hienoi.renderer.get_info().api == GraphicsAPI.OPENGL:
            sdl2.SDL_GL_SwapWindow(self._handles.window)

    def terminate(self):
        """Cleanup the GUI resources."""
        self._renderer.cleanup()
        if hienoi.renderer.get_info().api == GraphicsAPI.OPENGL:
            sdl2.SDL_GL_DeleteContext(self._handles.renderer.context)

        sdl2.SDL_DestroyWindow(self._handles.window)
        sdl2.SDL_Quit()

    def get_window_size(self):
        """Retrieve the window size.

        Returns
        -------
        hienoi.Vector2i
            The window size.
        """
        window_size_x = ctypes.c_int()
        window_size_y = ctypes.c_int()
        sdl2.SDL_GetWindowSize(self._handles.window,
                               ctypes.byref(window_size_x),
                               ctypes.byref(window_size_y))
        return Vector2i(window_size_x.value, window_size_y.value)

    def get_view_aperture(self):
        """Retrieve the view aperture.

        It represents the area in world units covered by the view.

        Returns
        -------
        hienoi.Vector2f
            The view aperture.
        """
        window_size = self.get_window_size()
        aperture_x = self._initial_view_aperture_x / self._view_zoom
        return Vector2f(aperture_x, aperture_x * window_size.y / window_size.x)

    def get_mouse_position(self):
        """Retrieve the mouse position in screen space.

        Returns
        -------
        hienoi.Vector2i
            The mouse position.
        """
        position_x = ctypes.c_int()
        position_y = ctypes.c_int()
        sdl2.SDL_GetMouseState(ctypes.byref(position_x),
                               ctypes.byref(position_y))
        return Vector2i(position_x.value, position_y.value)

    def get_screen_to_world_ratio(self):
        """Retrieve the ratio to convert a sreen unit into a world unit.

        Returns
        -------
        float
            The screen to world ratio.
        """
        window_size = self.get_window_size()
        aperture_x = self._initial_view_aperture_x / self._view_zoom
        return aperture_x / window_size.x

    def screen_to_world(self, point):
        """Convert a point from screen space to world space coordinates.

        Parameters
        ----------
        point : hienoi.Vector2i
            Point in screen space coordinates.

        Returns
        -------
        hienoi.Vector2f
            The point in world space coordinates.
        """
        window_size = self.get_window_size()
        view_aperture = self.get_view_aperture()
        return Vector2f(
            (self.view_position.x
             + (point.x - window_size.x / 2.0)
             * view_aperture.x / window_size.x),
            (self.view_position.y
             - (point.y - window_size.y / 2.0)
             * view_aperture.y / window_size.y))

    def world_to_screen(self, point):
        """Convert a point from world space to screen space coordinates.

        Parameters
        ----------
        point : hienoi.Vector2f
            Point in world space coordinates.

        Returns
        -------
        hienoi.Vector2i
            The point in screen space coordinates.
        """
        window_size = self.get_window_size()
        view_aperture = self.get_view_aperture()
        return Vector2i(
            int(round(
                (window_size.x / view_aperture.x)
                * (-self.view_position.x + point.x + view_aperture.x / 2.0))),
            int(round(
                (window_size.y / view_aperture.y)
                * (self.view_position.y - point.y + view_aperture.y / 2.0))))

    def write_snapshot(self, filename):
        """Take a snapshot of the view and write it as a BMP image.

        Parameters
        ----------
        filename : str
            Destination filename.
        """
        pixel_size = 4
        pixels = self._renderer.read_pixels()
        surface = sdl2.SDL_CreateRGBSurfaceFrom(
            pixels.data, pixels.width, pixels.height,
            8 * pixel_size, pixels.width * pixel_size,
            _RGB_MASKS.red, _RGB_MASKS.green, _RGB_MASKS.blue, 0)
        sdl2.SDL_SaveBMP(surface, filename)
        sdl2.SDL_FreeSurface(surface)

    def _reset_view(self):
        """Reset the view position and zoom."""
        self.view_position = Vector2f(0.0, 0.0)
        self.view_zoom = 1.0
        self._has_view_changed = True

    def _fit_view(self, scene_state):
        """Fit the view to the scene."""
        if len(scene_state.particles) > 1:
            window_size = self.get_window_size()
            initial_size = Vector2f(
                self._initial_view_aperture_x,
                self._initial_view_aperture_x * window_size.y / window_size.x)

            lower_bounds = scene_state.lower_bounds
            upper_bounds = scene_state.upper_bounds
            required_size = (upper_bounds - lower_bounds).iscale(
                _FIT_VIEW_REL_PADDING)
            required_size = Vector2f(
                max(required_size.x,
                    initial_size.x * self._view_zoom_range[0]),
                max(required_size.y,
                    initial_size.y * self._view_zoom_range[0]))

            self.view_position = (lower_bounds + upper_bounds).iscale(0.5)
            self.view_zoom = min(initial_size.x / required_size.x,
                                 initial_size.y / required_size.y)
        elif len(scene_state.particles) == 1:
            self.view_position = Vector2f(
                *scene_state.particles['position'][0])
            self.view_zoom = 1.0
        else:
            self._reset_view()

        self._has_view_changed = True

    def _on_quit_event(self, event):
        """Event 'on quit'."""
        self.quit = True

    def _on_window_event(self, event):
        """Event 'on window'."""
        if event.event == sdl2.SDL_WINDOWEVENT_SIZE_CHANGED:
            self._renderer.resize(event.data1, event.data2)

    def _on_key_down_event(self, event, scene_state):
        """Event 'on key down'."""
        code = event.keysym.sym
        modifier = event.keysym.mod
        if modifier == sdl2.KMOD_NONE:
            if code == sdl2.SDLK_SPACE:
                self._listen_for_navigation = True
            elif code == sdl2.SDLK_d:
                self.particle_display = (
                    (self.particle_display + 1) % (ParticleDisplay._LAST + 1))
            elif code == sdl2.SDLK_f:
                self._fit_view(scene_state)
            elif code == sdl2.SDLK_g:
                self.show_grid = not self.show_grid
            elif code == sdl2.SDLK_r:
                self._reset_view()

    def _on_key_up_event(self, event):
        """Event 'on key up'."""
        code = event.keysym.sym
        if code == sdl2.SDLK_SPACE:
            self._listen_for_navigation = False

    def _on_mouse_button_down_event(self, event):
        """Event 'on mouse button down'."""
        if self._listen_for_navigation:
            if event.button == sdl2.SDL_BUTTON_LEFT:
                self._navigation_action = NavigationAction.MOVE
            elif event.button == sdl2.SDL_BUTTON_RIGHT:
                self._navigation_action = NavigationAction.ZOOM

    def _on_mouse_button_up_event(self, event):
        """Event 'on mouse button up'."""
        if (event.button == sdl2.SDL_BUTTON_LEFT
                or event.button == sdl2.SDL_BUTTON_RIGHT):
            self._navigation_action = NavigationAction.NONE

    def _on_mouse_wheel_event(self, event):
        """Event 'on mouse wheel'."""
        scale = 1.0 + self._mouse_wheel_step * event.y
        self.view_zoom *= scale
        self._has_view_changed = True

    def _on_mouse_motion_event(self, event):
        """Event 'on mouse motion'."""
        window_size = self.get_window_size()
        view_aperture = self.get_view_aperture()
        if self._navigation_action == NavigationAction.MOVE:
            self.view_position.set(
                (self.view_position.x
                 - event.xrel * view_aperture.x / window_size.x),
                (self.view_position.y
                 + event.yrel * view_aperture.y / window_size.y))
            self._has_view_changed = True
        elif self._navigation_action == NavigationAction.ZOOM:
            scale = (1.0
                     + float(event.xrel) / window_size.x
                     - float(event.yrel) / window_size.y)
            self.view_zoom *= scale
            self._has_view_changed = True


def _create_handles(window_title, window_position, window_size, window_flags,
                    renderer_info):
    """Create the SDL2 handles."""
    window_flags = sdl2.SDL_WINDOW_SHOWN | window_flags
    if renderer_info.api == GraphicsAPI.OPENGL:
        window_flags |= sdl2.SDL_WINDOW_OPENGL
        window = sdl2.SDL_CreateWindow(
            window_title.encode(),
            window_position.x, window_position.y,
            window_size.x, window_size.y,
            window_flags)
        if not window:
            raise RuntimeError(sdl2.SDL_GetError().decode())

        context = sdl2.SDL_GL_CreateContext(window)
        if not context:
            raise RuntimeError(sdl2.SDL_GetError().decode())

        # Try to disable the vertical synchronization. It applies to the active
        # context and thus needs to be called after `SDL_GL_CreateContext`.
        sdl2.SDL_GL_SetSwapInterval(0)

        return _Handles(
            window=window,
            renderer=_GLHandles(context=context))
