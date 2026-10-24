import math
import random

from pygame.math import Vector2

from src.core import constants

class MovementMixin:

    accel_time_ms = constants.ENEMY_ACCEL_TIME_MS
    dir_noise_deg = constants.ENEMY_DIR_NOISE_DEG
    dir_noise_hz  = constants.ENEMY_DIR_NOISE_HZ

    # Burst-bevegelse (#22): hopp, pause, hopp. Av hvis en av fasene er 0.
    burst_move_ms  = 0
    burst_pause_ms = 0
    burst_jitter   = 0.25  # ±andel tilfeldig variasjon per fase

    # ---------- BURST ----------

    def _init_burst(self):
        """Kalles fra Enemy.__init__. Tilfeldig startpunkt i første hopp så fiender ikke hopper i takt."""
        self._burst_moving    = True
        self._burst_hops      = 0
        self._burst_phase_len = self._burst_phase_length(True) if self._bursting() else 1.0
        self._burst_left_ms   = self._burst_phase_len * random.random()

    def _bursting(self):
        return self.burst_move_ms > 0 and self.burst_pause_ms > 0

    def _burst_phase_length(self, moving):
        base = self.burst_move_ms if moving else self.burst_pause_ms
        if self.burst_jitter <= 0:
            return float(base)
        return base * random.uniform(1 - self.burst_jitter, 1 + self.burst_jitter)

    def _advance_burst(self, dt_ms):
        self._burst_left_ms -= dt_ms
        while self._burst_left_ms <= 0:
            self._burst_moving = not self._burst_moving
            if self._burst_moving:
                self._burst_hops += 1
            self._burst_phase_len = self._burst_phase_length(self._burst_moving)
            self._burst_left_ms += self._burst_phase_len

    def _burst_paused(self):
        return self._bursting() and not self._burst_moving

    def _gait_phase(self):
        """Gait-fase (0..1) synket med hoppet, eller None (Sprite bruker da klokka).

        Ett hopp = en halv gait-syklus = én sprett (|sin| går 0 → topp → 0).
        Annethvert hopp bruker andre halvdel, så sway/lean fortsetter jevnt.
        """
        if not self._bursting() or not self._burst_moving:
            return None
        progress = 1.0 - self._burst_left_ms / self._burst_phase_len
        progress = max(0.0, min(1.0, progress))
        return 0.5 * (self._burst_hops % 2) + 0.5 * progress

    # ---------- STEERING ----------

    def _direction_noise_deg(self, dt_ms, dist_to_target):
        """Sakte drivende vinkelavvik (grader) for målretningen.

        Sum av to sinuser med tilfeldig fase per fiende og ikke-rasjonelt
        frekvensforhold, så det ikke ser periodisk ut. Tones ned nær målet så
        fienden fortsatt treffer spilleren/waypoints presist.
        """
        if self.dir_noise_deg <= 0:
            return 0.0

        self._noise_t += dt_ms / 1000.0
        w = 2 * math.pi * self.dir_noise_hz
        p1, p2 = self._noise_phase
        raw = 0.6 * math.sin(w * self._noise_t + p1) + 0.4 * math.sin(w * 2.37 * self._noise_t + p2)

        T = constants.TILE_SIZE
        fade = max(0.0, min(1.0, (dist_to_target - 0.5 * T) / (1.5 * T)))
        return self.dir_noise_deg * raw * fade

    def _steer(self, desired_vx, desired_vy, dt_ms, obstacles):
        """Glid self.velocity mot ønsket hastighet med begrenset akselerasjon, og flytt.

        Gir buer når retningen endres og litt overshoot når målet snur.
        """
        self._steered = True
        desired = Vector2(desired_vx, desired_vy)

        if self.accel_time_ms <= 0:
            self.velocity = desired
        else:
            accel = self.speed / (self.accel_time_ms / 1000.0)
            max_delta = accel * dt_ms / 1000.0
            diff = desired - self.velocity
            if diff.length() > max_delta:
                diff.scale_to_length(max_delta)
            self.velocity += diff

        if desired.length_squared() == 0 and self.velocity.length() < 1.0:
            self.velocity.update(0, 0)
            return

        start_x, start_y = self.pos.x, self.pos.y
        self._slide_move(self.velocity.x, self.velocity.y, dt_ms, obstacles)

        # Nullstill aksen som ble blokkert av vegg, så farten ikke bygger seg opp inn i den
        dt = dt_ms / 1000.0
        if abs(self.velocity.x * dt) > 1e-6 and abs(self.pos.x - start_x) < 1e-6:
            self.velocity.x = 0
        if abs(self.velocity.y * dt) > 1e-6 and abs(self.pos.y - start_y) < 1e-6:
            self.velocity.y = 0

    def coast(self, obstacles, dt_ms):
        """Kalles én gang per frame etter move(). Bremser mykt hvis fienden ikke styrte."""
        if not self._steered and self.velocity.length_squared() > 0:
            self._steer(0, 0, dt_ms, obstacles)
        self._steered = False

    def _slide_move(self, vx, vy, dt_ms, obstacles):
        """Smooth bevegelse med wall sliding."""
        dt = dt_ms / 1000.0
        dx_total = vx * dt
        dy_total = vy * dt
        steps = max(1, int(max(abs(dx_total), abs(dy_total)) // 4))
        sdx = dx_total / steps
        sdy = dy_total / steps
        
        for _ in range(steps):
            x_blocked = False
            y_blocked = False
            
            if sdx:
                self.pos.x += sdx
                self._sync_rect_from_pos()
                if self.check_collision(obstacles):
                    self.pos.x -= sdx
                    self._sync_rect_from_pos()
                    x_blocked = True
            
            if sdy:
                self.pos.y += sdy
                self._sync_rect_from_pos()
                if self.check_collision(obstacles):
                    self.pos.y -= sdy
                    self._sync_rect_from_pos()
                    y_blocked = True
            
            if x_blocked and not y_blocked and sdy:
                magnitude = (sdx**2 + sdy**2)**0.5
                self.pos.y += (magnitude - abs(sdy)) * (1 if sdy > 0 else -1)
                self._sync_rect_from_pos()
                if self.check_collision(obstacles):
                    self.pos.y -= (magnitude - abs(sdy)) * (1 if sdy > 0 else -1)
                    self._sync_rect_from_pos()
            
            elif y_blocked and not x_blocked and sdx:
                magnitude = (sdx**2 + sdy**2)**0.5
                self.pos.x += (magnitude - abs(sdx)) * (1 if sdx > 0 else -1)
                self._sync_rect_from_pos()
                if self.check_collision(obstacles):
                    self.pos.x -= (magnitude - abs(sdx)) * (1 if sdx > 0 else -1)
                    self._sync_rect_from_pos()

    def _move_towards(self, target_px, obstacles, dt_ms):
        """Gå mot en piksel-posisjon med normalisert fart."""
        direction = Vector2(target_px[0] - self.pos.x, target_px[1] - self.pos.y)
        dist = direction.length()

        if self._bursting():
            self._advance_burst(dt_ms)

        if self._burst_paused():
            self._steer(0, 0, dt_ms, obstacles)  # pause: inertien bremser hoppet mykt ned
        elif dist > 1e-6:
            direction /= dist
            direction.rotate_ip(self._direction_noise_deg(dt_ms, dist))
            self._steer(direction.x * self.speed, direction.y * self.speed, dt_ms, obstacles)
        return self._dist2(int(self.pos.x), int(self.pos.y), int(target_px[0]), int(target_px[1])) <= (24 * 24)

    def _lunge(self, vx, vy, dt_ms, obstacles):
            """Lunge attack, returns when it hits an obstacle"""
            self.velocity.update(0, 0)  # lunge er instant – starter fra stillstand etterpå
            dt = dt_ms / 1000.0
            dx_total = vx * dt
            dy_total = vy * dt
            steps = max(1, int(max(abs(dx_total), abs(dy_total)) // 4))
            sdx = dx_total / steps
            sdy = dy_total / steps

            for _ in range(steps):

                if sdx:
                    self.pos.x += sdx
                    self._sync_rect_from_pos()
                    if self.check_collision(obstacles):
                        self.pos.x -= sdx
                        self._sync_rect_from_pos()
                        return True

                if sdy:
                    self.pos.y += sdy
                    self._sync_rect_from_pos()
                    if self.check_collision(obstacles):
                        self.pos.y -= sdy
                        self._sync_rect_from_pos()
                        return True
            return False

    def _separation_push(self, target_x, target_y, radius, strength):
        """Regner ut push-vektor bort fra (target_x, target_y).

        Maks styrke ved dist=0, null ved dist>=radius. Fallback-retning
        Vector2(1, 0) når self.pos er nøyaktig på target (samme mønster
        som apply_knockback i entity.py).
        """
        direction = Vector2(self.pos.x - target_x, self.pos.y - target_y)
        dist = direction.length()
        if dist >= radius:
            return 0.0, 0.0
        if dist > 0:
            direction = direction.normalize()
        else:
            direction = Vector2(1, 0)

        magnitude = (radius - dist) * strength
        return direction.x * magnitude, direction.y * magnitude

    def apply_separation(self, others, obstacles):
        """Myk dytting bort fra andre fiender – respekterer vegger."""
        strength = 0.08
        radius = 64
        pushx = pushy = 0.0

        for other in others:
            if other is self or not other.alive:
                continue
            ox, oy = self._separation_push(other.pos.x, other.pos.y, radius, strength)
            pushx += ox
            pushy += oy

        # X-akse
        if pushx:
            self.pos.x += pushx
            self._sync_rect_from_pos()
            if self.check_collision(obstacles):
                self.pos.x -= pushx
                self._sync_rect_from_pos()

        # Y-akse
        if pushy:
            self.pos.y += pushy
            self._sync_rect_from_pos()
            if self.check_collision(obstacles):
                self.pos.y -= pushy
                self._sync_rect_from_pos()

    def apply_player_separation(self, player, obstacles):
        """Myk dytting av fienden bort fra spilleren – kun aktiv under "chase". Spilleren påvirkes ikke."""
        if self.state != "chase":
            return

        strength = 0.08
        radius = (self.width + self.height) / 4 + (player.width + player.height) / 4 + 24

        pushx, pushy = self._separation_push(player.rect.centerx, player.rect.centery, radius, strength)

        # X-akse
        if pushx:
            self.pos.x += pushx
            self._sync_rect_from_pos()
            if self.check_collision(obstacles):
                self.pos.x -= pushx
                self._sync_rect_from_pos()

        # Y-akse
        if pushy:
            self.pos.y += pushy
            self._sync_rect_from_pos()
            if self.check_collision(obstacles):
                self.pos.y -= pushy
                self._sync_rect_from_pos()