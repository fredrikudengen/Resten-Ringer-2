import pygame
import constants
from rooms import GridRoom
from entities import Door
from components import Speed_Powerup, Attack_Powerup, Shield_Powerup
from entities import (
    Enemy, FastEnemy, SlowEnemy, TankEnemy, ScoutEnemy,
    AssassinEnemy, BruteEnemy, SwarmEnemy, BossEnemy
)
import random
import copy


class RoomManager:
      
    def __init__(self, world, player, camera):
        self.world = world
        self.player = player
        self.camera = camera

        self.rooms             = []
        self.doors             = []
        self.total_kills       = 0
        self.rooms_cleared     = 0
        self.progression_level = 1 

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
        self.rooms_cleared += 1
        self._update_progression_level()
        
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

        # --- Obstacles ---
        for gy in range(room.rows):
            for gx in range(room.cols):
                if room.terrain[gy][gx] == constants.TILE_WALL:
                    self.world.add_obstacle(room.tile_rect(gx, gy))

        # --- Spawns ---
        self.doors = []
        for gy in range(room.rows):
            for gx in range(room.cols):
                tag = room.spawns[gy][gx]
                if not tag: 
                    continue
                x, y = gx * constants.TILE_SIZE, gy * constants.TILE_SIZE
                
                # Forced specific enemy types
                if tag == 'fast_enemy':
                    self.world.add_enemy(x, y, enemy_type=FastEnemy)
                elif tag == 'slow_enemy':
                    self.world.add_enemy(x, y, enemy_type=SlowEnemy)
                elif tag == 'tank_enemy':
                    self.world.add_enemy(x, y, enemy_type=TankEnemy)
                elif tag == 'scout_enemy':  
                    self.world.add_enemy(x, y, enemy_type=ScoutEnemy)
                elif tag == 'assassin_enemy':
                    self.world.add_enemy(x, y, enemy_type=AssassinEnemy)
                elif tag == 'brute_enemy':  
                    self.world.add_enemy(x, y, enemy_type=BruteEnemy)
                elif tag == 'swarm_enemy':  
                    self.world.add_enemy(x, y, enemy_type=SwarmEnemy)
                elif tag == 'boss_enemy':  
                    self.world.add_enemy(x, y, enemy_type=BossEnemy)

                elif tag == 'enemy':
                    enemy_type = self._choose_enemy_for_progression()
                    self.world.add_enemy(x, y, enemy_type=enemy_type)
                
                # Powerups
                elif tag == 'speed_powerup':
                    self.world.add_powerup(Speed_Powerup(x, y, 20))
                elif tag == 'attack_powerup':
                    self.world.add_powerup(Attack_Powerup(x, y, 20))
                elif tag == 'shield_powerup':
                    self.world.add_powerup(Shield_Powerup(x, y, 20))
                
                # Doors
                elif tag == 'door':
                    drect = pygame.Rect(x, y, constants.TILE_SIZE, constants.TILE_SIZE)
                    self.doors.append({"door": Door(drect), "g": (gx, gy)})
                
                room.spawns[gy][gx] = None  # clear marker

        # --- Player spawn ---
        spawn_side = constants.OPPOSITE.get(entry_side) if entry_side else None
        if spawn_side:
            self.player.rect.topleft = self._pick_spawn_near_door(room, spawn_side)
        else:
            self.player.rect.topleft = (constants.TILE_SIZE * 2, constants.TILE_SIZE * 2)

        # Close doors at start
        for d in self.doors:
            d["door"].set_open(False)
        self._sync_door_blockers()
        
        self.world.current_room = room

    # ========== PROGRESSION SYSTEM ==========
    
    def _update_progression_level(self):
        """
        Update progression level based on rooms cleared.
        
        Level 1-10 based on rooms cleared:
        - Level 1: Rooms 0-2
        - Level 2: Rooms 3-4
        - Level 3: Rooms 5-6
        - ...
        - Level 10: Rooms 18+
        """
        if self.rooms_cleared <= 2:
            self.progression_level = 1
        elif self.rooms_cleared <= 4:
            self.progression_level = 2
        elif self.rooms_cleared <= 6:
            self.progression_level = 3
        elif self.rooms_cleared <= 8:
            self.progression_level = 4
        elif self.rooms_cleared <= 10:
            self.progression_level = 5
        elif self.rooms_cleared <= 12:
            self.progression_level = 6
        elif self.rooms_cleared <= 14:
            self.progression_level = 7
        elif self.rooms_cleared <= 16:
            self.progression_level = 8
        elif self.rooms_cleared <= 18:
            self.progression_level = 9
        else:
            self.progression_level = 10
    
    def _choose_enemy_for_progression(self):
        """
        Choose enemy type based on current progression level.
        
        Returns:
            Enemy class
        """
        level = self.progression_level
        
        if level == 1:
            # Tutorial - only weak enemies
            return random.choice([SwarmEnemy, SwarmEnemy, FastEnemy])
        
        elif level == 2:
            # Introduce FastEnemy
            return random.choice([SwarmEnemy, FastEnemy, FastEnemy])
        
        elif level == 3:
            # Introduce SlowEnemy
            return random.choice([FastEnemy, FastEnemy, SlowEnemy])
        
        elif level == 4:
            # Introduce ScoutEnemy
            return random.choice([FastEnemy, SlowEnemy, ScoutEnemy])
        
        elif level == 5:
            # Introduce AssassinEnemy
            return random.choice([
                FastEnemy, SlowEnemy, ScoutEnemy, AssassinEnemy
            ])
        
        elif level == 6:
            # Introduce TankEnemy
            return random.choice([
                FastEnemy, SlowEnemy, AssassinEnemy, TankEnemy
            ])
        
        elif level == 7:
            # Introduce BruteEnemy
            return random.choice([
                SlowEnemy, AssassinEnemy, TankEnemy, BruteEnemy
            ])
        
        elif level == 8:
            return random.choice([
                AssassinEnemy, AssassinEnemy, 
                TankEnemy, BruteEnemy
            ])
        
        elif level == 9:
            return random.choice([
                TankEnemy, TankEnemy,
                BruteEnemy, BruteEnemy,
                AssassinEnemy
            ])
        
        else:  # level >= 10
            return random.choice([
                TankEnemy, BruteEnemy, BruteEnemy, AssassinEnemy
            ])
    
    def get_enemy_pool_for_level(self, level):
        pools = {
            1: ["SwarmEnemy", "FastEnemy"],
            2: ["SwarmEnemy", "FastEnemy"],
            3: ["FastEnemy", "SlowEnemy"],
            4: ["FastEnemy", "SlowEnemy", "ScoutEnemy"],
            5: ["FastEnemy", "SlowEnemy", "ScoutEnemy", "AssassinEnemy"],
            6: ["FastEnemy", "SlowEnemy", "AssassinEnemy", "TankEnemy"],
            7: ["SlowEnemy", "AssassinEnemy", "TankEnemy", "BruteEnemy"],
            8: ["AssassinEnemy", "TankEnemy", "BruteEnemy"],
            9: ["TankEnemy", "BruteEnemy", "AssassinEnemy"],
            10: ["TankEnemy", "BruteEnemy", "AssassinEnemy"]
        }
        return pools.get(min(level, 10), pools[10])

    # ========== DOOR & SPAWN HELPERS ==========

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

    def door_side(self, room, gx, gy):
        if gx == 0: return "W"
        if gx == room.cols - 1: return "E"
        if gy == 0: return "N"
        if gy == room.rows - 1: return "S"
        return None
    
    def _pick_spawn_near_door(self, room, want_side):
        if not room.doors:
            return (constants.TILE_SIZE * 2, constants.TILE_SIZE * 2)

        candidates = []
        for (gx, gy) in room.doors:
            s = self.door_side(room, gx, gy)
            if s == want_side:
                candidates.append((gx, gy))

        gx, gy = (candidates[0] if candidates else room.doors[0])

        # Spawn one tile into room
        T = constants.TILE_SIZE
        px = gx * T
        py = gy * T

        if want_side == "W": px += T
        elif want_side == "E": px -= T
        elif want_side == "N": py += T
        elif want_side == "S": py -= T

        return (px + (T - self.player.rect.width)//2, py + (T - self.player.rect.height)//2)

    # ========== ROOM DEFINITIONS ==========

    def _build_demo_grid_rooms(self):
        """
        Build demo rooms with progression-based spawning.
        
        Legend:
        - '#' = Wall
        - '.' = Floor
        - 'D' = Door
        - 'E' = Enemy (progression-based)
        - 'F/S/T/B' = Specific enemy type (forced)
        - 'P' = Powerup
        """
        
        # Combat room 1 - generic enemies
        r1 = GridRoom([
            "###########D############",
            "#......................#",
            "#.......P..............#",
            "#......................#",
            "#......................#",
            "#......................D",
            "D..........F...........#",
            "#......................#",
            "#......................#",
            "#......................#",
            "#......................#",
            "############D###########",
        ])

        r2 = GridRoom([
            "###########D############",
            "#......................#",
            "#......................#",
            "#......................#",
            "#......................#",
            "#......................D",
            "D..........F...........#",
            "#......................#",
            "#.................P....#",
            "#......................#",
            "#......................#",
            "############D###########",
        ])

        r3 = GridRoom([
            "####D#####......####D###",
            "#........#......#......#",
            "D...P....########......D",
            "#.........E............#",
            "#......................#",
            "############D###########",
        ])
                
        # Boss room - specific boss placement
        r_boss = GridRoom([
            "###########D############",
            "#.....................#",
            "#.....................#",
            "D.........B...........D",
            "#.....................#",
            "#.....................#",
            "############D###########",
        ])
        
        # Elite room - mix of specific hard enemies
        r_elite = GridRoom([
            "############D###########",
            "#....T................#",
            "#..###......###.......#",
            "D..#...R....#....A....D",
            "#..###......###.......#",
            "#.................T...#",
            "############D###########",
        ])
        
        # Start room - no enemies
        r_start = GridRoom([
            "##D##",
            "#...#",
            "D...D",
            "#...#",
            "##D##"
        ])
        
        # Reward room - powerups, few weak enemies
        r_reward = GridRoom([
            "...D...",
            "..P...D",
            "D..P...",
            "...D..."
        ])
        
        self.rooms = {
            "combat": [r1, r2, r3],
            "elite": [r_elite],
            "boss": [r_boss],
            "start": [r_start],
            "reward": [r_reward]
        }