import json
import copy

NOTE_TYPE_TAP = 1
NOTE_TYPE_DRAG = 2
NOTE_TYPE_HOLD = 3
NOTE_TYPE_FLICK = 4


class speed_event:
    __slots__ = ("start_time", "end_time", "floor_position", "value", "real_start_time", "real_end_time")

    def __init__(self, start_tm: float, end_tm: float, floor_pos: float, value: float, bpm: float):
        self.start_time = start_tm
        self.end_time = end_tm
        self.floor_position = floor_pos
        self.value = value
        self.real_start_time = start_tm * 1.875 / bpm
        self.real_end_time = end_tm * 1.875 / bpm


class phi_event_base:
    __slots__ = ("start", "end", "start_time", "end_time", "real_start_time", "real_end_time")

    def __init__(self, start: float, end: float, start_tm: float, end_tm: float, bpm: float):
        self.start_time = start_tm
        self.end_time = end_tm
        self.start = start
        self.end = end
        self.real_start_time = start_tm * 1.875 / bpm
        self.real_end_time = end_tm * 1.875 / bpm


class phi_ver3_event_base(phi_event_base):
    __slots__ = ("start2", "end2")

    def __init__(self, start: float, end: float, start2: float, end2: float, start_tm: float, end_tm: float,
                 bpm: float):
        super(phi_ver3_event_base, self).__init__(start, end, start_tm, end_tm, bpm)
        self.start2 = start2
        self.end2 = end2


class phi_move_event(phi_ver3_event_base):
    def __init__(self, start: float, end: float, start2: float, end2: float, start_tm: float, end_tm: float,
                 bpm: float):
        super(phi_move_event, self).__init__(start, end, start2, end2, start_tm, end_tm, bpm)


class phi_rotate_event(phi_event_base):
    def __init__(self, start: float, end: float, start_tm: float, end_tm: float,
                 bpm: float):
        super(phi_rotate_event, self).__init__(start, end, start_tm, end_tm, bpm)


class phi_disappear_event(phi_event_base):
    def __init__(self, start: float, end: float, start_tm: float, end_tm: float,
                 bpm: float):
        super(phi_disappear_event, self).__init__(start, end, start_tm, end_tm, bpm)


class phi_note:
    __slots__ = ("multi_highlight", "time", "note_type", "floor_position", "speed", "position_x", "hold_time",
                 "real_hold_time", "real_time")

    def __init__(self, tm: int, note_ty: int, floor_pos: float, speed: float,
                 pos_x: float, hold_tm: float, bpm: float):
        self.multi_highlight = False
        self.time = tm
        self.note_type = note_ty
        self.floor_position = floor_pos
        self.speed = speed
        self.position_x = pos_x
        self.hold_time = hold_tm
        self.real_hold_time = hold_tm * 1.875 / bpm
        self.real_time = tm * 1.875 / bpm


def rearrange_speed_events(resolved_events: list[speed_event], bpm: float):
    rearranged_events = list[speed_event]()
    for ev in resolved_events:
        if len(rearranged_events) == 0:
            rearranged_events.append(ev)
            continue
        last = copy.copy(rearranged_events[-1])
        if last.value != ev.value:
            resolved_events.append(ev)
            continue
        last.end_time = ev.end_time
        rearranged_events[-1] = ev
    for ev in rearranged_events:
        ev.real_start_time = ev.start_time * 1.875 / bpm
        ev.real_end_time = ev.end_time * 1.875 / bpm
    return rearranged_events


def get_speed_events_from_dict(content: dict, chart_ver: int):
    """Extracts speed events from judge line content"""
    bpm: float = content["bpm"]
    ev_list: list[dict] = content["speedEvents"]
    ret = list[speed_event]()
    y = 0.0

    for ev in ev_list:
        start_tm = max(ev["startTime"], 0)
        end_tm = ev["endTime"]
        value = ev["value"]

        if chart_ver == 3:  # most possible
            floor_pos = ev["floorPosition"]
        else:
            floor_pos = y
            y += (end_tm - start_tm) * value * 1.875 / bpm
        ret.append(speed_event(start_tm, end_tm, floor_pos, value, bpm))

    if chart_ver != 3:
        ret = rearrange_speed_events(ret, bpm)

    return ret


def rearrange_ver1_events(ev_list: list, ev_type: type, bpm: float):
    old_events = copy.copy(ev_list)
    new_events = list[ev_type]()
    new_events.append(ev_type(0 if len(old_events) == 0 else old_events[0].start,
                              0 if len(old_events) == 0 else old_events[0].end,
                              1 - 1e6, 0, bpm))
    for old_ev in old_events:
        ev = new_events[-1]
        if ev.end_time == old_ev.start_time:
            new_events.append(old_ev)
            continue
        if ev.end_time < old_ev.start_time:
            new_events.append(ev_type(ev.end, ev.end, ev.end_time, old_ev.start_time, bpm))
        else:
            new_events.append(ev_type(
                (old_ev.start * (old_ev.end_time - ev.end_time) +
                 old_ev.end * (ev.end_time - old_ev.start_time)) / (old_ev.end_time - old_ev.start_time),
                ev.end,
                ev.end_time,
                old_ev.end_time,
                bpm
            ))

    return new_events


