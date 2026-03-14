from .enemy import Enemy


class FastEnemy(Enemy):
    """
    Rask, smidig fiende med lav health.
    Kort windup – angriper raskt og presist.
    """
    speed=100
    health=3
    damage=1
    detection_radius=700
    attack_range=5000
    attack_cooldown=800
    attack_windup_ms=500      
    knockback_strength=16  
    color=(255, 0, 0)
    xp_reward=15
    width = 50
    height = 50

    def __init__(self, x, y):
        super().__init__(x, y)


class SlowEnemy(Enemy):
    """
    Treg, robust tank.
    Lang windup – tydelig telegraf, men gjør stor skade og knockback.
    """
    speed=100
    health=3
    damage=1
    detection_radius=700
    attack_range=5000
    attack_cooldown=800
    attack_windup_ms=500      
    knockback_strength=16  
    color=(255, 0, 0)
    xp_reward=15
    width = 50
    height = 50

    def __init__(self, x, y):
        super().__init__(x, y)


class TankEnemy(Enemy):
    """
    Ekstremt robust boss-lignende fiende.
    Veldig lang windup, massiv skade og knockback.
    """
    speed=100
    health=3
    damage=1
    detection_radius=700
    attack_range=5000
    attack_cooldown=800
    attack_windup_ms=500      
    knockback_strength=16  
    color=(255, 0, 0)
    xp_reward=15
    width = 50
    height = 50

    def __init__(self, x, y):
        super().__init__(x, y)


class ScoutEnemy(Enemy):
    """
    Scout – oppdager tidlig, men er svak i nærkamp.
    """
    speed=100
    health=3
    damage=1
    detection_radius=700
    attack_range=5000
    attack_cooldown=800
    attack_windup_ms=500      
    knockback_strength=16  
    color=(255, 0, 0)
    xp_reward=15
    width = 50
    height = 50

    def __init__(self, x, y):
        super().__init__(x, y)


class AssassinEnemy(Enemy):
    """
    Assassin – balansert og dødelig.
    Middels windup, høy skade.
    """
    speed=100
    health=3
    damage=1
    detection_radius=700
    attack_range=5000
    attack_cooldown=800
    attack_windup_ms=500      
    knockback_strength=16  
    color=(255, 0, 0)
    xp_reward=15
    width = 50
    height = 50

    def __init__(self, x, y):
        super().__init__(x, y)

class BruteEnemy(Enemy):
    """
    Brute – kraftig i nærkamp.
    Lang windup men massiv skade og knockback.
    """
    speed=100
    health=3
    damage=1
    detection_radius=700
    attack_range=5000
    attack_cooldown=800
    attack_windup_ms=500      
    knockback_strength=16  
    color=(255, 0, 0)
    xp_reward=15
    width = 50
    height = 50

    def __init__(self, x, y):
        super().__init__(x, y)


class SwarmEnemy(Enemy):
    """
    Swarm – svak alene, farlig i gruppe.
    Kort windup og rask attack rate.
    """
    speed=100
    health=3
    damage=1
    detection_radius=700
    attack_range=5000
    attack_cooldown=800
    attack_windup_ms=500      
    knockback_strength=16  
    color=(255, 0, 0)
    xp_reward=15
    width = 50
    height = 50

    def __init__(self, x, y):
        super().__init__(x, y)


class BossEnemy(Enemy):
    """
    Boss – ekstrem utfordring.
    Lang windup gir spilleren én sjanse til å dashe unna.
    """
    speed=100
    health=3
    damage=1
    detection_radius=700
    attack_range=5000
    attack_cooldown=800
    attack_windup_ms=500      
    knockback_strength=16  
    color=(255, 0, 0)
    xp_reward=15
    width = 50
    height = 50

    def __init__(self, x, y):
        super().__init__(x, y)
    
    def draw(self, screen, camera):
        """Custom tegning for boss – gul border."""
        super().draw(screen, camera)
        import pygame
        draw_rect = camera.apply(rect)
        pygame.draw.rect(screen, (255, 255, 0), draw_rect, 3)