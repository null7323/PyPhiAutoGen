import sdl2
from sdl2.sdlmixer import *


__all__ = ["audio_file", ]


class audio_file:
    __slots__ = ("sound_object", "currently_used_channel")

    def __init__(self, sound_ptr):
        self.sound_object = sound_ptr
        self.currently_used_channel: int = -1

    @classmethod
    def init(cls):
        Mix_OpenAudio(48000, sdl2.AUDIO_S16, 2, 256)
        Mix_AllocateChannels(40)

    @classmethod
    def close(cls):
        Mix_CloseAudio()

    @classmethod
    def open_wav_file(cls, file_path: str):
        ptr = Mix_LoadWAV(file_path.encode("utf-8"))
        return cls(ptr)

    def async_play(self):
        self.currently_used_channel = Mix_PlayChannel(-1, self.sound_object, 0)
