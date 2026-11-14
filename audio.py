import array
import math

import pygame


class Audio:
    def __init__(self):
        self.enabled = False
        self.music_channel = None
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            pygame.mixer.set_num_channels(8)
            self.sounds = {
                "dot": self._tone(560, 0.055, 0.22),
                "power": self._tone(280, 0.32, 0.28, rising=True),
                "eat": self._tone(760, 0.19, 0.24, rising=True),
                "death": self._tone(420, 0.65, 0.22, rising=False),
                "win": self._tone(620, 0.7, 0.2, rising=True),
            }
            self.music = self._music_loop()
            self.music_channel = pygame.mixer.Channel(7)
            self.enabled = True
        except pygame.error as exc:
            print(f"Audio disabled: {exc}")

    @staticmethod
    def _tone(frequency, duration, volume, rising=False):
        sample_rate = 22050
        samples = array.array("h")
        for index in range(int(sample_rate * duration)):
            progress = index / (sample_rate * duration)
            freq = frequency * (1 + progress if rising else 1 - progress * 0.65)
            envelope = min(1.0, progress * 18) * (1 - progress) ** 0.7
            samples.append(int(32767 * volume * envelope *
                               math.sin(math.tau * freq * index / sample_rate)))
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def _music_loop(self):
        sample_rate = 22050
        notes = (110, 147, 165, 147, 123, 165, 185, 165)
        beat = 0.24
        samples = array.array("h")
        for note in notes:
            for index in range(int(sample_rate * beat)):
                t = index / sample_rate
                envelope = min(1.0, t * 20) * max(0.0, 1 - t / beat)
                tone = math.sin(math.tau * note * t) + 0.35 * math.sin(math.tau * note * 2 * t)
                samples.append(int(32767 * 0.10 * envelope * tone))
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def play(self, name):
        if self.enabled and name in self.sounds:
            self.sounds[name].play()

    def set_volume(self, value):
        if not self.enabled:
            return
        for sound in self.sounds.values():
            sound.set_volume(value)
        self.music.set_volume(value * 0.35)
        if self.music_channel:
            self.music_channel.set_volume(value * 0.35)

    def start_music(self):
        if self.enabled and self.music_channel and not self.music_channel.get_busy():
            self.music_channel.play(self.music, loops=-1)
