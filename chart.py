"""
This module provides several types and functions to access Phigros chart.

"""

import json
import copy

NOTE_TYPE_TAP = 1
NOTE_TYPE_DRAG = 2
NOTE_TYPE_HOLD = 3
NOTE_TYPE_FLICK = 4

NOTE_DIRECTION_NORMAL = 0
NOTE_DIRECTION_REVERSED = 1

__all__ = ["NOTE_TYPE_TAP", "NOTE_TYPE_FLICK", "NOTE_TYPE_HOLD", "NOTE_TYPE_DRAG",
           "speed_event", "phi_move_event", "phi_note", "phi_chart", "phi_event_base",
           "phi_judge_line", "phi_rotate_event", "phi_ver3_event_base", "phi_disappear_event",
           "open_chart_file", "open_chart_string"]


class speed_event:
    __slots__ = ("start_time", "end_time", "floor_position", "value", "real_start_time", "real_end_time")

    def __init__(self, start_tm: float, end_tm: float, floor_pos: float, value: float, bpm: float):
        self.start_time = start_tm
        self.end_time = end_tm
        self.floor_position = floor_pos
        self.value = value
        self.real_start_time = start_tm * 1.875 / bpm
        self.real_end_time = end_tm * 1.875 / bpm

    def is_real_time_valid(self, real_time: float) -> bool:
        return self.real_start_time <= real_time < self.real_end_time

    def get_value_unchecked(self, real_time: float) -> float:
        return (real_time - self.real_start_time) * self.value + self.floor_position


class phi_event_base:
    """Represents a basic Phigros event."""
    __slots__ = ("start", "end", "start_time", "end_time", "real_start_time", "real_end_time")

    def __init__(self, start: float, end: float, start_tm: float, end_tm: float, bpm: float):
        self.start_time = start_tm
        self.end_time = end_tm
        self.start = start
        self.end = end
        self.real_start_time = start_tm * 1.875 / bpm
        self.real_end_time = end_tm * 1.875 / bpm

    def is_real_time_valid(self, real_time: float) -> bool:
        """
        Verify whether given time is in range.\n
        :param real_time: The real time in seconds to check.
        :return: A bool value. True if the time is valid; false otherwise.
        """
        return self.real_start_time <= real_time < self.real_end_time

    def get_value_unchecked(self, real_time: float) -> float:
        t2 = (real_time - self.real_start_time) / (self.real_end_time - self.real_start_time)
        t1 = 1 - t2
        return self.start * t1 + self.end * t2


class phi_ver3_event_base(phi_event_base):
    """Represents a Phigros event with new format."""
    __slots__ = ("start2", "end2")

    def __init__(self, start: float, end: float, start2: float, end2: float, start_tm: float, end_tm: float,
                 bpm: float):
        super(phi_ver3_event_base, self).__init__(start, end, start_tm, end_tm, bpm)
        self.start2 = start2
        self.end2 = end2

    def get_value_unchecked(self, real_time: float) -> tuple[float, float]:
        t2 = (real_time - self.real_start_time) / (self.real_end_time - self.real_start_time)
        t1 = 1 - t2
        return self.start * t1 + self.end * t2, 1 - self.start2 * t1 - self.end2 * t2


class phi_move_event(phi_ver3_event_base):
    """
    Represents a judge line movement event, indicating how the center of judge line moves.\n
    This event uses format 3.
    """
    def __init__(self, start: float, end: float, start2: float, end2: float, start_tm: float, end_tm: float,
                 bpm: float):
        super(phi_move_event, self).__init__(start, end, start2, end2, start_tm, end_tm, bpm)


class phi_rotate_event(phi_event_base):
    """
    Represents a judge line rotation event, indicating how the judge line rotates.\n
    This event uses format 1.
    """
    def __init__(self, start: float, end: float, start_tm: float, end_tm: float,
                 bpm: float):
        super(phi_rotate_event, self).__init__(start, end, start_tm, end_tm, bpm)


class phi_disappear_event(phi_event_base):
    """
    Represents a judge line alpha event, indicating whether the judge line is transparent.\n
    This event uses format 1.
    """
    def __init__(self, start: float, end: float, start_tm: float, end_tm: float,
                 bpm: float):
        super(phi_disappear_event, self).__init__(start, end, start_tm, end_tm, bpm)


class phi_note:
    """Represents a note structure."""
    __slots__ = ("multi_highlight", "time", "note_type", "floor_position", "speed", "position_x", "hold_time",
                 "real_hold_time", "real_time")

    def __init__(self, tm: int, note_ty: int, floor_pos: float, speed: float,
                 pos_x: float, hold_tm: float, bpm: float, direction: int):
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
            rearranged_events.append(ev)
            continue
        last.end_time = ev.end_time
        rearranged_events[-1] = ev
    for ev in rearranged_events:
        ev.real_start_time = ev.start_time * 1.875 / bpm
        ev.real_end_time = ev.end_time * 1.875 / bpm
    return rearranged_events


