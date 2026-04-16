import os

import pygame

class SoundManager:

    _PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    SFX_DIR            = os.path.join(_PROJECT_ROOT, "assets", "sfx")
    MUSIC_DIR          = os.path.join(_PROJECT_ROOT, "assets", "music")
    DEFAULT_THROTTLE_MS = 60

    def __init__(self):
        self._sounds:      dict[str, pygame.mixer.Sound] = {}
        self._last_played: dict[str, int] = {}
        self._missing:     set[str] = set()
        self._initialized  = False

        self._throttle_ms  = self.DEFAULT_THROTTLE_MS
        self._sfx_volume   = 0.7
        self._music_volume = 0.5

    # ------------------------------------------------------------------ #
    #  SFX
    # ------------------------------------------------------------------ #

    def play(self, name: str, volume: float | None = None):
        """
        Play a sound effect by name.

        Maps name → assets/sfx/{name}.ogg
        Throttled: same name won't replay within throttle_ms.
        Missing files log a warning once, never crash.
        """
        self._ensure_init()

        now = pygame.time.get_ticks()
        if name in self._last_played:
            if now - self._last_played[name] < self._throttle_ms:
                return

        snd = self._load(name)
        if snd is None:
            return

        vol = volume if volume is not None else self._sfx_volume
        snd.set_volume(vol)
        snd.play()
        self._last_played[name] = now

    # ------------------------------------------------------------------ #
    #  Music
    # ------------------------------------------------------------------ #

    def play_music(self, name: str, fade_ms: int = 1000, loops: int = -1):
        """
        Start background music with fade-in.

        Maps name → assets/music/{name}.ogg
        loops=-1 means infinite loop.
        """
        self._ensure_init()

        path = os.path.join(self.MUSIC_DIR, f"{name}.ogg")
        if not os.path.isfile(path):
            if name not in self._missing:
                print(f"[SoundManager] Music not found: {path}")
                self._missing.add(f"music:{name}")
            return

        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(self._music_volume)
        pygame.mixer.music.play(loops, fade_ms=fade_ms)

    def stop_music(self, fade_ms: int = 500):
        """Stop current music with fade-out."""
        self._ensure_init()
        pygame.mixer.music.fadeout(fade_ms)

    # ------------------------------------------------------------------ #
    #  Volume
    # ------------------------------------------------------------------ #

    def set_sfx_volume(self, vol: float):
        self._sfx_volume = max(0.0, min(1.0, vol))

    def set_music_volume(self, vol: float):
        self._music_volume = max(0.0, min(1.0, vol))
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(self._music_volume)

    # ------------------------------------------------------------------ #
    #  Internals
    # ------------------------------------------------------------------ #

    def _ensure_init(self):
        """Lazy-init mixer on first use."""
        if self._initialized:
            return
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.set_num_channels(16)
        self._initialized = True

    def _load(self, name: str) -> pygame.mixer.Sound | None:
        """Load and cache a sound. Returns None if missing."""
        if name in self._sounds:
            return self._sounds[name]

        if name in self._missing:
            return None

        path = os.path.join(self.SFX_DIR, f"{name}.ogg")
        if not os.path.isfile(path):
            print(f"[SoundManager] SFX not found: {path}")
            self._missing.add(name)
            return None

        try:
            snd = pygame.mixer.Sound(path)
            self._sounds[name] = snd
            return snd
        except pygame.error as e:
            print(f"[SoundManager] Failed to load {path}: {e}")
            self._missing.add(name)
            return None


sound = SoundManager()