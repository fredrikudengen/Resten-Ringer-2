import pygame


class AfterimageTrail:
    """Blekende etterbilder bak en sprite i rask bevegelse (fiendens lunge, spillerens dash).

    Eieren kaller update() hver frame med om effekten er aktiv, og draw() før den tegner
    seg selv, så etterbildene havner under spriten. Rent visuelt – påvirker ikke spillogikk.
    """

    def __init__(
        self,
        interval_ms: int = 30,
        lifetime_ms: int = 160,
        max_alpha: int = 150,
        tint: tuple[int, int, int] | None = (30, 30, 50),
    ):
        self.interval_ms = interval_ms   # ms mellom hvert etterbilde
        self.lifetime_ms = lifetime_ms   # hvor lenge et etterbilde lever før det er borte
        self.max_alpha = max_alpha       # alpha på et helt nytt etterbilde
        self.tint = tint                 # lett kald tone så de skiller seg fra selve spriten
        self._ghosts: list[tuple[tuple[int, int], int, str, bool]] = []  # (senter, tid, frame, flip_x)
        self._last_record = -10**9

    def update(self, active: bool, center: tuple[int, int], frame: str, flip_x: bool, now: int):
        if active and now - self._last_record >= self.interval_ms:
            self._ghosts.append((tuple(center), now, frame, flip_x))
            self._last_record = now
        self._ghosts = [g for g in self._ghosts if now - g[1] < self.lifetime_ms]

    def draw(self, screen, camera, sprite, size: tuple[int, int], now: int):
        for center, born, frame, flip_x in self._ghosts:
            alpha = int(self.max_alpha * (1 - (now - born) / self.lifetime_ms))
            if alpha <= 0:
                continue
            rect = pygame.Rect(0, 0, *size)
            rect.center = center
            sprite.draw(
                screen, camera.apply(rect), frame=frame, flip_x=flip_x,
                tint=self.tint, alpha=alpha, moving=False,
            )

    def __len__(self):
        return len(self._ghosts)