def get_speed_events_from_dict(content: dict, chart_ver: int):
    """Extracts speed events from judge line content. Chart version is required for parsing pattern determination."""
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
    """Extracts events of old format (version 1). Event type should be specified manually."""
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
    """Loads old style movement events."""
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
    """Gets all movement events from json list. Chart version is required to match parsing pattern."""
    if chart_ver != 3:
        # load version 1 events.
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


def get_notes(line_content: dict[str, list], list_name: str, bpm: float):
    """Extracts note events from line content."""
    data_list: list[dict] = line_content[list_name]
    note_list: list[phi_note] = []

    note_direction = NOTE_DIRECTION_NORMAL if list_name == "notesAbove" else NOTE_DIRECTION_REVERSED

    for ev_note in data_list:
        tm = ev_note["time"]
        floor_pos = ev_note["floorPosition"]
        pos_x = ev_note["positionX"]
        ty = ev_note["type"]
        hold_tm = ev_note["holdTime"]
        speed = ev_note["speed"]

        note_list.append(phi_note(tm, ty, floor_pos, speed, pos_x, hold_tm, bpm, note_direction))
    note_list.sort(key=lambda x: x.time, reverse=False)
    return note_list


class phi_judge_line:
    """Represents a judge line structure."""
    __slots__ = ("content", "speed_events", "move_events", "rotate_events", "disappear_events", "notes_above",
                 "notes_below", "num_notes_above", "num_notes_below", "num_notes", "chart_version",
                 "offset", "index", "bpm")

    def __init__(self, content: dict, index: int, chart_ver: int):
        """
        Initializes a new judge line structure.\n
        :param content: The dict extracted from the json chart, containing judge line information.
        :param index: The index to this judge line, which determines the render order.
        :param chart_ver: Chart version.
        """
        self.content = content
        self.index: int = index
        self.chart_version = chart_ver
        self.bpm: float = content["bpm"]
        self.num_notes: int = content["numOfNotes"]
        self.num_notes_above: int = max(content["numOfNotesAbove"], 0)
        self.num_notes_below: int = max(content["numOfNotesBelow"], 0)
        self.speed_events = get_speed_events_from_dict(content, chart_ver)
        self.rotate_events: list[phi_rotate_event] = get_typed_ver1_events(
            content["judgeLineRotateEvents"], phi_rotate_event, self.bpm
        )
        self.disappear_events: list[phi_disappear_event] = get_typed_ver1_events(
            content["judgeLineDisappearEvents"], phi_disappear_event, self.bpm
        )
        self.move_events = get_movement_events(content["judgeLineMoveEvents"], chart_ver, self.bpm)
        self.notes_above: list[phi_note] = get_notes(content, "notesAbove", self.bpm)
        self.notes_below: list[phi_note] = get_notes(content, "notesBelow", self.bpm)


class phi_chart:
    """Represents a chart structure."""
    __slots__ = ("content", "version", "offset", "numOfNotes", "lines", "notes")

    def __init__(self, content: dict):
        """
        Initializes a new chart object with specified dictionary extracted from json.
        :param content: The dictionary containing chart data.
        """
        self.content: dict = content
        self.version: int = content["formatVersion"]
        self.offset: float = content["offset"]
        self.numOfNotes: int = content["numOfNotes"]
        self.lines: list[phi_judge_line] = list[phi_judge_line]()
        line_id = 0
        for data in content["judgeLineList"]:
            self.lines.append(phi_judge_line(data, line_id, self.version))
            line_id += 1
        self.notes: list[phi_note] = []
        for line in self.lines:
            self.notes += line.notes_above
            self.notes += line.notes_below
        self.notes.sort(key=lambda x: x.real_time, reverse=False)

        # creates a <time - note list> map to identify what notes should be highlighted.
        tm_map: dict[float, list[phi_note]] = {}
        for n in self.notes:
            tm = round(n.real_time, 6)
            if tm not in tm_map.keys():
                tm_map[tm] = [n, ]
            else:
                tm_map[tm].append(n)
        for v in tm_map.values():
            if len(v) > 1:
                # there are more than 1 notes being hit at the same time. mark them.
                for n in v:
                    # we only need to set this field this time.
                    # for python always passes object reference.
                    n.multi_highlight = True


def open_chart_file(file_name: str) -> phi_chart:
    """Opens a chart file, initializes a new chart instance with the file content and returns the chart object."""
    with open(file_name) as file_stream:
        json_data = json.load(file_stream)
    return phi_chart(json_data)


def open_chart_string(json_string: str) -> phi_chart:
    """Converts the json string to a dictionary, and returns a new chart instance with it."""
    return phi_chart(eval(json_string))
