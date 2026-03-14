import pygame
from core import constants
from components import Door
from components import Speed_Powerup, Attack_Powerup, Shield_Powerup
from entities import (
    Enemy, FastEnemy, SlowEnemy, TankEnemy, ScoutEnemy,
    AssassinEnemy, BruteEnemy, SwarmEnemy, BossEnemy
)
from rooms.room_registry import build_rooms
from rooms.progression import level_from_rooms_cleared, choose_enemy
import random

# Tag → enemy class (for eksplisitte spawn-tags i rom-layoutet)
_TAG_TO_ENEMY = {
    'fast_enemy':     FastEnemy,
    'slow_enemy':     SlowEnemy,
    'tank_enemy':     TankEnemy,
    'scout_enemy':    ScoutEnemy,
    'assassin_enemy': AssassinEnemy,
    'brute_enemy':    BruteEnemy,
    'swarm_enemy':    SwarmEnemy,
    'boss_enemy':     BossEnemy,
}


class RoomManager:

    def __init__(self, world, player, camera):
        self.world  = world
        self.player = player
        self.camera = camera

        self.rooms             = build_rooms()
        self.doors             = []
        self.total_kills       = 0
        self.rooms_cleared     = 0
        self.progression_level = 1
        self.current_room_type = "start"

        self._load_room(self.rooms["start"][0], entry_side="N")

    # ========== PUBLIC API ==========

    def update(self):
        cleared = (len(self.world.enemies) == 0)
        for d in self.doors:
            d["door"].set_open(cleared)
        self._sync_door_blockers()

        if cleared:
            for d in self.doors:
                door_obj = d["door"]
                if self.player.rect.colliderect(door_obj.rect):
                    gx, gy = d["g"]
                    entry_side = self.door_side(self.world.current_room, gx, gy)
                    self._go_to_next_room(entry_side)
                    break

    def draw(self, screen):
        for d in self.doors:
            d["door"].draw(screen, self.camera)

    # ========== ROM-NAVIGASJON ==========

    def _go_to_next_room(self, entry_side):
        self.rooms_cleared     += 1
        self.progression_level  = level_from_rooms_cleared(self.rooms_cleared)

        if self.current_room_type == "reward":
            candidates = self.rooms["combat"]
        else:
            candidates = (
                self.rooms["reward"]
                if random.random() < 0.25
                else self.rooms["combat"]
            )

        self._load_room(random.choice(candidates), entry_side)

    def _load_room(self, room, entry_side):
        self.current_room_type = room
        self.world.clear()
        room.reset_spawns()

        self._place_obstacles(room)
        self._place_spawns(room)
        self._place_player(room, entry_side)

        for d in self.doors:
            d["door"].set_open(False)
        self._sync_door_blockers()

        self.world.current_room = room

    def _place_obstacles(self, room):
        for gy in range(room.rows):
            for gx in range(room.cols):
                if room.terrain[gy][gx] == constants.TILE_WALL:
                    self.world.add_obstacle(room.tile_rect(gx, gy))

    def _place_spawns(self, room):
        self.doors = []
        for gy in range(room.rows):
            for gx in range(room.cols):
                tag = room.spawns[gy][gx]
                if not tag:
                    continue
                x = gx * constants.TILE_SIZE
                y = gy * constants.TILE_SIZE
                self._handle_tag(tag, x, y, gx, gy)
                room.spawns[gy][gx] = None

    def _handle_tag(self, tag, x, y, gx, gy):
        # Spesifikk enemy
        if tag in _TAG_TO_ENEMY:
            self.world.add_enemy(x, y, enemy_type=_TAG_TO_ENEMY[tag])

        # Progresjonsstyrt enemy
        elif tag == 'enemy':
            self.world.add_enemy(x, y, enemy_type=choose_enemy(self.progression_level))

        # Powerups
        elif tag == 'speed_powerup':
            self.world.add_powerup(Speed_Powerup(x, y, 20))
        elif tag == 'attack_powerup':
            self.world.add_powerup(Attack_Powerup(x, y, 20))
        elif tag == 'shield_powerup':
            self.world.add_powerup(Shield_Powerup(x, y, 20))

        # Dør
        elif tag == 'door':
            
            self.doors.append({"door": Door(x, y), "g": (gx, gy)})

    def _place_player(self, room, entry_side):
        spawn_side = constants.OPPOSITE.get(entry_side) if entry_side else None
        if spawn_side:
            self.player.rect.topleft = self._pick_spawn_near_door(room, spawn_side)
        else:
            self.player.rect.topleft = (constants.TILE_SIZE * 2, constants.TILE_SIZE * 2)

    # ========== DØR-HJELPERE ==========

    def door_side(self, room, gx, gy):
        if gx == 0:              return "W"
        if gx == room.cols - 1:  return "E"
        if gy == 0:              return "N"
        if gy == room.rows - 1:  return "S"
        return None

    def _pick_spawn_near_door(self, room, want_side):
        if not room.doors:
            return (constants.TILE_SIZE * 2, constants.TILE_SIZE * 2)

        candidates = [(gx, gy) for gx, gy in room.doors
                      if self.door_side(room, gx, gy) == want_side]
        gx, gy = candidates[0] if candidates else room.doors[0]

        T  = constants.TILE_SIZE
        px = gx * T
        py = gy * T

        if want_side == "W": px += T
        elif want_side == "E": px -= T
        elif want_side == "N": py += T
        elif want_side == "S": py -= T

        return (px + (T - self.player.rect.width) // 2,
                py + (T - self.player.rect.height) // 2)

    def _rect_key(self, r: pygame.Rect):
        return (r.x, r.y, r.w, r.h)

    def _sync_door_blockers(self):
        door_keys = {self._rect_key(d["door"].rect) for d in self.doors}
        self.world.obstacles = [
            r for r in self.world.obstacles
            if self._rect_key(r) not in door_keys
        ]
        existing = {self._rect_key(r) for r in self.world.obstacles}
        for d in self.doors:
            if not d["door"].is_open:
                k = self._rect_key(d["door"].rect)
                if k not in existing:
                    self.world.add_obstacle(d["door"].rect)
                    existing.add(k)