from __future__ import annotations

import random
from dataclasses import dataclass

import pygame

from components.chest import Chest
from core import constants
from components import Door, ShieldPowerup, AttackPowerup, SpeedPowerup, HealthPowerup
from core.sound_manager import sound
from .room_registry import RoomRegistry
from .floor_generator import generate_floor
from .floor_map import FloorMap, RoomNode
from .progression import level_from_rooms_cleared, choose_enemy, scale_enemy


@dataclass
class DoorEntry:
    door: Door
    grid_pos: tuple[int, int]  # (gx, gy) inside the GridRoom layout

TAG_TO_POWERUP: dict[str, type] = {
    'SpeedPowerup': SpeedPowerup,
    'AttackPowerup': AttackPowerup,
    'ShieldPowerup': ShieldPowerup,
    'HealthPowerup': HealthPowerup
}

def choose_powerup():
    return random.choice([ShieldPowerup, AttackPowerup, SpeedPowerup, HealthPowerup])


class RoomManager:

    def __init__(self, world, player, camera):
        self.world  = world
        self.player = player
        self.camera = camera

        self.registry = RoomRegistry()

        # Floor state
        self.floor_map:    FloorMap | None  = None
        self.current_node: RoomNode | None  = None

        # Door widgets for the current room
        self.doors: list[DoorEntry] = []

        # Stats (persist across floors)
        self.rooms_cleared     = 0
        self.progression_level = 1
        self.current_room_type = "start"

        # Room-local state
        self._room_cleared       = False
        self.pending_boss_reward = False
        self.pending_room_reward = False

        self.chest: Chest | None = None

        # Generate and enter floor 1
        self._generate_floor(floor_number=1)

    # ========== PUBLIC API ==========

    def update(self, player):
        if not self._room_cleared:
            if len(self.world.enemies) == 0:
                if self.current_room_type != "reward" or self.current_room_type == "start":
                    sound.play("room_cleared")
                self._room_cleared = True
                if self.current_node is not None:
                    self.current_node.cleared = True

            for d in self.doors:
                d.door.is_open = self._room_cleared
            self._sync_door_blockers()

        if self._room_cleared:
            if self.current_room_type == "boss":
                if not self.pending_boss_reward:
                    self.pending_boss_reward = True
                return

            if self.current_room_type == "reward" and self.chest and not self.chest.opened:
                if self.player.rect.colliderect(self.chest.rect):
                    self.chest.opened = True
                    if not self.pending_room_reward:
                        self.pending_room_reward = True

            for d in self.doors:
                if self.player.rect.colliderect(d.door.trigger) and player.is_moving:
                    side = self._door_side(
                        self.current_node.grid_room, *d.grid_pos
                    )
                    self._go_to_next_room(side)
                    break

    def draw(self, screen):
        for d in self.doors:
            d.door.draw(screen, self.camera)
        if self.chest:
            self.chest.draw(screen, self.camera)

    def advance_after_boss(self):
        """Called by BossRewardState after the player picks a reward."""
        floor_num = self.floor_map.floor_number + 1
        self._generate_floor(floor_num)

    # ========== FLOOR GENERATION ==========

    def _generate_floor(self, floor_number: int):
        """Generate a new floor and enter its start room."""
        self.floor_map = generate_floor(floor_number)
        start_node = self.floor_map.get_node(*self.floor_map.start_pos)
        self._visit_node(start_node, entry_side=None)

    # ========== ROOM TRANSITIONS ==========

    def _go_to_next_room(self, side: str):
        if self.current_room_type not in ("start", "reward", "boss"):
            self.rooms_cleared += 1
            self.progression_level = level_from_rooms_cleared(self.rooms_cleared)

        next_node = self.floor_map.neighbour(self.current_node, side)
        if next_node is None:
            return
        self._visit_node(next_node, entry_side=side)

    def _visit_node(self, node: RoomNode, entry_side: str | None):
        """
        Enter a room node.  Instantiates the GridRoom on first visit,
        then loads it into the world.
        """
        if not node.visited:
            node.visited = True
            node.grid_room = self._instantiate_room(node)

        self.current_node = node
        self._load_room(node, entry_side)

    def _instantiate_room(self, node: RoomNode):
        """
        Pick a compatible room template and build a GridRoom for this node.
        """
        required = node.door_sides

        templates = self.registry.find_compatible(node.room_type, required)
        if not templates:
            # Fallback: any template of this type, activate what we can
            templates = self.registry.all_templates(node.room_type)

        if not templates:
            raise RuntimeError(
                f"No room templates available for type '{node.room_type}'"
            )

        template = random.choice(templates)

        # Activate the intersection: required sides that the layout supports
        active = required & template.potential_doors
        return self.registry.instantiate(template, active)

    # ========== ROOM LOADING ==========

    def _load_room(self, node: RoomNode, entry_side):
        room = node.grid_room
        self.current_room_type = room.room_type
        self._room_cleared     = node.cleared
        self.world.clear()
        room.reset_spawns()

        self._place_obstacles(room)
        self._place_spawns(room, skip_enemies=node.cleared)
        self._place_player(room, entry_side)
        if room.room_type == "reward":
            self._place_chest(room)
        else:
            self.chest = None

        for d in self.doors:
            d.door.is_open = node.cleared
        self._sync_door_blockers()

        self.world.current_room = room

    def _place_obstacles(self, room):
        for gy in range(room.rows):
            for gx in range(room.cols):
                if room.terrain[gy][gx] == constants.TILE_WALL:
                    self.world.add_obstacle(room.tile_rect(gx, gy))

    def _place_spawns(self, room, skip_enemies: bool = False):
        self.doors = []
        for gy in range(room.rows):
            for gx in range(room.cols):
                tag = room.spawns[gy][gx]
                if not tag:
                    continue
                if skip_enemies and tag in (*constants.TAG_TO_ENEMY, 'enemy', *TAG_TO_POWERUP, 'powerup'):
                    room.spawns[gy][gx] = None
                    continue
                x = gx * constants.TILE_SIZE
                y = gy * constants.TILE_SIZE
                self._handle_tag(tag, x, y, gx, gy)
                room.spawns[gy][gx] = None

    def _handle_tag(self, tag, x, y, gx, gy):
        if tag in constants.TAG_TO_ENEMY:
            enemy = self.world.add_enemy(x, y, enemy_type=constants.TAG_TO_ENEMY[tag])
            scale_enemy(enemy, self.progression_level)
        if tag in TAG_TO_POWERUP:
            self.world.add_powerup(x, y, powerup_type=TAG_TO_POWERUP[tag])
        elif tag == 'enemy':
            enemy = self.world.add_enemy(x, y, enemy_type=choose_enemy(self.progression_level))
            scale_enemy(enemy, self.progression_level)
        elif tag == 'powerup':
            self.world.add_powerup(x, y, powerup_type=choose_powerup())
        elif tag == 'door':
            self.doors.append(DoorEntry(door=Door(x, y), grid_pos=(gx, gy)))

    def _place_player(self, room, entry_side):
        if room.room_type == "start":
            cx = (room.cols * constants.TILE_SIZE) // 2 - self.player.rect.width  // 2
            cy = (room.rows * constants.TILE_SIZE) // 2 - self.player.rect.height // 2
            self.player.rect.topleft = (cx, cy)
            return

        spawn_side = constants.OPPOSITE.get(entry_side) if entry_side else None
        if spawn_side:
            self.player.rect.topleft = self._pick_spawn_near_door(room, spawn_side)
        else:
            self.player.rect.topleft = (constants.TILE_SIZE * 2, constants.TILE_SIZE * 2)

    # ========== HELPERS ==========

    def _door_side(self, room, gx, gy) -> str | None:
        if gx == 0:             return "W"
        if gx == room.cols - 1: return "E"
        if gy == 0:             return "N"
        if gy == room.rows - 1: return "S"
        return None

    def _pick_spawn_near_door(self, room, want_side) -> tuple[int, int]:
        if not room.doors:
            return (constants.TILE_SIZE * 2, constants.TILE_SIZE * 2)

        candidates = [
            (gx, gy) for gx, gy in room.doors
            if self._door_side(room, gx, gy) == want_side
        ]
        gx, gy = candidates[0] if candidates else room.doors[0]

        T  = constants.TILE_SIZE
        px = gx * T
        py = gy * T

        if want_side == "W":   px += T
        elif want_side == "E": px -= T
        elif want_side == "N": py += T
        elif want_side == "S": py -= T

        return (
            px + (T - self.player.rect.width)  // 2,
            py + (T - self.player.rect.height) // 2,
        )

    def _rect_key(self, r: pygame.Rect) -> tuple[int, int, int, int]:
        return (r.x, r.y, r.w, r.h)

    def _sync_door_blockers(self):
        door_keys = {self._rect_key(d.door.rect) for d in self.doors}
        self.world.obstacles = [
            r for r in self.world.obstacles
            if self._rect_key(r) not in door_keys
        ]
        existing = {self._rect_key(r) for r in self.world.obstacles}
        for d in self.doors:
            if not d.door.is_open:
                k = self._rect_key(d.door.rect)
                if k not in existing:
                    self.world.add_obstacle(d.door.rect)
                    existing.add(k)

    def _place_chest(self, room):
        cx = (room.cols * constants.TILE_SIZE) // 2 - Chest.WIDTH // 2
        cy = (room.rows * constants.TILE_SIZE) // 2 - Chest.HEIGHT // 2
        self.chest = Chest(cx, cy)