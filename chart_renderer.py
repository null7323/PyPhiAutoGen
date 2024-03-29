import copy

from chart import *
from sdl_render import *
from sdl_image import *
from sdl_transparent_cover import *
from sdl_line import *
from math import sin, cos, pi
from wav_audio import audio_file


class global_resource:
    """
    Represents resources that every renderer instance uses.
    """

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

    tap_sound: audio_file or None = None
    drag_sound: audio_file or None = None
    flick_sound: audio_file or None = None

    note_sound_map: dict[int, audio_file] or None = None

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
    def init_tap_hold_sound(cls, path: str):
        cls.tap_sound = audio_file.open_wav_file(path)

    @classmethod
    def init_flick_sound(cls, path: str):
        cls.flick_sound = audio_file.open_wav_file(path)

    @classmethod
    def init_drag_sound(cls, path: str):
        cls.drag_sound = audio_file.open_wav_file(path)

    @classmethod
    def generate_note_sound_map(cls):
        cls.note_sound_map = {
            NOTE_TYPE_TAP: cls.tap_sound,
            NOTE_TYPE_FLICK: cls.flick_sound,
            NOTE_TYPE_DRAG: cls.drag_sound,
            NOTE_TYPE_HOLD: cls.tap_sound
        }

    @classmethod
    def close_sound(cls):
        cls.tap_sound = None
        cls.flick_sound = None
        cls.drag_sound = None


class render_resource:
    __slots__ = ("illustration_image", "audio_file")

    def __init__(self, img: sdl_image, wav: audio_file):
        self.illustration_image = img
        self.audio_file = wav

    @classmethod
    def open_file(cls, img_path: str, wav_path: str, parent: sdl_renderer):
        return cls(sdl_image.open_image(img_path, parent), audio_file.open_wav_file(wav_path))


class render_options:
    """Represents a structure indicating render options."""
    __slots__ = ("width", "height", "fps", "cover_alpha", "comparative_note_speed", "visibility_check",
                 "all_perfect_indication", "show_hidden_line")

    def __init__(self, w: int, h: int, fps: int = 60, cover_alpha: int = 0x6F, note_speed: float = 1,
                 visibility_check: bool = True,
                 all_perfect_indication: bool = True, show_hidden_line: bool = False):
        self.width = w
        self.height = h
        self.fps = fps
        self.cover_alpha = cover_alpha
        self.comparative_note_speed = note_speed
        self.visibility_check = visibility_check
        self.all_perfect_indication = all_perfect_indication
        self.show_hidden_line = show_hidden_line

    def get_line_color(self) -> tuple[int, int, int, int]:
        return (0xfe, 0xff, 0xa9, 0xff) if self.all_perfect_indication else (0xff, 0xff, 0xff, 0xff)


class hit_effect_player:
    __slots__ = ("note_list", "index")

    def __init__(self, list_of_notes: list[phi_note]):
        self.note_list = list_of_notes
        self.index: int = 0

    def play_time_less_than(self, tm: float):
        len_of_notes = len(self.note_list)
        while self.index < len_of_notes:
            n = self.note_list[self.index]
            if n.real_time < tm:
                global_resource.note_sound_map[n.note_type].async_play()
                self.index += 1
                continue
            break


