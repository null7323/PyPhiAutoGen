from chart import *
from sdl_render import *
from sdl_image import *
from sdl_transparent_cover import *
from sdl_line import *
from math import sin, cos, pi


class global_resource:
    tap: sdl_image = None
    flick: sdl_image = None
    hold_head: sdl_image = None
    hold_body: sdl_image = None
    hold_tail: sdl_image = None
    drag: sdl_image = None

    tap_hl: sdl_image = None
    flick_hl: sdl_image = None
    hold_head_hl: sdl_image = None
    hold_body_hl: sdl_image = None
    drag_hl: sdl_image = None

    @classmethod
    def init_tap(cls, path: str, parent: sdl_renderer):
        cls.tap = sdl_image.open_image(path, parent)

    @classmethod
    def init_flick(cls, path: str, parent: sdl_renderer):
        cls.flick = sdl_image.open_image(path, parent)

    @classmethod
    def init_drag(cls, path: str, parent: sdl_renderer):
        cls.drag = sdl_image.open_image(path, parent)

    @classmethod
    def init_hold(cls, head_path: str, body_path: str, tail_path: str or None, parent: sdl_renderer):
        cls.hold_head = sdl_image.open_image(head_path, parent)
        cls.hold_body = sdl_image.open_image(body_path, parent)
        cls.hold_tail = None if tail_path is None else sdl_image.open_image(tail_path, parent)

    @classmethod
    def init_tap_hl(cls, path: str, parent: sdl_renderer):
        cls.tap_hl = sdl_image.open_image(path, parent)

    @classmethod
    def init_flick_hl(cls, path: str, parent: sdl_renderer):
        cls.flick_hl = sdl_image.open_image(path, parent)

    @classmethod
    def init_hold_hl(cls, head_path: str, body_path: str, parent: sdl_renderer):
        cls.hold_head_hl = sdl_image.open_image(head_path, parent)
        cls.hold_body_hl = sdl_image.open_image(body_path, parent)

    @classmethod
    def init_audio(cls):
        required = SDL_AudioSpec(48000, AUDIO_U16, 2, 512)
        result = SDL_AudioSpec(48000, AUDIO_U16, 2, 512)
        SDL_OpenAudio(byref(required), byref(result))


class render_resource:
    pass


class render_options:
    """Represents a structure indicating render options."""
    __slots__ = ("width", "height", "fps", "comparative_note_speed", "visibility_check",
                 "all_perfect_indication", "show_hidden_line")

    def __init__(self, w: int, h: int, fps: int = 60, note_speed: float = 1, visibility_check: bool = True,
                 all_perfect_indication: bool = True, show_hidden_line: bool = False):
        self.width = w
        self.height = h
        self.fps = fps
        self.comparative_note_speed = note_speed
        self.visibility_check = visibility_check
        self.all_perfect_indication = all_perfect_indication
        self.show_hidden_line = show_hidden_line

    def get_line_color(self) -> tuple[int, int, int, int]:
        return (0xfe, 0xff, 0xa9, 0xff) if self.all_perfect_indication else (0xff, 0xff, 0xff, 0xff)


