import pygame
import constants

class Door:
    """
    Dør som kan åpnes/lukkes. Når lukket, legger vi inn en blokkerings-rect i obstacles.
    Når åpen fjernes blokkerings-rect fra obstacles (gjøres av RoomManager).
    """
    def __init__(self, rect: pygame.Rect, color_closed=(150, 50, 50), color_open=(50, 150, 50)):
        self.rect = rect
        self.is_open = False
        self.color_closed = color_closed
        self.color_open = color_open

        # Dette er selve "veggen" når døra er lukket.
        # Vi bruker samme rect; RoomManager legger/fjerner den i world.obstacles.
        self.block_rect = rect

    def set_open(self, open_flag: bool):
        self.is_open = open_flag

    def draw(self, screen, camera):
        dr = camera.apply(self.rect)
        color = self.color_open if self.is_open else self.color_closed
        pygame.draw.rect(screen, color, dr)
        # Valgfritt outline:
        pygame.draw.rect(screen, (0, 0, 0), dr, 2)
