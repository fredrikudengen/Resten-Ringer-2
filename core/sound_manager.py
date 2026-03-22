import pygame

class SoundManager:

    def __init__(self):
        """Initializes the sound manager."""

    def play(self, name):
        """Plays a single sound.
        params:
            sound_name: name of the sound.
        """
        print(f"[SFX] {name}")

    def play_music(self, name):
        """Plays the looping background soundtrack.
        params:
        sound_name: name of the soundtrack name."""
        pass

    def stop_music(self):
        """Stops the playing the background music."""
        pass

sound = SoundManager()