class judge_line_renderer:
    """Represents a judge line renderer."""
    __slots__ = ("judge_line", "win", "opt", "real_time", "line_x", "line_y", "rotation", "position_y", "draw_line",
                 "instant_judged_map", "last_alpha_index", "last_move_index", "last_rotate_index")

    def __init__(self, line_data: phi_judge_line, parent_window: sdl_window, options: render_options):
        self.judge_line = line_data
        self.win = parent_window
        self.opt = options
        self.real_time = 0.0  # in seconds
        self.line_x = 0
        self.line_y = 0
        self.rotation = 0
        self.position_y = 0
        self.last_alpha_index = 0
        self.last_move_index = 0
        self.last_rotate_index = 0
        self.instant_judged_map = dict[float, bool]()

        scale = options.height / 18.75 if options.width > options.height * 0.75 else options.height / 14.0625
        line_len = int(options.width * 3)
        line_width = int(round(scale * 0.15 * 0.925))

        self.draw_line = sdl_line(parent_window.renderer, line_len, line_width, options.get_line_color())

        for n in self.judge_line.notes_above:
            self.instant_judged_map[n.real_time] = False
        for n in self.judge_line.notes_below:
            self.instant_judged_map[n.real_time] = False

    def adjust_line_state(self):
        self.adjust_alpha()
        self.adjust_rotation()
        self.adjust_movement()
        self.adjust_speed()

    def adjust_speed(self):
        real_time = self.real_time
        for ev in self.judge_line.speed_events:
            if ev.is_real_time_valid(real_time):
                self.position_y = ev.get_value_unchecked(real_time)
                return

    def adjust_rotation(self):
        real_time = self.real_time
        rotate_events = self.judge_line.rotate_events
        for i in range(self.last_rotate_index, len(rotate_events)):
            ev = rotate_events[i]
            if ev.is_real_time_valid(real_time):
                self.rotation = -ev.get_value_unchecked(real_time)
                self.last_rotate_index = i
                return

    def adjust_alpha(self):
        real_time = self.real_time
        alpha_events = self.judge_line.disappear_events
        for i in range(self.last_alpha_index, len(alpha_events)):
            ev = alpha_events[i]
            if ev.is_real_time_valid(real_time):
                alpha = int(ev.get_value_unchecked(real_time) * 255.0)
                self.draw_line.set_alpha(alpha)
                self.last_alpha_index = i
                return

    def adjust_movement(self):
        real_time = self.real_time
        w, h = self.opt.width, self.opt.height
        move_events = self.judge_line.move_events
        for i in range(self.last_move_index, len(move_events)):
            ev = move_events[i]
            if ev.is_real_time_valid(real_time):
                x, y = ev.get_value_unchecked(real_time)
                self.line_x = int(w * x)
                self.line_y = int(h * y)
                self.last_move_index = i
                return

    def advance_frame(self):
        self.real_time += (1 / self.opt.fps)
        '''
        for k in self.instant_judged_map.keys():
            if k < self.real_time:
                self.instant_judged_map[k] = True
                continue
            break
        '''
        self.adjust_line_state()

    def render_line(self):
        self.draw_line.draw(self.line_x, self.line_y, self.rotation)

    @staticmethod
    def get_instant_note_image(n: phi_note):
        '''
        match n.note_type:
            case 1:
                return global_resource.tap_hl if n.multi_highlight else global_resource.tap
            case 2:
                return global_resource.drag_hl if n.multi_highlight else global_resource.drag
            case 4:
                return global_resource.flick_hl if n.multi_highlight else global_resource.flick
            case _:
                return None
        '''
        hl_map = [global_resource.tap_hl, global_resource.drag_hl, None, global_resource.flick_hl]
        single_map = [global_resource.tap, global_resource.drag, None, global_resource.flick]
        if n.multi_highlight:
            return hl_map[n.note_type - 1]
        return single_map[n.note_type - 1]

    def draw_instant_notes_above(self):
        w, h = self.opt.width, self.opt.height
        len_rat = w * 9.0 / 160.0
        ns = self.opt.comparative_note_speed
        sin_value = sin(pi / 180.0 * self.rotation)
        cos_value = cos(pi / 180.0 * self.rotation)
        base_note_height = 0.018457 * h
        for n in self.judge_line.notes_above:
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
            img = judge_line_renderer.get_instant_note_image(n)


class chart_renderer:
    __slots__ = ("chart_object", "judge_line_renderer_list", "window",
                 "cover", "bg", "effect_sound_player", "real_time", "fps")

    def __init__(self, init_chart: phi_chart, render_opt: render_options, illustration_path: str = "",
                 super_sampling: bool = False):
        self.chart_object = init_chart
        self.window = sdl_window("Autoplay", render_opt.width, render_opt.height, False, False, super_sampling)
        self.judge_line_renderer_list = list[judge_line_renderer]()
        self.cover = sdl_transparent_cover(self.window.renderer, (0, 0, 0, render_opt.cover_alpha))
        self.bg = None if illustration_path == "" else sdl_image.open_image(illustration_path, self.window.renderer,
                                                                            (2048, 1080))

        if self.bg is not None:
            old = self.bg
            self.bg = old.crop_to_fit(render_opt.width / render_opt.height)
            old.destroy()

        self.real_time = 0
        self.fps = render_opt.fps
        self.effect_sound_player = hit_effect_player(init_chart.notes)

        render_opt = copy.copy(render_opt)
        if super_sampling:
            render_opt.width *= 2
            render_opt.height *= 2
        for line in init_chart.lines:
            self.judge_line_renderer_list.append(judge_line_renderer(line, self.window, render_opt))

    def render_frame(self):
        self.window.renderer.clear()
        self.effect_sound_player.play_time_less_than(self.real_time)
        if self.bg is not None:
            self.bg.tex.direct_copy_to_parent()
            self.cover.draw_cover()
        for line_renderer in self.judge_line_renderer_list:
            line_renderer.render_line()

        for line_renderer in self.judge_line_renderer_list:
            line_renderer.advance_frame()
        self.real_time += 1 / self.fps
