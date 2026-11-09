import pygame

from src.view.asset_manager import assets


class AimArm:
    """Arm med våpen som roteres rundt skulderen mot et siktepunkt (spilleren og skytende fiender).

    Alle koordinater er i kildepiksler og ganges med `scale`:
      shoulder : skulderpunktet i eierens sprite, målt fra sprite-sentrum (eier vendt mot høyre)
      pivot    : punktet i arm-spriten som festes i skulderen
      muzzle   : munningen i arm-spriten (der kulene kommer ut)
    Vinkler er grader mot klokka fra høyre (math-konvensjon, y opp), som Player.aim_angle.
    """

    def __init__(self, path: str, scale: float, pivot: tuple[float, float],
                 muzzle: tuple[float, float], shoulder: tuple[float, float] = (0, 0)):
        self.path = path
        self.scale = scale
        self.pivot = pivot
        self.muzzle_px = muzzle
        self.shoulder_px = shoulder
        self._surface: pygame.Surface | None = None  # lastes lazily

    def shoulder(self, center: tuple[float, float], flip_x: bool) -> tuple[float, float]:
        sx = self.shoulder_px[0] * self.scale
        sy = self.shoulder_px[1] * self.scale
        return (center[0] - sx if flip_x else center[0] + sx, center[1] + sy)

    def muzzle(self, shoulder_pos: tuple[float, float], angle: float, flip_x: bool) -> tuple[int, int]:
        s = self.scale
        # Munningen relativt til pivot, med y opp. Speiles vertikalt når armen er flippet
        dx = (self.muzzle_px[0] - self.pivot[0]) * s
        dy = (self.pivot[1] - self.muzzle_px[1]) * s
        offset = pygame.math.Vector2(dx, -dy if flip_x else dy).rotate(angle)
        return (int(shoulder_pos[0] + offset.x), int(shoulder_pos[1] - offset.y))

    def draw(self, screen, shoulder_pos: tuple[float, float], angle: float, flip_x: bool,
             tint: tuple[int, int, int] | None = None):
        if self._surface is None:
            raw = assets.get(self.path)
            if raw is None:
                return
            self._surface = pygame.transform.scale(
                raw, (int(raw.get_width() * self.scale), int(raw.get_height() * self.scale))
            )

        arm = self._surface
        W, H = arm.get_size()
        pivot_x = self.pivot[0] * self.scale
        pivot_y = self.pivot[1] * self.scale

        if flip_x:
            arm = pygame.transform.flip(arm, False, True)
            pivot_y = H - pivot_y  # speil pivot_y etter vertikal flip
        if tint is not None:
            arm = arm.copy()
            arm.fill(tint, special_flags=pygame.BLEND_RGB_ADD)
        rotated = pygame.transform.rotate(arm, angle)

        pivot_offset = pygame.math.Vector2(pivot_x - W / 2, pivot_y - H / 2)
        rotated_offset = pivot_offset.rotate(-angle)

        center = (
            shoulder_pos[0] - rotated_offset.x,
            shoulder_pos[1] - rotated_offset.y,
        )
        screen.blit(rotated, rotated.get_rect(center=center))
