import pygame
import random
import math

class GameObject:
    def __init__(self, image, cut_images, x, y, vx, vy, gravity=600, angular_vel=0):
        self.original_image = image
        self.cut_images = cut_images
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.x = float(x)
        self.y = float(y)
        self.vx = vx
        self.vy = vy
        self.gravity = gravity
        self.rotation = 0.0
        self.angular_vel = angular_vel
        self.is_cut = False
        self.is_off_screen = False

    def update(self, dt):
        self.vy += self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rotation += self.angular_vel * dt
        self.rect.center = (int(self.x), int(self.y))
        if (self.y > 1080 + 100 or self.y < -100 or
            self.x > 1920 + 100 or self.x < -100):
            self.is_off_screen = True

    def draw(self, screen, offset=(0,0)):
        rotated = pygame.transform.rotate(self.image, math.degrees(self.rotation))
        new_rect = rotated.get_rect(center=self.rect.center)
        screen.blit(rotated, (new_rect.x + offset[0], new_rect.y + offset[1]))

    def slice(self):
        if self.is_cut or not self.cut_images:
            return []
        self.is_cut = True
        halves = []
        half1_img, half2_img = self.cut_images
        separation = 150
        angle = random.uniform(-0.3, 0.3)
        v1x = self.vx - separation * math.cos(angle)
        v1y = self.vy - abs(separation) * math.sin(angle)
        v2x = self.vx + separation * math.cos(angle)
        v2y = self.vy + abs(separation) * math.sin(angle)
        half1 = CutHalf(half1_img, self.x, self.y, v1x, v1y, self.gravity, random.uniform(-5,5))
        half2 = CutHalf(half2_img, self.x, self.y, v2x, v2y, self.gravity, random.uniform(-5,5))
        halves.extend([half1, half2])
        return halves

class CutHalf(GameObject):
    def __init__(self, image, x, y, vx, vy, gravity, angular_vel):
        super().__init__(image, None, x, y, vx, vy, gravity, angular_vel)
        self.is_cut = True
    def slice(self):
        return []

class Bomb(GameObject):
    def __init__(self, image, x, y, vx, vy, gravity=600, angular_vel=0):
        super().__init__(image, None, x, y, vx, vy, gravity, angular_vel)
    def slice(self):
        self.is_cut = True
        return []

class Particle:
    def __init__(self, x, y, color, lifetime=0.5):
        self.x = x
        self.y = y
        self.vx = random.uniform(-200, 200)
        self.vy = random.uniform(-300, -100)
        self.lifetime = lifetime
        self.age = 0.0
        self.color = color
        self.size = random.randint(3, 7)
    def update(self, dt):
        self.vy += 600 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.age += dt
        return self.age < self.lifetime
    def draw(self, screen, offset=(0,0)):
        alpha = max(0, int(255 * (1 - self.age / self.lifetime)))
        surf = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color, alpha), (self.size, self.size), self.size)
        screen.blit(surf, (self.x - self.size + offset[0], self.y - self.size + offset[1]))