class judge_line_renderer:
    """Represents a judge line renderer."""
    __slots__ = ("judge_line", "win", "opt", "real_time", "line_x", "line_y", "rotation", "position_y", "draw_line",
                 "instant_judged_map")

    def __init__(self, line_data: phi_judge_line, parent_window: sdl_window, options: render_options):
        self.judge_line = line_data
        self.win = parent_window
        self.opt = options
        self.real_time = 0.0  # in seconds
        self.line_x = 0
        self.line_y = 0
        self.rotation = 0
        self.position_y = 0
        self.instant_judged_map = dict[float, bool]()

        scale = options.height / 18.75 if options.width > options.height * 0.75 else options.height / 14.0625
        line_len = int(options.width * 3)
        line_width = int(round(scale * 0.15 * 0.85))

        self.draw_line = sdl_line(parent_window.renderer, line_len, line_width, options.get_line_color())

        for n in self.judge_line.notesAbove:
            self.instant_judged_map[n.real_time] = False
        for n in self.judge_line.notesBelow:
            self.instant_judged_map[n.real_time] = False

    def adjust_line_state(self):
        self.adjust_alpha()
        self.adjust_rotation()
        self.adjust_movement()
        self.adjust_speed()

    def adjust_speed(self):
        real_time = self.real_time
        for ev in self.judge_line.speedEvents:
            if ev.is_real_time_valid(real_time):
                self.position_y = ev.get_value_unchecked(real_time)
                return

    def adjust_rotation(self):
        real_time = self.real_time
        for ev in self.judge_line.rotateEvents:
            if ev.is_real_time_valid(real_time):
                self.rotation = -ev.get_value_unchecked(real_time)
                return

    def adjust_alpha(self):
        real_time = self.real_time
        for ev in self.judge_line.disappearEvents:
            if ev.is_real_time_valid(real_time):
                alpha = int(ev.get_value_unchecked(real_time) * 255.0)
                self.draw_line.set_alpha(alpha)
                return

    def adjust_movement(self):
        real_time = self.real_time
        w, h = self.opt.width, self.opt.height
        for ev in self.judge_line.moveEvents:
            if ev.is_real_time_valid(real_time):
                x, y = ev.get_value_unchecked(real_time)
                self.line_x = int(w * x)
                self.line_y = int(h * y)
                return

    def advance_frame(self):
        self.real_time += (1 / self.opt.fps)
        for k in self.instant_judged_map.keys():
            if k < self.real_time:
                self.instant_judged_map[k] = True
                continue
            break
        self.adjust_line_state()

    def render_line(self):
        self.draw_line.draw(self.line_x, self.line_y, self.rotation)

    def draw_instant_notes_above(self):
        w, h = self.opt.width, self.opt.height
        len_rat = w * 9.0 / 160.0
        ns = self.opt.comparative_note_speed
        sin_value = sin(pi / 180.0 * self.rotation)
        cos_value = cos(pi / 180.0 * self.rotation)
        base_note_height = 0.018457 * h
        for n in self.judge_line.notesAbove:
            if n.note_type == NOTE_TYPE_HOLD:
                continue
            if self.instant_judged_map[n.real_time]:
                continue
            if not self.instant_judged_map[n.real_time] and n.real_time < self.real_time:
                # to do: draw animation here
                pass

            dy = (n.floor_position - self.position_y) * n.speed * h * 0.6 * ns
            project_x = self.line_x + len_rat * n.position_x * cos_value
            offset_x = project_x + dy * sin_value

            project_y = self.line_y + 0.6 * w * n.position_x * sin_value
            offset_y = (project_y - len_rat * (n.floor_position - self.position_y) * n.speed * cos_value)

            if self.opt.visibility_check and n.real_time > self.real_time:
                if dy > -1e-3 * len_rat:
                    if n.note_type == NOTE_TYPE_HOLD and n.speed == 0:
                        continue
                else:
                    continue

            note_height = base_note_height
            img = global_resource.tap

            if n.note_type == NOTE_TYPE_TAP:
                if n.multi_highlight:
                    img = global_resource.tap_hl
                note_height /= 2
            elif n.note_type == NOTE_TYPE_FLICK:
                if n.multi_highlight:
                    img = global_resource.flick_hl
                else:
                    img = global_resource.flick
            else:
                if n.multi_highlight:
                    img = global_resource.drag_hl
                else:
                    img = global_resource.drag


class chart_renderer:
    __slots__ = ("chart_object", "judge_line_renderer_list", "window")

    def __init__(self, init_chart: phi_chart, render_opt: render_options):
        self.chart_object = init_chart
        self.window = sdl_window("Autoplay", render_opt.width, render_opt.height)
        self.judge_line_renderer_list = list[judge_line_renderer]()
        for line in init_chart.lines:
            self.judge_line_renderer_list.append(judge_line_renderer(line, self.window, render_opt))

    def render_frame(self):
        self.window.renderer.clear()
        for line_renderer in self.judge_line_renderer_list:
            line_renderer.render_line()

        for line_renderer in self.judge_line_renderer_list:
            line_renderer.advance_frame()
