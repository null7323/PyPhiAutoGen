import sdl2
from sdl2.sdlmixer import *


__all__ = ["audio_file", ]


class audio_file:
    __slots__ = ("sound_object", )

    def __init__(self, sound_ptr):
        self.sound_object = sound_ptr

    @classmethod
    def init(cls):
        Mix_OpenAudio(48000, sdl2.AUDIO_U16, 2, 256)
        Mix_AllocateChannels(28)

    @classmethod
    def close(cls):
        Mix_CloseAudio()

    @classmethod
    def open_wav_file(cls, file_path: str):
        ptr = Mix_LoadWAV(file_path.encode("utf-8"))
        return cls(ptr)

    def async_play(self):
        Mix_PlayChannel(-1, self.sound_object, 0)
