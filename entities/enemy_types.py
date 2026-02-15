"""
Spesialiserte fiende-typer.

Alle disse arver fra Enemy base class og setter bare sine egne stats.
All AI-logikk er i Enemy base class!
"""

from .enemy import Enemy


class FastEnemy(Enemy):
    """
    Rask, smidig fiende med lav health.
    
    Strategi: Rush og hit-and-run
    """
    def __init__(self, x, y):
        super().__init__(
            x, y,
            speed=100,                   # Veldig rask! 🏃
            health=3,                  # Lav health (glass cannon)
            damage=1,                   # Moderat skade
            detection_radius=700,       # Oppdager spilleren lett
            attack_range=100,            # Må komme nært
            attack_cooldown=800,        # Rask attack rate
            size=(50, 50),              # Mindre størrelse
            color=(255, 0, 0),          # Rødaktig
            wander_radius=4,            # Vandrer mye
            wander_interval=(500, 1500) # Ofte i bevegelse
        )


class SlowEnemy(Enemy):
    """
    Treg, robust fiende med høy health.
    
    Strategi: Tank og absorbere skade
    """
    def __init__(self, x, y):
        super().__init__(
            x, y,
            speed=40,                    # Veldig treg 🐌
            health=80,                  # Høy health (tank)
            damage=8,                   # Høy skade når den treffer
            detection_radius=150,       # Dårligere synsvidde
            attack_range=60,            # OK attack range
            attack_cooldown=1500,       # Treg attack rate
            size=(28, 28),              # Større størrelse
            color=(0, 0, 0),      # Grønnaktig
            wander_radius=2,            # Vandrer lite
            wander_interval=(2000, 4000) # Sjelden i bevegelse
        )


class TankEnemy(Enemy):
    """
    Ekstremt robust fiende - boss-lignende.
    
    Strategi: Absorbere masse skade, slow push
    """
    def __init__(self, x, y):
        super().__init__(
            x, y,
            speed=40,                  # Svært treg 🛡️
            health=150,                 # Enorm health!
            damage=12,                  # Massiv skade
            detection_radius=180,       # Moderat synsvidde
            attack_range=70,            # God attack range
            attack_cooldown=2000,       # Svært treg attack
            size=(36, 36),              # Stor størrelse
            color=(80, 80, 200),        # Blåaktig (metal)
            wander_radius=1,            # Nesten ingen wandering
            wander_interval=(3000, 6000) # Står mest stille
        )


class ScoutEnemy(Enemy):
    """
    Scout - oppdager spilleren tidlig og varsler andre.
    
    Strategi: Oppdagelse og flukt
    """
    def __init__(self, x, y):
        super().__init__(
            x, y,
            speed=40,                    # Ganske rask 🔭
            health=25,                  # Veldig lav health
            damage=3,                   # Lav skade
            detection_radius=400,       # ENORM detection radius!
            attack_range=40,            # Liten attack range
            attack_cooldown=1200,       # Moderat attack rate
            size=(18, 18),              # Liten størrelse
            color=(0, 0, 0),      # Gulaktig
            wander_radius=5,            # Vandrer mye (patruljerer)
            wander_interval=(300, 1000) # Konstant i bevegelse
        )


class AssassinEnemy(Enemy):
    """
    Assassin - balansert og dødelig.
    
    Strategi: Balansert approach
    """
    def __init__(self, x, y):
        super().__init__(
            x, y,
            speed=40,                    # Balansert hastighet ⚔️
            health=50,                  # Moderat health
            damage=10,                  # Høy skade!
            detection_radius=200,       # Standard detection
            attack_range=55,            # Standard range
            attack_cooldown=1000,       # Moderat cooldown
            size=(24, 24),              # Standard størrelse
            color=(180, 50, 180),       # Lilla (sneaky)
            wander_radius=3,            # Moderat wandering
            wander_interval=(1000, 2500) # Balansert
        )


