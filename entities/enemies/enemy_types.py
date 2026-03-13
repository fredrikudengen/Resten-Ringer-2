from .enemy import Enemy


class FastEnemy(Enemy):
    """
    Rask, smidig fiende med lav health.
    Kort windup – angriper raskt og presist.
    """
    def __init__(self, x, y):
        self.width = 50
        self.height = 50

        super().__init__(x, y)

        self.speed=100
        self.health=3
        self.damage=1
        self.detection_radius=700
        self.attack_range=5000
        self.attack_cooldown=800
        self.attack_windup_ms=500      
        self.knockback_strength=16  
        self.color=(255, 0, 0)
        self.xp_reward=15


class SlowEnemy(Enemy):
    """
    Treg, robust tank.
    Lang windup – tydelig telegraf, men gjør stor skade og knockback.
    """
    def __init__(self, x, y):
        self.width = 50
        self.height = 50

        super().__init__(x, y)

        self.speed=100
        self.health=3
        self.damage=1
        self.detection_radius=700
        self.attack_range=5000
        self.attack_cooldown=800
        self.attack_windup_ms=500      
        self.knockback_strength=16      
        self.color=(255, 0, 0)
        self.wander_radius=4
        self.xp_reward=15


class TankEnemy(Enemy):
    """
    Ekstremt robust boss-lignende fiende.
    Veldig lang windup, massiv skade og knockback.
    """
    def __init__(self, x, y):
        self.width = 50
        self.height = 50

        super().__init__(x, y)

        self.speed=100
        self.health=3
        self.damage=1
        self.detection_radius=700
        self.attack_range=5000
        self.attack_cooldown=800
        self.attack_windup_ms=500      
        self.knockback_strength=16  
        self.color=(255, 0, 0)
        self.xp_reward=15


class ScoutEnemy(Enemy):
    """
    Scout – oppdager tidlig, men er svak i nærkamp.
    """
    def __init__(self, x, y):
        self.width = 50
        self.height = 50

        super().__init__(x, y)

        self.speed=100
        self.health=3
        self.damage=1
        self.detection_radius=700
        self.attack_range=5000
        self.attack_cooldown=800
        self.attack_windup_ms=500      
        self.knockback_strength=16  
        self.color=(255, 0, 0)
        self.xp_reward=15


class AssassinEnemy(Enemy):
    """
    Assassin – balansert og dødelig.
    Middels windup, høy skade.
    """
    def __init__(self, x, y):
        self.width = 50
        self.height = 50

        super().__init__(x, y)

        self.speed=100
        self.health=3
        self.damage=1
        self.detection_radius=700
        self.attack_range=5000
        self.attack_cooldown=800
        self.attack_windup_ms=500      
        self.knockback_strength=16  
        self.color=(255, 0, 0)
        self.xp_reward=15

class BruteEnemy(Enemy):
    """
    Brute – kraftig i nærkamp.
    Lang windup men massiv skade og knockback.
    """
    def __init__(self, x, y):
        self.width = 50
        self.height = 50

        super().__init__(x, y)

        self.speed=100
        self.health=3
        self.damage=1
        self.detection_radius=700
        self.attack_range=5000
        self.attack_cooldown=800
        self.attack_windup_ms=500      
        self.knockback_strength=16  
        self.color=(255, 0, 0)
        self.xp_reward=15


class SwarmEnemy(Enemy):
    """
    Swarm – svak alene, farlig i gruppe.
    Kort windup og rask attack rate.
    """
    def __init__(self, x, y):
        self.width = 50
        self.height = 50

        super().__init__(x, y)

        self.speed=100
        self.health=3
        self.damage=1
        self.detection_radius=700
        self.attack_range=5000
        self.attack_cooldown=800
        self.attack_windup_ms=500      
        self.knockback_strength=16  
        self.color=(255, 0, 0)
        self.xp_reward=15


class BossEnemy(Enemy):
    """
    Boss – ekstrem utfordring.
    Lang windup gir spilleren én sjanse til å dashe unna.
    """
    def __init__(self, x, y):
        self.width = 50
        self.height = 50

        super().__init__(x, y)

        self.speed=100
        self.health=3
        self.damage=1
        self.detection_radius=700
        self.attack_range=5000
        self.attack_cooldown=800
        self.attack_windup_ms=500      
        self.knockback_strength=16  
        self.color=(255, 0, 0)
        self.xp_reward=15
    
    def draw(self, screen, camera):
        """Custom tegning for boss – gul border."""
        super().draw(screen, camera)
        import pygame
        draw_rect = camera.apply(self.rect)
        pygame.draw.rect(screen, (255, 255, 0), draw_rect, 3)