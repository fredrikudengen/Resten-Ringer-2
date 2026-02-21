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
            attack_windup_ms=500,      
            knockback_strength=16,      
            size=(50, 50),
            color=(255, 0, 0),
            wander_radius=4,
            xp_reward=15
        )


class SlowEnemy(Enemy):
    """
    Treg, robust tank.
    Lang windup – tydelig telegraf, men gjør stor skade og knockback.
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
            attack_windup_ms=500,      
            knockback_strength=16,      
            size=(50, 50),
            color=(255, 0, 0),
            wander_radius=4,
            xp_reward=15
        )


class TankEnemy(Enemy):
    """
    Ekstremt robust boss-lignende fiende.
    Veldig lang windup, massiv skade og knockback.
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
            attack_windup_ms=500,      
            knockback_strength=16,      
            size=(50, 50),
            color=(255, 0, 0),
            wander_radius=4,
            xp_reward=15
        )


class ScoutEnemy(Enemy):
    """
    Scout – oppdager tidlig, men er svak i nærkamp.
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
            attack_windup_ms=500,      
            knockback_strength=16,      
            size=(50, 50),
            color=(255, 0, 0),
            wander_radius=4,
            xp_reward=15
        )


class AssassinEnemy(Enemy):
    """
    Assassin – balansert og dødelig.
    Middels windup, høy skade.
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
            attack_windup_ms=500,      
            knockback_strength=16,      
            size=(50, 50),
            color=(255, 0, 0),
            wander_radius=4,
            xp_reward=15
        )


class BruteEnemy(Enemy):
    """
    Brute – kraftig i nærkamp.
    Lang windup men massiv skade og knockback.
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
            attack_windup_ms=500,      
            knockback_strength=16,      
            size=(50, 50),
            color=(255, 0, 0),
            wander_radius=4,
        )


class SwarmEnemy(Enemy):
    """
    Swarm – svak alene, farlig i gruppe.
    Kort windup og rask attack rate.
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
            attack_windup_ms=500,      
            knockback_strength=16,      
            size=(50, 50),
            color=(255, 0, 0),
            wander_radius=4,
            xp_reward=15
        )


class BossEnemy(Enemy):
    """
    Boss – ekstrem utfordring.
    Lang windup gir spilleren én sjanse til å dashe unna.
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
            attack_windup_ms=500,      
            knockback_strength=16,      
            size=(50, 50),
            color=(255, 0, 0),
            wander_radius=4,
        )
    
    def draw(self, screen, camera):
        """Custom tegning for boss – gul border."""
        super().draw(screen, camera)
        import pygame
        draw_rect = camera.apply(self.rect)
        pygame.draw.rect(screen, (255, 255, 0), draw_rect, 3)