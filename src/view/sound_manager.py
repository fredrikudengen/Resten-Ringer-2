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
        self._sfx_volume   = 0.1
        self._music_volume = 0.5

        # Music plays on a channel reserved at init so the SFX system
        # (which calls snd.play() without picking a channel) can never
        # steal it out from under the currently playing track.
        self._music_channel: pygame.mixer.Channel | None = None
        self._loop_sound:    pygame.mixer.Sound | None = None
        self._looping        = False

    # ------------------------------------------------------------------ #
    #  SFX
    # ------------------------------------------------------------------ #

    def play(self, name: str, volume: float | None = None):
        """
        Play a view effect by name.

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

    def play_music_with_intro(self, name: str, fade_ms: int = 1000):
        """
        Start background music that plays a one-shot intro before looping.

        Maps name → assets/music/{name}-intro.* (played once) followed by
        assets/music/{name}.* (looped forever). If no intro track exists,
        falls back to looping the main track directly.
        """
        self._ensure_init()

        loop = self._load_music(name)
        if loop is None:
            return

        self._looping = False
        self._music_channel.stop()

        intro = self._load_music(f"{name}-intro")
        if intro is not None:
            self._loop_sound = loop
            self._looping = True
            self._music_channel.play(intro, fade_ms=fade_ms)
            self._music_channel.queue(loop)
        else:
            self._music_channel.play(loop, loops=-1, fade_ms=fade_ms)

    def update(self):
        """
        Call once per frame. Re-queues the looping track whenever the
        channel's queue empties, keeping it playing indefinitely.
        """
        if self._looping and self._music_channel.get_queue() is None:
            self._music_channel.queue(self._loop_sound)

    def stop_music(self, fade_ms: int = 500):
        """Stop current music with fade-out."""
        self._ensure_init()
        self._looping = False
        self._music_channel.fadeout(fade_ms)

    # ------------------------------------------------------------------ #
    #  Volume
    # ------------------------------------------------------------------ #

    def set_sfx_volume(self, vol: float):
        self._sfx_volume = max(0.0, min(1.0, vol))

    def set_music_volume(self, vol: float):
        self._music_volume = max(0.0, min(1.0, vol))
        if self._music_channel is not None:
            self._music_channel.set_volume(self._music_volume)

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
        # Reserve channel 0 for music so pygame's automatic channel
        # allocation (used by snd.play() for SFX) never grabs it.
        pygame.mixer.set_reserved(1)
        self._music_channel = pygame.mixer.Channel(0)
        self._music_channel.set_volume(self._music_volume)
        self._initialized = True

    def _load(self, name: str) -> pygame.mixer.Sound | None:
        """Load and cache a view. Returns None if missing."""
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

    def _load_music(self, name: str) -> pygame.mixer.Sound | None:
        """Load and cache a music track. Returns None if missing."""
        key = f"music:{name}"
        if key in self._sounds:
            return self._sounds[key]

        if key in self._missing:
            return None

        for ext in (".wav", ".ogg"):
            path = os.path.join(self.MUSIC_DIR, f"{name}{ext}")
            if os.path.isfile(path):
                try:
                    snd = pygame.mixer.Sound(path)
                    self._sounds[key] = snd
                    return snd
                except pygame.error as e:
                    print(f"[SoundManager] Failed to load {path}: {e}")
                    self._missing.add(key)
                    return None

        print(f"[SoundManager] Music not found: {name}")
        self._missing.add(key)
        return None


sound = SoundManager()