class BruteEnemy(Enemy):
    """
    Brute - kraftig og farlig når nært.
    
    Strategi: Close combat devastation
    """
    def __init__(self, x, y):
        super().__init__(
            x, y,
            speed=40,                  # Treg-moderat 💪
            health=100,                 # Høy health
            damage=15,                  # MASSIV skade!
            detection_radius=160,       # Kort synsvidde
            attack_range=75,            # God reach
            attack_cooldown=1800,       # Langsom attack
            size=(32, 32),              # Stor størrelse
            color=(200, 50, 50),        # Mørk rød (aggro)
            wander_radius=2,            # Lite wandering
            wander_interval=(1500, 3500) # Relativt statisk
        )


class SwarmEnemy(Enemy):
    """
    Swarm - svak alene, farlig i gruppe.
    
    Strategi: Overwhelm med tall
    """
    def __init__(self, x, y):
        super().__init__(
            x, y,
            speed=40,                    # Moderat hastighet 🐝
            health=15,                  # Veldig lav health
            damage=2,                   # Lav skade
            detection_radius=220,       # God detection
            attack_range=45,            # Kort range
            attack_cooldown=600,        # Rask attack!
            size=(16, 16),              # Veldig liten
            color=(0, 0, 0),      # Oransje
            wander_radius=4,            # Aktiv wandering
            wander_interval=(400, 1200) # Svært aktiv
        )


class BossEnemy(Enemy):
    """
    Boss - ekstrem utfordring!
    
    Strategi: Dominere hele kampen
    """
    def __init__(self, x, y):
        super().__init__(
            x, y,
            speed=40,                    # Overraskende rask for størrelsen 👑
            health=300,                 # ENORM health pool
            damage=20,                  # Massiv skade
            detection_radius=350,       # Ser alt
            attack_range=80,            # Lang reach
            attack_cooldown=1500,       # Moderat cooldown
            size=(48, 48),              # STOR størrelse
            color=(255, 0, 255),        # Magenta (special)
            wander_radius=2,            # Lite wandering
            wander_interval=(2000, 4000) # Imposing presence
        )
    
    def draw(self, screen, camera):
        """
        Custom tegning for boss - mer iøynefallende.
        """
        # Tegn basis
        super().draw(screen, camera)
        
        # Legg til border for å skille boss fra vanlige enemies
        import pygame
        draw_rect = camera.apply(self.rect)
        pygame.draw.rect(screen, (255, 255, 0), draw_rect, 3)  # Gul border


# ============== UTILITY ==============

def spawn_mixed_wave(world, area_rect, count=10):
    """
    Spawn en blandet bølge av forskjellige enemy-typer.
    
    Args:
        world: World objekt
        area_rect: pygame.Rect område å spawne i
        count: Totalt antall enemies
    """
    import random
    
    # Distribusjon av enemy-typer
    enemy_types = [
        (FastEnemy, 3),      # 30% fast
        (SlowEnemy, 2),      # 20% slow
        (ScoutEnemy, 2),     # 20% scout
        (AssassinEnemy, 2),  # 20% assassin
        (SwarmEnemy, 1),     # 10% swarm
    ]
    
    # Expand til actual liste
    pool = []
    for enemy_class, weight in enemy_types:
        pool.extend([enemy_class] * weight)
    
    for _ in range(count):
        enemy_class = random.choice(pool)
        x = random.randint(area_rect.left, area_rect.right - 50)
        y = random.randint(area_rect.top, area_rect.bottom - 50)
        world.enemies.append(enemy_class(x, y))


def spawn_boss_wave(world, area_rect):
    """
    Spawn en boss med minions.
    
    Args:
        world: World objekt
        area_rect: pygame.Rect område å spawne i
    """
    import random
    
    # Boss i sentrum
    boss_x = area_rect.centerx
    boss_y = area_rect.centery
    world.enemies.append(BossEnemy(boss_x, boss_y))
    
    # Minions rundt
    minion_count = 4
    for i in range(minion_count):
        angle = (i / minion_count) * 6.28  # 2*pi
        offset = 100
        x = int(boss_x + offset * __import__('math').cos(angle))
        y = int(boss_y + offset * __import__('math').sin(angle))
        world.enemies.append(SwarmEnemy(x, y))