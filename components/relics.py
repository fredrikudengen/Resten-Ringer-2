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
    name = "Vampyrisk"
    description = "Helbred 2 HP for hvert kill."
    color = constants.RED

    def on_kill(self, player):
        player.health = min(player.health + 2, player.max_health)

class Adrenaline(Relic):
    name        = "Adrenalin"
    description = "Få +3 fart i 2s når du tar skade."
    color       = (255, 200, 50)

    def on_hit(self, player):
        player.adrenaline_until = pygame.time.get_ticks() + 2000
        player.speed += 3

class GlassCannon(Relic):
    name        = "Glass Kanon"
    description = "+40% våpen skade, -35 max HP."
    color       = (255, 80, 80)

    def on_equip(self, player):
        player.gun.damage  = round(player.gun.damage * 1.4, 1)
        player.max_health -= 35
        player.health      = min(player.health, player.max_health)

class Reloader(Relic):
    name        = "Reloader"
    description = "Å dashe reloader våpenet automatisk."
    color       = (100, 180, 255)

    def on_dash(self, player):
        player.gun.current_ammo  = player.gun.max_ammo
        player.gun._reload_start = None

ALL_RELICS = [Vampiric, Adrenaline, GlassCannon, Reloader]