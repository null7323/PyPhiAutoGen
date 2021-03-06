from sdl_render import *


class sdl_transparent_cover:
    __slots__ = ("parent", "r", "g", "b", "a")

    def __init__(self, boundParent: sdl_renderer, cover_col: tuple[int, int, int, int] = (0, 0, 0, 255)):
        """
        Initializes a new transparent cover with specified color.\n
        :param boundParent: The target renderer to draw at.
        :param cover_col: The color to initialize the cover. Default is black (not transparent).
        """
        self.parent = boundParent
        self.r, self.g, self.b, self.a = cover_col

    def draw_cover(self) -> None:
        """
        Draws current cover to the renderer. This operation is not thread-safe.\n
        :return: None.
        """
        raw_col = self.parent.get_draw_color()
        self.parent.set_draw_color(self.r, self.g, self.b, self.a)
        self.parent.fill()
        self.parent.set_draw_color(*raw_col)

    def draw_ranged_cover(self, area: SDL_Rect):
        """
        Draws a ranged cover to the renderer. This operation is not thread-safe.\n
        :param area: A SDL rectangle structure, indicating where is drawn.
        :return: None.
        """
        raw_col = self.parent.get_draw_color()
        self.parent.set_draw_color(self.r, self.g, self.b, self.a)
        self.parent.fill_area(area)
        self.parent.set_draw_color(*raw_col)

    def set_alpha(self, a: int):
        self.a = a

    def get_alpha(self):
        return self.a