def rearrange_move_events(ev_list: list[phi_move_event], bpm: float):
    old_events = copy.copy(ev_list)
    new_events = list[phi_move_event]()
    is_old_events_empty: bool = len(old_events) == 0
    new_events.append(phi_move_event(0 if is_old_events_empty else old_events[0].start,
                                     0 if is_old_events_empty else old_events[0].end,
                                     0 if is_old_events_empty else old_events[0].start2,
                                     0 if is_old_events_empty else old_events[0].end2,
                                     1 - 1e6, 0, bpm))
    for old_ev in old_events:
        ev = new_events[-1]
        if ev.end_time == old_ev.start_time:
            new_events.append(old_ev)
            continue
        if ev.end_time < old_ev.start_time:
            new_events.append(phi_move_event(ev.end, ev.end, ev.end2, ev.end2, ev.end_time, old_ev.start_time, bpm))
        else:
            new_events.append(phi_move_event(
                (old_ev.start * (old_ev.end_time - ev.end_time) +
                 old_ev.end * (ev.end_time - old_ev.start_time)) / (old_ev.end_time - old_ev.start_time),
                ev.end,
                (old_ev.start2 * (old_ev.end_time - ev.end_time) +
                 old_ev.end2 * (ev.end_time - old_ev.start_time)) / (old_ev.end_time - old_ev.start_time),
                ev.end2,
                ev.end_time,
                old_ev.end_time,
                bpm
            ))

    return new_events


def get_typed_ver1_events(content: list, ev_type: type, bpm: float):
    """Extracts events of old format (version 1)."""
    ret = list[ev_type]()

    for ev in content:
        start_tm = ev["startTime"]
        end_tm = ev["endTime"]
        start = ev["start"]
        end = ev["end"]

        ret.append(ev_type(start, end, start_tm, end_tm, bpm))

    ret = rearrange_ver1_events(ret, ev_type, bpm)
    return ret


def load_old_move_events(content: list, bpm: float):
    ret = list[phi_move_event]()

    for ev in content:
        start = ev["start"]
        end = ev["end"]
        start_tm = ev["startTime"]
        end_tm = ev["endTime"]
        start2 = start % 1e3 / 520
        end2 = end % 1e3 / 520
        start = start / 1e3 / 880
        end = end / 1e3 / 880

        ret.append(phi_move_event(start, end, start2, end2, start_tm, end_tm, bpm))
    return rearrange_move_events(ret, bpm)


def get_movement_events(content: list, chart_ver: int, bpm: float):
    if chart_ver != 3:
        return load_old_move_events(content, bpm)

    ret = list[phi_move_event]()

    for ev in content:
        start = ev["start"]
        end = ev["end"]
        start_tm = ev["startTime"]
        end_tm = ev["endTime"]
        start2 = ev["start2"]
        end2 = ev["end2"]

        ret.append(phi_move_event(start, end, start2, end2, start_tm, end_tm, bpm))

    return ret


class phi_judge_line:
    __slots__ = ("content", "speedEvents", "moveEvents", "rotateEvents", "disappearEvents", "notesAbove",
                 "notesBelow", "notes", "numOfNotesAbove", "numOfNotesBelow", "numOfNotes", "chartVersion",
                 "offset", "index", "bpm")

    def __init__(self, content: dict, index: int, chart_ver: int):
        self.content = content
        self.index: int = index
        self.chartVersion = chart_ver
        self.bpm: float = content["bpm"]
        self.numOfNotes: int = content["numOfNotes"]
        self.numOfNotesAbove: int = max(content["numOfNotesAbove"], 0)
        self.numOfNotesBelow: int = max(content["numOfNotesBelow"], 0)
        self.speedEvents = get_speed_events_from_dict(content, chart_ver)
        self.rotateEvents: list[phi_rotate_event] = get_typed_ver1_events(
            content["judgeLineRotateEvents"], phi_rotate_event, self.bpm
        )
        self.disappearEvents: list[phi_disappear_event] = get_typed_ver1_events(
            content["judgeLineDisappearEvents"], phi_disappear_event, self.bpm
        )
        self.moveEvents = get_movement_events(content["judgeLineMoveEvents"], chart_ver, self.bpm)


class phi_chart:
    __slots__ = ("content", "version", "offset", "numOfNotes", "lines")

    def __init__(self, content: dict):
        self.content: dict = content
        self.version: int = content["formatVersion"]
        self.offset: float = content["offset"]
        self.numOfNotes: int = content["numOfNotes"]
