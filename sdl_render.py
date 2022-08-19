# coding:gbk
import copy

from sdl2 import *
from sdl2.render import *
from sdl2.video import *
from ctypes import byref, c_int, c_uint, c_uint8, c_void_p, c_double
from functools import singledispatch


def none_call_back(placeholder: object):
    return


class sdl_renderer:
    __slots__ = ("handle", "width", "height", "parent")

    def __init__(self, parent):
        self.parent = parent
        self.width = parent.width
        self.height = parent.height
        self.handle = SDL_CreateRenderer(parent.handle, c_int(-1), SDL_RENDERER_ACCELERATED)
        SDL_SetRenderDrawBlendMode(self.handle, SDL_BLENDMODE_BLEND)

    def set_draw_color(self, r: int, g: int, b: int, a: int):
        """Sets the drawing color. The color is used for clear as well."""
        cr = c_uint8(r)
        cg = c_uint8(g)
        cb = c_uint8(b)
        ca = c_uint8(a)
        SDL_SetRenderDrawColor(self.handle, cr, cg, cb, ca)

    def get_draw_color(self) -> tuple[int, int, int, int]:
        r = c_uint8(0)
        g = c_uint8(0)
        b = c_uint8(0)
        a = c_uint8(0)
        SDL_GetRenderDrawColor(self.handle, byref(r), byref(g), byref(b), byref(a))
        return r.value, g.value, b.value, a.value

    def clear(self):
        """Clears the renderer with drawing color."""
        SDL_RenderClear(self.handle)

    def present(self):
        """Swaps the buffers to present a new frame."""
        SDL_RenderPresent(self.handle)

    def fill_area(self, area: SDL_Rect):
        """Fills the specified area with drawing color."""
        SDL_RenderFillRect(self.handle, area)

    def fill(self):
        """Fills the entire renderer with drawing color."""
        SDL_RenderFillRect(self.handle, POINTER(SDL_Rect)())

    def get_render_target(self):
        return SDL_GetRenderTarget(self.handle)

    def set_render_texture(self, target):
        """Sets the render target to the given target. The target should be a texture."""
        SDL_SetRenderTarget(self.handle, target.handle)

    def set_render_target(self, handle):
        """Sets the render target to the given handle."""
        SDL_SetRenderTarget(self.handle, handle)

    def reset_render_target(self):
        """Resets the render target to the window."""
        p = POINTER(SDL_Texture)
        SDL_SetRenderTarget(self.handle, p.from_param(None))

    def destroy(self):
        if self.handle != 0:
            SDL_DestroyRenderer(self.handle)
        self.handle = 0

    def is_renderer_available(self):
        return self.handle != 0


class event_handle_state:
    """Represents a structure indicating the state of an event handler."""
    __slots__ = ("interrupted", "accomplished")

    def __init__(self):
        self.interrupted = False
        self.accomplished = False

    def set_interruption(self):
        """Indicates that the handle operation is interrupted."""
        self.interrupted = True
        self.accomplished = False

    def set_accomplishment(self):
        """Indicates that the handle operation is accomplished. This call is conflict with interruption flag."""
        if not self.interrupted:
            self.accomplished = True

    def reset(self):
        """Resets current handle state."""
        self.interrupted = False
        self.accomplished = False


class event_handler:
    """Provides easy access to handle SDL events."""
    __slots__ = ("bound_parent", "callbacks", "state")

    def __init__(self, parent):
        self.bound_parent = parent
        self.callbacks = []
        self.state = event_handle_state()

    def add_callback(self, callback):
        """Adds a callback to the handler."""
        self.callbacks.append(callback)

    def pop_first_callback(self):
        """Removes the first callback."""
        self.callbacks.pop(0)

    def pop_last_callback(self):
        """Removes the last callback."""
        self.callbacks.pop()

    def clear_callback(self):
        """Removes every callback from the delegation."""
        self.callbacks.clear()

    def handle(self, *args, **kwargs):
        """Iterates through the callback list and invokes each method to handle events."""
        self.state.reset()

        for callback in self.callbacks:
            callback(self.state, *args, **kwargs)

            if self.state.interrupted:
                return

        self.state.set_accomplishment()


class sdl_window:
    __slots__ = ("handle", "renderer", "width", "height", "handler")

    @staticmethod
    def basic_sdl_event_handler(state: event_handle_state, win, event_list: list):
        """
        A basic event handler.\n
        :param state: A structure that represents the handler's state.
        :param win: The window object.
        :param event_list: The SDL event to handle.
        :return: None.
        """
        for ev in event_list:
            if ev.type == 256:
                # SDL_Event.SDL_QUIT == 256 -> true
                win.destroy()
                state.set_interruption()

    def __init__(self, caption: str, w: int, h: int, fullScreen: bool = False, borderless: bool = False):
        if fullScreen:
            mode = SDL_DisplayMode()
            SDL_GetCurrentDisplayMode(0, byref(mode))
            w = mode.w
            h = mode.h
        self.width = w
        self.height = h
        flags = SDL_WINDOW_ALLOW_HIGHDPI | SDL_WINDOW_SHOWN

        if borderless:
            flags |= SDL_WINDOW_BORDERLESS

        self.handle = SDL_CreateWindow(caption.encode(), SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, w, h, flags)
        self.renderer: sdl_renderer = sdl_renderer(self)
        self.handler = event_handler(self)
        self.handler.add_callback(sdl_window.basic_sdl_event_handler)

    def get_event_handler(self):
        """Returns the event handler of current window."""
        return self.handler

    def handle_events(self):
        """Calls the handle method of current handler."""
        self.handler.handle(self, sdl_window.get_events())

    def destroy(self):
        if self.renderer is not None:
            self.renderer.destroy()

        if self.handle != 0:
            SDL_DestroyWindow(self.handle)

        self.renderer = None
        self.handle = 0

    @staticmethod
    def get_events():
        """Gets all event waiting in SDL event queue."""
        ev_list = []
        while True:  # add this loop to create new SDL_Event.
            ev = SDL_Event()
            if SDL_PollEvent(byref(ev)) != 0:
                ev_list.append(ev)
            else:
                break
        return ev_list

    def is_window_available(self):
        """Determines whether current window is available."""
        return self.handle != 0


