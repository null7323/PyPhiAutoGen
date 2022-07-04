from sdl_render import *


class sdl_transparent_cover:
    __slots__ = ("parent", "r", "g", "b", "a")

    def __init__(self, boundParent: renderer, cover_col: tuple[int, int, int, int] = (0, 0, 0, 255)):
        self.parent = boundParent
        self.r, self.g, self.b, self.a = cover_col

    def draw_cover(self):
        raw_col = self.parent.get_draw_color()
        self.parent.set_draw_color(self.r, self.g, self.b, self.a)
        self.parent.fill()
        self.parent.set_draw_color(*raw_col)

    def draw_ranged_cover(self, area: SDL_Rect):
        raw_col = self.parent.get_draw_color()
        self.parent.set_draw_color(self.r, self.g, self.b, self.a)
        self.parent.fill_area(area)
        self.parent.set_draw_color(*raw_col)

    def set_alpha(self, a: int):
        self.a = a

    def get_alpha(self):
        return self.a
