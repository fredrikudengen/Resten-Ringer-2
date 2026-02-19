"""
Spesialiserte fiende-typer.

Alle arver fra Enemy og setter sine egne stats.
attack_windup_ms: Tid fienden står stille med "telegraf"-animasjon før slag lander.
knockback_strength: Kraft på knockback mot spilleren ved treff.
"""

from .enemy import Enemy


class FastEnemy(Enemy):
    """
    Rask, smidig fiende med lav health.
    Kort windup – angriper raskt og presist.
    """
    def __init__(self, x, y):
        super().__init__(
            x, y,
            speed=100,
            health=3,
            damage=1,
            detection_radius=700,
            attack_range=5000,
            attack_cooldown=800,
            attack_windup_ms=500,      # Rask – kort tid å reagere
            knockback_strength=6,      # Lett knockback
            size=(50, 50),
            color=(255, 0, 0),
            wander_radius=4,
            wander_interval=(500, 1500)
        )


class SlowEnemy(Enemy):
    """
    Treg, robust tank.
    Lang windup – tydelig telegraf, men gjør stor skade og knockback.
    """
    def __init__(self, x, y):
        super().__init__(
            x, y,
            speed=40,
            health=80,
            damage=8,
            detection_radius=150,
            attack_range=60,
            attack_cooldown=1500,
            attack_windup_ms=700,      # Treg – men lett å unngå med dash
            knockback_strength=14,     # Kraftig knockback
            size=(28, 28),
            color=(0, 0, 0),
            wander_radius=2,
            wander_interval=(2000, 4000)
        )


class TankEnemy(Enemy):
    """
    Ekstremt robust boss-lignende fiende.
    Veldig lang windup, massiv skade og knockback.
    """
    def __init__(self, x, y):
        super().__init__(
            x, y,
            speed=40,
            health=150,
            damage=12,
            detection_radius=180,
            attack_range=70,
            attack_cooldown=2000,
            attack_windup_ms=900,      # Svært treg – men dødelig
            knockback_strength=18,     # Massiv knockback
            size=(36, 36),
            color=(80, 80, 200),
            wander_radius=1,
            wander_interval=(3000, 6000)
        )


class ScoutEnemy(Enemy):
    """
    Scout – oppdager tidlig, men er svak i nærkamp.
    """
    def __init__(self, x, y):
        super().__init__(
            x, y,
            speed=40,
            health=25,
            damage=3,
            detection_radius=400,
            attack_range=40,
            attack_cooldown=1200,
            attack_windup_ms=300,      # Moderat
            knockback_strength=5,      # Liten knockback
            size=(18, 18),
            color=(0, 0, 0),
            wander_radius=5,
            wander_interval=(300, 1000)
        )


class AssassinEnemy(Enemy):
    """
    Assassin – balansert og dødelig.
    Middels windup, høy skade.
    """
    def __init__(self, x, y):
        super().__init__(
            x, y,
            speed=40,
            health=50,
            damage=10,
            detection_radius=200,
            attack_range=55,
            attack_cooldown=1000,
            attack_windup_ms=350,      # Balansert
            knockback_strength=10,     # Solid knockback
            size=(24, 24),
            color=(180, 50, 180),
            wander_radius=3,
            wander_interval=(1000, 2500)
        )


class BruteEnemy(Enemy):
    """
    Brute – kraftig i nærkamp.
    Lang windup men massiv skade og knockback.
    """
    def __init__(self, x, y):
        super().__init__(
            x, y,
            speed=40,
            health=100,
            damage=15,
            detection_radius=160,
            attack_range=75,
            attack_cooldown=1800,
            attack_windup_ms=600,      # Tydelig telegraf
            knockback_strength=20,     # Sterkeste knockback
            size=(32, 32),
            color=(200, 50, 50),
            wander_radius=2,
            wander_interval=(1500, 3500)
        )


class SwarmEnemy(Enemy):
    """
    Swarm – svak alene, farlig i gruppe.
    Kort windup og rask attack rate.
    """
    def __init__(self, x, y):
        super().__init__(
            x, y,
            speed=40,
            health=15,
            damage=2,
            detection_radius=220,
            attack_range=45,
            attack_cooldown=600,
            attack_windup_ms=200,      
            knockback_strength=4,      
            size=(16, 16),
            color=(0, 0, 0),
            wander_radius=4,
            wander_interval=(400, 1200)
        )


class BossEnemy(Enemy):
    """
    Boss – ekstrem utfordring.
    Lang windup gir spilleren én sjanse til å dashe unna.
    """
    def __init__(self, x, y):
        super().__init__(
            x, y,
            speed=40,
            health=300,
            damage=20,
            detection_radius=350,
            attack_range=80,
            attack_cooldown=1500,
            attack_windup_ms=800,      # Lang – telegraferer tydelig
            knockback_strength=25,     # Ekstrem knockback
            size=(48, 48),
            color=(255, 0, 255),
            wander_radius=2,
            wander_interval=(2000, 4000)
        )
    
    def draw(self, screen, camera):
        """Custom tegning for boss – gul border."""
        super().draw(screen, camera)
        import pygame
        draw_rect = camera.apply(self.rect)
        pygame.draw.rect(screen, (255, 255, 0), draw_rect, 3)