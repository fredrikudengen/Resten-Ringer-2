import pygame

class SoundManager:

    def __init__(self):
        """Initialiserer sound manager."""

    def play(self, name):
        print(f"[SFX] {name}")

    def play_music(self, name):
        pass

    def stop_music(self):
        pass

sound = SoundManager()