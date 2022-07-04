from sdl_render import *


class sdl_line:
    __slots__ = ("tex", "parent", "w", "h")

    def __init__(self, parent: renderer, w: float, h: float):
        self.parent = parent
        self.tex = texture(parent, int(w * parent.width), int(h * parent.height), texture_access.render_target)
