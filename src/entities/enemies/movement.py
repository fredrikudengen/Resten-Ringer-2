from pygame.math import Vector2

class MovementMixin:

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
        if dist > 1e-6:
            direction /= dist
            self._slide_move(direction.x * self.speed, direction.y * self.speed, dt_ms, obstacles)
        return self._dist2(int(self.pos.x), int(self.pos.y), int(target_px[0]), int(target_px[1])) <= (24 * 24)

    def _lunge(self, vx, vy, dt_ms, obstacles):
            """Lunge attack, returns when it hits an obstacle"""
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

    def apply_separation(self, others, obstacles):
        """Myk dytting bort fra andre fiender – respekterer vegger."""
        strength = 0.08
        radius = 64
        self_x, self_y = self.pos.x, self.pos.y
        pushx = pushy = 0.0
        r2 = float(radius * radius)

        for other in others:
            if other is self or not other.alive:
                continue
            dx = self_x - other.pos.x
            dy = self_y - other.pos.y
            dist2 = dx * dx + dy * dy
            if 0 < dist2 < r2:
                weight = 1.0 - (dist2 / r2)
                pushx += dx * weight
                pushy += dy * weight

        # X-akse
        if pushx:
            self.pos.x += pushx * strength
            self._sync_rect_from_pos()
            if self.check_collision(obstacles):
                self.pos.x -= pushx * strength
                self._sync_rect_from_pos()

        # Y-akse
        if pushy:
            self.pos.y += pushy * strength
            self._sync_rect_from_pos()
            if self.check_collision(obstacles):
                self.pos.y -= pushy * strength
                self._sync_rect_from_pos()