from sdl_render import *
from sdl2.sdlimage import *
from ctypes import cast, c_void_p, POINTER, c_uint8


class sdl_image:
    __slots__ = ("tex", "width", "height", "parent")

    def __init__(self, data: surface, parent: renderer):
        self.parent = parent
        if data is None or parent is None:
            self.tex = None
            self.width = 0
            self.height = 0
            return
        self.tex = texture.from_surface(data, parent)
        self.width = self.tex.width
        self.height = self.tex.height

    def crop(self, x: int, y: int, w: int, h: int):
        ret = sdl_image(None, self.tex.parent)
        ret.tex = texture(self.tex.parent, w, h, texture_access.streaming)
        ret.width = w
        ret.height = h

        parent = self.tex.parent
        parent.set_render_texture(ret.tex)

        area = SDL_Rect(x, y, w, h)
        dst = SDL_Rect(0, 0, w, h)
        self.tex.crop_copy_to_parent(area, dst)
        parent.reset_render_target()

        return ret

    def set_alpha(self, a: int):
        self.tex.set_alpha(a)

    def destroy(self):
        if self.tex is not None:
            self.tex.destroy()
        self.tex = None
        self.width = self.height = 0
        self.parent = None

    @classmethod
    def open_image(cls, path: str, parent: renderer):
        s = IMG_Load(path.encode())
        ret = cls(surface(s), parent)
        SDL_FreeSurface(s)
        return ret
