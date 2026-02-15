import pygame
import constants
from rooms import GridRoom
from entities import Door
from components import Speed_Powerup, Attack_Powerup, Shield_Powerup
from entities import Enemy
import random
import copy


class RoomManager:
    def __init__(self, world, player, camera):
        self.world = world
        self.player = player
        self.camera = camera

        self.rooms = []
        self.doors = []

        self._build_demo_grid_rooms()
        self.current_room_type = "start"
        self._load_room(self.rooms[self.current_room_type][0], entry_side="N")

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

    def _go_to_next_room(self, entry_side):
        if self.current_room_type == "reward":
            candidates = self.rooms["combat"]
        else:
            candidates = (
                self.rooms["reward"]
                if random.random() < 0.25
                else self.rooms["combat"]
            )

        nxt = random.choice(candidates)
        self._load_room(nxt, entry_side)


    def _load_room(self, room, entry_side):
        self.current_room_type = room
        self.world.clear()
        room.reset_spawns()

        for gy in range(room.rows):
            for gx in range(room.cols):
                if room.terrain[gy][gx] == constants.TILE_WALL:
                    self.world.add_obstacle(room.tile_rect(gx, gy))

        self.doors = []
        for gy in range(room.rows):
            for gx in range(room.cols):
                tag = room.spawns[gy][gx]
                if not tag: 
                    continue
                x, y = gx * constants.TILE_SIZE, gy * constants.TILE_SIZE
                if tag == 'enemy':
                    self.world.add_enemy(x, y)
                elif tag == 'speed_powerup':
                    self.world.add_powerup(Speed_Powerup(x, y, 20))
                elif tag == 'attack_powerup':
                    self.world.add_powerup(Attack_Powerup(x, y, 20))
                elif tag == 'shield_powerup':
                    self.world.add_powerup(Shield_Powerup(x, y, 20))
                elif tag == 'door':
                    drect = pygame.Rect(x, y, constants.TILE_SIZE, constants.TILE_SIZE)
                    self.doors.append({"door": Door(drect), "g": (gx, gy)})
                room.spawns[gy][gx] = None  # tøm markør

        # 4) Player spawn
        spawn_side = constants.OPPOSITE.get(entry_side) if entry_side else None
        if spawn_side:
            self.player.rect.topleft = self._pick_spawn_near_door(room, spawn_side)
        else:
            self.player.rect.topleft = (constants.TILE_SIZE * 2, constants.TILE_SIZE * 2)


        # 5) Lukk dører i starten
        for d in self.doors:
            d["door"].set_open(False)
        self._sync_door_blockers()
        
        self.world.current_room = room


    def _rect_key(self, r: pygame.Rect):
        return (r.x, r.y, r.w, r.h)

    def _sync_door_blockers(self):
        # Fjern alle dør-blockers
        door_keys = {self._rect_key(d["door"].rect) for d in self.doors}
        self.world.obstacles = [
            r for r in self.world.obstacles
            if self._rect_key(r) not in door_keys
        ]
        # Legg til blockers for lukka dører
        existing = {self._rect_key(r) for r in self.world.obstacles}
        for d in self.doors:
            if not d["door"].is_open:
                k = self._rect_key(d["door"].rect)
                if k not in existing:
                    self.world.add_obstacle(d["door"].rect)
                    existing.add(k)

    def door_side(self, room, gx, gy):
        if gx == 0: return "W"
        if gx == room.cols - 1: return "E"
        if gy == 0: return "N"
        if gy == room.rows - 1: return "S"
        return None
    
    def _pick_spawn_near_door(self, room, want_side):
        if not room.doors:
            return (constants.TILE_SIZE * 2, constants.TILE_SIZE * 2)

        # finn kandidater på ønsket side
        candidates = []
        for (gx, gy) in room.doors:
            s = self.door_side(room, gx, gy)
            if s == want_side:
                candidates.append((gx, gy))

        # fallback: bruk første dør hvis ingen matcher
        gx, gy = (candidates[0] if candidates else room.doors[0])

        # spawn ett tile inn i rommet
        T = constants.TILE_SIZE
        px = gx * T
        py = gy * T

        if want_side == "W": px += T
        elif want_side == "E": px -= T
        elif want_side == "N": py += T
        elif want_side == "S": py -= T

        # sentrer spilleren omtrent på tile (litt penere)
        return (px + (T - self.player.rect.width)//2, py + (T - self.player.rect.height)//2)


    def _build_demo_grid_rooms(self):
        r1 = GridRoom([
            "###################D##############",
            "#....E.......P..................#",
            "#..###......###.................#",
            "#..#........#...................#",
            "#..###..E...###.................#",
            "D...............................D",
            "#...............................#",
            "#...............................#",
            "#...............................#",
            "#.........................E.....#",
            "#...................E...........#",
            "#################D################",
        ])
        r2 = GridRoom([
            "############D###########",
            "#................E....#",
            "#..######.............#",
            "D..#....#.....P.......D",
            "#..#....#.............#",
            "#..######.............#",
            "############D###########",
        ])
        r3 = GridRoom([
            "###########D############",
            "#....E................#",
            "#..###......###.......#",
            "D..#........#.........D",
            "#..###......###...P...#",
            "#.....................#",
            "############D###########",
        ])
        r_start = GridRoom([
            "##D##",
            "#...#",
            "D...D",
            "#...#",
            "##D##"
        ])
        r_reward = GridRoom([
            "...D...",
            "......D",
            "D......",
            "...D..."
        ])
        self.rooms = {
                "combat": [r1, r2, r3],
                "start":  [r_start],
                "reward": [r_reward]
                }

