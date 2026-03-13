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
    
    def _apply_separation(self, others):
        """Myk dytting bort fra andre fiender."""
        strength = 0.08
        radius = 64
        self_x, self_y = self.pos.x, self.pos.y
        pushx = pushy = 0.0
        r2 = float(radius * radius)

        for other in others:
            if other is self or not other.alive:
                continue
            other_x, other_y = other.pos.x, other.pos.y
            distance_x, distance_y = self_x - other_x, self_y - other_y
            distance2 = distance_x * distance_x + distance_y * distance_y
            if 0 < distance2 < r2:
                weight = 1.0 / max(1.0, distance2)
                pushx += distance_x * weight
                pushy += distance_y * weight

        self.pos.x += pushx * strength
        self.pos.y += pushy * strength
        self._sync_rect_from_pos() 