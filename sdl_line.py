from sdl_render import *
__all__ = ["sdl_line", ]


class sdl_line:
    """Represents a line object which can be drawn to SDL renderer."""
    __slots__ = ("tex", "parent", "w", "h")

    def __init__(self, parent: sdl_renderer, w: int, h: int, init_color=(255, 255, 255, 255)):
        self.parent = parent

        # Directly generate a new texture to fill.
        self.tex = sdl_texture.generate(parent, w, h, texture_access.render_target)
        self.w, self.h = w, h
        raw_target = parent.get_render_target()
        parent.set_render_texture(self.tex)
        raw_col = parent.get_draw_color()
        parent.set_draw_color(*init_color)
        parent.fill_area(SDL_Rect(0, 0, w, h))
        parent.set_draw_color(*raw_col)
        parent.set_render_target(raw_target)

    def set_alpha(self, a: int):
        self.tex.set_alpha(a)

    def draw(self, x_center: int, y_center: int, rotation: float):
        """
        Draws current line to the renderer.\n
        :param x_center: The x coordinate of the center.
        :param y_center: The y coordinate of the center.
        :param rotation: The degree that the line rotates.
        :return: None
        """
        dst = SDL_Rect(x_center - self.w // 2, y_center - self.h // 2, self.w, self.h)
        SDL_RenderCopyEx(self.parent.handle, self.tex.handle, POINTER(SDL_Rect)(), byref(dst), c_double(rotation),
                         SDL_Point(self.w // 2, self.h // 2), SDL_RendererFlip(0))

    def destroy(self):
        self.tex.destroy()