class sdl_surface:
    __slots__ = ("width", "height", "handle", "parent")

    def __init__(self, ptr):
        """Directly initializes this instance with a pointer to SDL_Surface structure."""
        self.handle = ptr
        self.width = -1
        self.height = -1

    @classmethod
    def generate(cls, w: int, h: int, depth: int = 32) -> surface:
        """
        Generates a new SDL surface using SDL_CreateRGBSurface, settings its blend mode to SDL_BLENDMODE_BLEND.\n
        :param w: The width in pixel of new surface.
        :param h: The height in pixel of new surface.
        :param depth: The color depth. Default is 32.
        :return: A new surface object.
        """
        s = cls(0)
        s.width = int(w)
        s.height = int(h)
        s.handle = SDL_CreateRGBSurface(0, c_int(s.width), c_int(s.height), c_int(depth),
                                        0xFF000000, 0x00FF0000, 0x0000FF00, 0x000000FF)
        SDL_SetSurfaceBlendMode(s.handle, SDL_BLENDMODE_BLEND)
        return s

    def is_surface_available(self):
        return self.handle != 0

    def blit_surface(self, src: SDL_Rect, dst: SDL_Rect, target):
        """
        Blit current surface to target.\n
        :param src:
        :param dst:
        :param target:
        :return:
        """
        SDL_BlitSurface(self.handle, byref(src), target.handle, byref(dst))

    def destroy(self):
        if self.handle != 0:
            SDL_FreeSurface(self.handle)
        self.handle = 0

    def lock(self):
        """
        Locks current surface.
        """
        SDL_LockSurface(self.handle)

    def unlock(self):
        """
        Unlocks current surface.
        """
        SDL_UnlockSurface(self.handle)

    @classmethod
    def convert_format(cls, source, pixel_format: SDL_PixelFormat):
        s = cls.generate(source.width, source.height)
        s.destroy()
        s.handle = SDL_ConvertSurface(source.handle, byref(pixel_format), 0)
        return s


class texture_access:
    static: int = SDL_TEXTUREACCESS_STATIC
    streaming: int = SDL_TEXTUREACCESS_STREAMING
    render_target: int = SDL_TEXTUREACCESS_TARGET


class sdl_texture:
    __slots__ = ("width", "height", "handle", "parent", "access")

    def __init__(self, w: int, h: int, ptr, parent: sdl_renderer, access: int):
        if w <= 0:
            w = parent.width
        if h <= 0:
            h = parent.height
        self.width = int(w)
        self.height = int(h)
        self.handle = ptr
        self.parent = parent
        self.access = access

    @classmethod
    def generate(cls, parent: sdl_renderer, w: int = -1, h: int = -1, access: int = SDL_TEXTUREACCESS_STATIC):
        if w <= 0:
            w = parent.width
        if h <= 0:
            h = parent.height
        w = int(w)
        h = int(h)

        handle = SDL_CreateTexture(parent.handle, c_uint(SDL_PIXELFORMAT_ARGB8888),
                                   c_int(access), c_int(w), c_int(h))
        SDL_SetTextureBlendMode(handle, SDL_BLENDMODE_BLEND)
        return cls(w, h, handle, parent, access)

    def destroy(self):
        if self.handle != 0:
            SDL_DestroyTexture(self.handle)
        self.handle = 0

    def update_content(self, pointer: c_void_p, width: int, depth: int = 4):
        SDL_UpdateTexture(self.handle, POINTER(SDL_Rect)(), pointer, c_int(int(width * depth)))

    def direct_copy_to_parent(self):
        null_p = POINTER(SDL_Rect)()
        SDL_RenderCopy(self.parent.handle, self.handle, null_p, null_p)

    def crop_copy_to_parent(self, source: SDL_Rect, destination: SDL_Rect):
        SDL_RenderCopy(self.parent.handle, self.handle, byref(source), byref(destination))

    def copy_to_parent(self, area: SDL_Rect):
        SDL_RenderCopy(self.parent.handle, self.handle, POINTER(SDL_Rect)(), byref(area))

    def rotate_copy_to_parent(self, area: SDL_Rect, center: SDL_Point, angle: float):
        c_angle = c_double(angle)
        SDL_RenderCopyEx(self.parent.handle, self.handle, c_void_p(0), byref(area),
                         c_angle, byref(center), SDL_FLIP_NONE)

    def is_texture_available(self):
        return self.handle != 0

    def set_alpha(self, a: int):
        SDL_SetTextureAlphaMod(self.handle, a)

    @classmethod
    def copy(cls, tex):
        ret = cls(tex.width, tex.height, None, tex.parent, texture_access.render_target)
        raw_target = ret.parent.get_render_target()
        ret.parent.set_render_texture(ret)
        tex.direct_copy_to_parent()
        ret.parent.set_render_target(raw_target)
        return ret

    @classmethod
    def from_surface(cls, data: sdl_surface, parent: sdl_renderer):
        tex = cls(data.width, data.height, SDL_CreateTextureFromSurface(parent.handle, data.handle), parent,
                  texture_access.static)
        SDL_SetTextureBlendMode(tex.handle, SDL_BLENDMODE_BLEND)
        return tex
