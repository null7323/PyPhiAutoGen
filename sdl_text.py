from sdl2.sdlttf import *
from sdl_render import sdl_surface, sdl_texture, sdl_renderer


class sdl_font:
    __slots__ = ("p_font", "font_size")
    library_initialized: bool = False

    def __init__(self, ttf_font, size: int):
        self.p_font = ttf_font
        self.font_size = size

    def destroy(self):
        if self.p_font is None:
            return

        TTF_CloseFont(self.p_font)

    @classmethod
    def open_ttf(cls, file_path: str, font_size: int):
        ptr = TTF_OpenFont(file_path.encode("utf-8"), font_size)
        return cls(ptr, font_size)

    @classmethod
    def init(cls):
        if not cls.library_initialized:
            TTF_Init()
        cls.library_initialized = True

    @classmethod
    def quit(cls):
        if cls.library_initialized:
            TTF_Quit()
        cls.library_initialized = False


class sdl_text:
    __slots__ = ("font", "text", "tex", "col")

    def __init__(self, text: str, font: sdl_font,
                 parent: sdl_renderer, foreground_color: tuple[int, int, int] = (255, 255, 255, 255)):
        self.font = sdl_font
        self.text = text
        self.col = SDL_Color(foreground_color[0], foreground_color[1], foreground_color[2], foreground_color[3])
        s = TTF_RenderText_Blended(font.p_font, text.encode("utf-8"), self.col)
        self.tex = sdl_texture.from_surface(sdl_surface(s), parent)

