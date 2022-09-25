from sdl_render import *
from sdl2.sdlimage import *
from ctypes import cast, c_void_p, POINTER, c_uint8


class sdl_image:
    __slots__ = ("tex", "width", "height", "parent")

    def __init__(self, data: sdl_surface or None, parent: sdl_renderer):
        """Using given SDL surface and renderer to initialize a new image instance."""
        self.parent = parent
        if data is None or parent is None:
            self.tex = None
            self.width = 0
            self.height = 0
            return
        self.tex = sdl_texture.from_surface(data, parent)
        self.width = self.tex.width
        self.height = self.tex.height

    def crop(self, x: int, y: int, w: int, h: int):
        x, y, w, h = int(x), int(y), int(w), int(h)

        parent = self.tex.parent
        ret = sdl_image(None, parent)
        ret.tex = sdl_texture.generate(self.tex.parent, w, h, texture_access.render_target)

        parent.set_render_texture(ret.tex)

        area = SDL_Rect(x, y, w, h)
        dst = SDL_Rect(0, 0, w, h)
        self.tex.crop_copy_to_parent(area, dst)
        parent.reset_render_target()

        return ret

    def crop_to_fit(self, width_height_rat: float):
        curr_width_height_rat = self.width / self.height

        if curr_width_height_rat == width_height_rat:
            return self.crop(0, 0, self.width, self.height)

        if curr_width_height_rat > width_height_rat:
            # width is wider, so we cut its width.
            narrowed_width = self.height * width_height_rat
            return self.crop((self.width - narrowed_width) // 2, 0, narrowed_width, self.height)

        narrowed_height = self.width / width_height_rat
        return self.crop(0, (self.height - narrowed_height) // 2, self.width, narrowed_height)

    def set_alpha(self, a: int):
        self.tex.set_alpha(a)

    def copy(self):
        return self.crop(0, 0, self.width, self.height)

    def destroy(self):
        if self.tex is not None:
            self.tex.destroy()
        self.tex = None
        self.width = self.height = 0
        self.parent = None

    @classmethod
    def open_image(cls, path: str, parent: sdl_renderer, file_size: (int, int) = (-1, -1)):
        s = IMG_Load(path.encode())
        ret = cls(sdl_surface(s), parent)
        ret.width, ret.height = file_size
        SDL_FreeSurface(s)
        return ret
