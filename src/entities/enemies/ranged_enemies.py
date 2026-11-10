from __future__ import annotations

import math
import random

import pygame
from pygame.math import Vector2

from src.core import constants, debug
from src.view.sprite import Sprite
from src.view.aim_arm import AimArm
from src.view.aim_arm import AimArm
from src.entities.enemies.enemy import Enemy
from src.components.gun import EnemyPistol


# ---------------------------------------------------------------------------
# Stat referanse
# ---------------------------------------------------------------------------
# 1 tile = 96px
# Spiller synsbredde ~20 tiles (10 på hver side)
# i px 1920 (dette kommer an på brukerens skjermstørrelse)
# Spiller synshøyde ~11 tiles (5 på hver side pluss i midten)
# i px 1080
# Fredrik hastighet = ~430
# ---------------------------------------------------------------------------

class RangedEnemy(Enemy):
    """
    Base class for enemies that shoot projectiles at the player.

    Subclass attributes to override
    --------------------------------
    gun_class          : Gun subclass to equip (default EnemyPistol)
    preferred_range_px : Ideal pixel distance to player while shooting (default 300)
    min_range_px       : Won't advance closer than this (default 140)
    reposition_interval: ms between LOS-position searches while chasing (default 800)
    strafe_speed_mult  : Andel av speed når den beveger seg sidelengs mens den skyter (0 = står stille)
    strafe_interval_ms : (min, max) ms per sidelengs-intervall før den velger side på nytt
    aim_error_deg      : Maks sikteavvik i grader. Driver litt fra skudd til skudd (i tillegg til gun.spread)
    arm_sprite         : Arm-sprite med våpen som sikter mot spilleren (None = ingen arm)
    arm_pivot / arm_muzzle : Skulderfeste og munning i arm-spritens kildepiksler
    arm_shoulder       : Skulderen i kropps-spriten, målt fra sprite-sentrum (vendt mot høyre)
    sprite_px          : Bredden på kropps-spriten i kildepiksler (for skalering av armen)
    arm_sprite         : Arm-sprite med våpen som sikter mot spilleren (None = ingen arm)
    arm_pivot / arm_muzzle : Skulderfeste og munning i arm-spritens kildepiksler
    arm_shoulder       : Skulderen i kropps-spriten, målt fra sprite-sentrum (vendt mot høyre)
    sprite_px          : Bredden på kropps-spriten i kildepiksler (for skalering av armen)
    """

    # ---- override these in subclasses ----
    gun_class:            type  = EnemyPistol
    preferred_range_px:   int   = 300
    min_range_px:         int   = 140
    reposition_interval:  int   = 800    # ms between reposition searches
    strafe_speed_mult:    float = 0.6
    strafe_interval_ms:   tuple = (400, 900)
    aim_error_deg:        float = 6.0
    arm_sprite:           str | None = None
    arm_pivot:            tuple = (0, 0)
    arm_muzzle:           tuple = (0, 0)
    arm_shoulder:         tuple = (0, 0)
    sprite_px:            int   = 32
    _RELAXED_ARM_DEG:     float = -30.0  # armen senket når den ikke sikter på noen
    arm_sprite:           str | None = None
    arm_pivot:            tuple = (0, 0)
    arm_muzzle:           tuple = (0, 0)
    arm_shoulder:         tuple = (0, 0)
    sprite_px:            int   = 32
    _RELAXED_ARM_DEG:     float = -30.0  # armen senket når den ikke sikter på noen

    # ---- sensible defaults (subclass can still override) ----
    speed            = 100
    health           = 70
    detection_radius = 700
    color            = (180, 100, 220)
    xp_reward        = 30
    width            = 38
    height           = 38
    wander_radius    = 5

    def __init__(self, x: int, y: int):
        super().__init__(x, y)
        self.gun              = self.gun_class()
        self.pending_bullets: list = []   # world.update() drains this each frame

        self._reposition_target: tuple[int, int] | None = None
        self._next_reposition_at: int = 0

        self._strafe_dir: int       = random.choice((-1, 1))
        self._strafe_switch_at: int = 0
        self._aim_offset_deg: float = 0.0
        self._aim_target: tuple[int, int] | None = None

        self.arm = None
        if self.arm_sprite:
            self.arm = AimArm(self.arm_sprite, scale=self.width / self.sprite_px,
                              pivot=self.arm_pivot, muzzle=self.arm_muzzle, shoulder=self.arm_shoulder)
        self._aim_target: tuple[int, int] | None = None

        self.arm = None
        if self.arm_sprite:
            self.arm = AimArm(self.arm_sprite, scale=self.width / self.sprite_px,
                              pivot=self.arm_pivot, muzzle=self.arm_muzzle, shoulder=self.arm_shoulder)

    # =========================================================
    # PUBLIC API — override of Enemy.move()
    # =========================================================

    def move(self, player, obstacles, room, dt_ms: int):
        self.gun.update_reload()  # reload går også mens fienden er død/ute av sikte
        super().move(player, obstacles, room, dt_ms)

    def _react_to_hit(self, player, now):
        """Husk hvor skuddet kom fra, men ikke avbryt det den holder på med."""
        if self.hit and self.state not in ("attack", "chase"):
            self.hit            = False
            self.last_seen_pos  = player.rect.center
            self.search_started = now

    def _sense(self, player, room) -> bool:
        see_player = super()._sense(player, room)
        self._aim_target = player.rect.center if see_player else None
        return see_player

    def _start_chase(self):
        super()._start_chase()
        self._reposition_target = None

    def _chase(self, player, obstacles, room, dt_ms, now):
        dist2 = self._dist2(*player.rect.center, *self.rect.center)
        self._do_chase(player, obstacles, room, dist2, dt_ms, now)

    def _update_special_state(self, player, obstacles, room, dt_ms, now, see_player):
        player_center = player.rect.center
        dist2 = self._dist2(*player_center, *self.rect.center)

        if self.state == "shoot":
            if not see_player:
                # Mistet sikte – finn en ny posisjon
                self._start_chase()
            elif self.gun.is_reloading:
                self.state = "reload"
            else:
                self._do_shoot(player_center)
                # Sidelengs mens den skyter, og trekk unna hvis spilleren er for nær
                self._strafe(player_center, obstacles, dt_ms, now,
                             retreat=dist2 < self.min_range_px ** 2)

        elif self.state == "reload":
            # Rygg litt mens den lader om, så den ikke virker passiv
            if see_player and dist2 < (self.preferred_range_px * 0.8) ** 2:
                self._retreat_from(player_center, obstacles, dt_ms)
            if not self.gun.is_reloading:
                self.state = "chase" if see_player else "search"

    def _update_facing(self):
        super()._update_facing()
        if self._aim_target is not None:
            # Se mot spilleren så lenge den sikter, ikke i strafe-retningen
            self.facing_left = self._aim_target[0] < self.rect.centerx

    # =========================================================
    # DRAW — extra colour coding for new states
    # =========================================================

    def draw(self, screen, camera):
        draw_rect = camera.apply(self.rect)

        if self.state != "dead":
            frame, tint = self._hurt_visual("idle")
            self.sprite.draw(screen, draw_rect, frame=frame, tint=tint, flip_x=self.facing_left)
            if self.arm is not None:
                shoulder = camera.apply_point(self._shoulder_world())
                self.arm.draw(screen, shoulder, self.aim_angle(), self.facing_left, tint=tint)
        if self.state != "dead":
            frame, tint = self._hurt_visual("idle")
            self.sprite.draw(screen, draw_rect, frame=frame, tint=tint, flip_x=self.facing_left)
            if self.arm is not None:
                shoulder = camera.apply_point(self._shoulder_world())
                self.arm.draw(screen, shoulder, self.aim_angle(), self.facing_left, tint=tint)

        # Draw reload progress bar above enemy
        if self.state == "reload":
            self._draw_reload_bar(screen, draw_rect)

        if self.state in ("idle", "walk") and self.wander_goal_g is not None:
            debug.draw_tile(screen, camera, self.wander_goal_g)

        if self._debug_los is not None:
            debug.draw_line(screen, camera, self.rect.center, self._debug_los)

        debug.draw_circle(screen, camera, self.rect.center, self.detection_radius)
        debug.draw_label(screen, camera, (self.rect.centerx, self.rect.top - 20), self.state)

        self._draw_healthbar(screen, camera)

    # =========================================================
    # PRIVATE HELPERS
    # =========================================================

    def _do_chase(self, player, obstacles, room, dist2: float, dt_ms: int, now: int):
        """
        Move to a position that has LOS to the player at preferred range.
        Transitions to "shoot" once we're in a good spot.
        """
        in_range = (self.min_range_px ** 2) <= dist2 <= (self.preferred_range_px * 1.6) ** 2

        if in_range and not self.gun.is_reloading:
            # Already in a good shooting position
            self.state              = "shoot"
            self._reposition_target = None
            return

        # Find / move toward a good position
        if self._reposition_target is None or now >= self._next_reposition_at:
            self._reposition_target  = self._find_los_tile(room, player)
            self._next_reposition_at = now + self.reposition_interval

        if self._reposition_target:
            target_px = self._center_of_tile(*self._reposition_target)
            reached   = self._move_towards(target_px, obstacles, dt_ms)
            if reached:
                self._reposition_target  = None
                self._next_reposition_at = now  # search again immediately
        else:
            # No good tile found — approach cautiously
            self._move_towards(player.rect.center, obstacles, dt_ms)

    def _shoulder_world(self) -> tuple[float, float]:
        """Skulderen (der armen roteres) i verdenskoordinater. Uten arm: sentrum."""
        if self.arm is None:
            return self.rect.center
        return self.arm.shoulder(self.rect.center, self.facing_left)

    def aim_angle(self) -> float:
        """Armens vinkel i grader mot klokka fra høyre, inkludert sikteavviket.

        Sikter mot spilleren når den ser ham, ellers senket i den retningen den vender.
        """
        if self._aim_target is None:
            return 180 - self._RELAXED_ARM_DEG if self.facing_left else self._RELAXED_ARM_DEG
        sx, sy = self._shoulder_world()
        base = math.degrees(math.atan2(-(self._aim_target[1] - sy), self._aim_target[0] - sx))
        # _aim_offset_deg roterer med klokka på skjermen (y ned), altså minus i math-vinkel
        return base - self._aim_offset_deg

    def _shoulder_world(self) -> tuple[float, float]:
        """Skulderen (der armen roteres) i verdenskoordinater. Uten arm: sentrum."""
        if self.arm is None:
            return self.rect.center
        return self.arm.shoulder(self.rect.center, self.facing_left)

    def aim_angle(self) -> float:
        """Armens vinkel i grader mot klokka fra høyre, inkludert sikteavviket.

        Sikter mot spilleren når den ser ham, ellers senket i den retningen den vender.
        """
        if self._aim_target is None:
            return 180 - self._RELAXED_ARM_DEG if self.facing_left else self._RELAXED_ARM_DEG
        sx, sy = self._shoulder_world()
        base = math.degrees(math.atan2(-(self._aim_target[1] - sy), self._aim_target[0] - sx))
        # _aim_offset_deg roterer med klokka på skjermen (y ned), altså minus i math-vinkel
        return base - self._aim_offset_deg

    def _do_shoot(self, player_center: tuple[int, int]):
        """Fire one bullet toward the player (respects gun fire rate).

        Med arm går kula ut fra munningen, i armens retning (skulder → spiller).
        """
        origin_x, origin_y = self._shoulder_world()
        """Fire one bullet toward the player (respects gun fire rate).

        Med arm går kula ut fra munningen, i armens retning (skulder → spiller).
        """
        origin_x, origin_y = self._shoulder_world()
        direction = Vector2(
            player_center[0] - origin_x,
            player_center[1] - origin_y,
            player_center[0] - origin_x,
            player_center[1] - origin_y,
        )
        if direction.length_squared() == 0 or not self.gun.can_shoot():
            return
        direction.rotate_ip(self._next_aim_offset())
        muzzle = self.rect.center
        if self.arm is not None:
            angle = math.degrees(math.atan2(-direction.y, direction.x))
            muzzle = self.arm.muzzle(self._shoulder_world(), angle, self.facing_left)
        bullets = self.gun.shoot(muzzle, direction)
        muzzle = self.rect.center
        if self.arm is not None:
            angle = math.degrees(math.atan2(-direction.y, direction.x))
            muzzle = self.arm.muzzle(self._shoulder_world(), angle, self.facing_left)
        bullets = self.gun.shoot(muzzle, direction)
        self.pending_bullets.extend(bullets)
        if self.gun.is_reloading:
            self.state = "reload"

    def _next_aim_offset(self) -> float:
        """Sikteavvik (grader) for neste skudd: random walk innenfor ±aim_error_deg.

        Avviket driver i stedet for å trekkes på nytt hver gang, så flere skudd
        på rad kan bomme til samme side, som et sikte som vingler.
        """
        e = self.aim_error_deg
        if e <= 0:
            return 0.0
        drifted = self._aim_offset_deg + random.uniform(-e, e) * 0.6
        self._aim_offset_deg = max(-e, min(e, drifted))
        return self._aim_offset_deg

    def _strafe(self, player_center: tuple[int, int], obstacles, dt_ms: int,
                now: int, retreat: bool = False):
        """Beveg seg sidelengs (vinkelrett på spilleren) i korte intervaller.

        Velger tilfeldig side ved hvert intervall og snur hvis den går i en vegg.
        Med retreat=True trekker den seg samtidig bort fra spilleren.
        """
        to_player = Vector2(player_center[0] - self.rect.centerx,
                            player_center[1] - self.rect.centery)
        if to_player.length_squared() < 1e-6:
            return
        to_player.normalize_ip()

        if now >= self._strafe_switch_at:
            self._strafe_dir       = random.choice((-1, 1))
            self._strafe_switch_at = now + random.randint(*self.strafe_interval_ms)

        side    = Vector2(-to_player.y, to_player.x) * self._strafe_dir
        desired = side * self.strafe_speed_mult
        if retreat:
            desired -= to_player
        if desired.length_squared() < 1e-6:
            return
        if desired.length() > 1:
            desired.scale_to_length(1)

        self._steer(desired.x * self.speed, desired.y * self.speed, dt_ms, obstacles)
        if self.velocity.length() < 1.0:
            self._strafe_dir *= -1  # blokkert av vegg – snu

    def _retreat_from(self, target_pos: tuple[int, int], obstacles, dt_ms: int):
        """Move away from target_pos (used to maintain min_range while reloading/shooting)."""
        away = Vector2(
            self.rect.centerx - target_pos[0],
            self.rect.centery - target_pos[1],
        )
        if away.length_squared() < 1e-6:
            return
        away = away.normalize()
        self._steer(away.x * self.speed, away.y * self.speed, dt_ms, obstacles)

    def _find_los_tile(self, room, player) -> tuple[int, int] | None:
        """
        Sample tiles at ~preferred_range from the player and return
        the closest one (to self) that has an unobstructed line-of-sight.

        Returns None if no suitable tile is found in this frame.
        """
        player_g  = player._grid_pos()
        my_g      = self._grid_pos()
        T         = constants.TILE_SIZE
        pref_g    = max(1, int(self.preferred_range_px / T))

        candidates: list[tuple[int, int]] = []

        # Sample tiles in an annulus around the player
        for _ in range(28):
            angle = random.uniform(0, math.tau)
            r     = random.uniform(pref_g * 0.55, pref_g * 1.45)
            gx    = int(player_g[0] + r * math.cos(angle))
            gy    = int(player_g[1] + r * math.sin(angle))
            if not room.is_blocked(gx, gy):
                candidates.append((gx, gy))

        # Prefer tiles closer to current position (less travel time)
        candidates.sort(
            key=lambda t: (t[0] - my_g[0]) ** 2 + (t[1] - my_g[1]) ** 2
        )

        for tile in candidates:
            if self._has_los(room, tile[0], tile[1], player_g[0], player_g[1]):
                return tile

        return None

    def _draw_reload_bar(self, screen, draw_rect: pygame.Rect):
        """Small white bar above the enemy showing reload progress."""
        bar_w  = draw_rect.width
        bar_h  = 4
        bar_x  = draw_rect.x
        bar_y  = draw_rect.y - 8

        progress = self.gun.reload_progress()
        filled_w = int(bar_w * progress)

        # Background
        pygame.draw.rect(screen, (50, 50, 60), (bar_x, bar_y, bar_w, bar_h))
        # Fill
        if filled_w > 0:
            pygame.draw.rect(screen, (180, 220, 255), (bar_x, bar_y, filled_w, bar_h))