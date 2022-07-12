from sdl2.sdlmixer import *

__all__ = ["pcm_u16_48khz_wave_audio", ]


class pcm_u16_48khz_wave_audio:
    __slots__ = ("sound_object", )

    @classmethod
    def open_audio(cls):
        Mix_OpenAudio(48000, MIX_DEFAULT_FORMAT, 2, 2048)

    @classmethod
    def close_audio(cls):
        Mix_CloseAudio()

    def __init__(self, sound_ptr):
        self.sound_object = sound_ptr

    @classmethod
    def open_wav(cls, file_path: str):
        sound_object = Mix_LoadMUS(file_path.encode("ascii"))
        return cls(sound_object)

    def async_play(self):
        Mix_PlayMusic(self.sound_object, 1)

    def destroy(self):
        Mix_FreeMusic(self.sound_object)

    @classmethod
    def is_playing_any(cls):
        return Mix_PlayingMusic()
