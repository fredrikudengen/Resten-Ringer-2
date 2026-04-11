import pygame

from core import constants

class Relic:
    name        = "Relic"
    description = ""
    color       = (200, 200, 200)

    def on_equip(self, player): pass
    def on_kill(self, player):  pass
    def on_hit(self, player):   pass
    def on_dash(self, player):  pass 

class Vampiric(Relic):
    name = "Vampiric"
    description = "Heal 2 HP on kill."
    color = constants.RED

    def on_kill(self, player):
        player.health = min(player.health + 2, player.max_health)

class Adrenaline(Relic):
    name        = "Adrenaline"
    description = "Gain +3 speed for 2s on taking damage."
    color       = (255, 200, 50)

    def on_hit(self, player):
        player.adrenaline_until = pygame.time.get_ticks() + 2000
        player.speed += 3

class GlassCannon(Relic):
    name        = "Glass Cannon"
    description = "+40% gun damage, -35 max HP."
    color       = (255, 80, 80)

    def on_equip(self, player):
        player.gun.damage  = round(player.gun.damage * 1.4, 1)
        player.max_health -= 35
        player.health      = min(player.health, player.max_health)

class Reloader(Relic):
    name        = "Reloader"
    description = "Dashing instantly reloads your gun."
    color       = (100, 180, 255)

    def on_dash(self, player):
        player.gun.current_ammo  = player.gun.max_ammo
        player.gun._reload_start = None

ALL_RELICS = [Vampiric, Adrenaline, GlassCannon, Reloader]