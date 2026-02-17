import pygame
import sys
import math

# ============================================================================
#  ULTRA Mario 2D Bros - Famicom 60FPS Edition
#  Main Menu (ULTRA style) + Procedural 1-1 (No Assets)
# ============================================================================

# --- CONFIGURATION ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480
FPS = 60
TILE_SIZE = 32
SCALER = 2

# Physics (Famicom Feel)
GRAVITY = 0.6
JUMP_POWER = -14.5
MOVE_SPEED = 6
FRICTION = 0.85
ACCEL = 0.5

# Palette (same as your v0)
SKY_BLUE = (92, 148, 252)
MARIO_RED = (216, 40, 0)
MARIO_SKIN = (252, 152, 56)
MARIO_BROWN = (136, 112, 0)
GROUND_BROWN = (200, 76, 12)
BRICK_BROWN = (128, 0, 0)
BLOCK_GOLD = (252, 188, 176)
PIPE_GREEN = (0, 168, 0)
PIPE_LIGHT = (88, 248, 152)
PIPE_DARK = (0, 80, 0)
GOOMBA_BODY = (228, 92, 16)
HILL_GREEN = (0, 168, 0)
HILL_OUTLINE = (0, 80, 0)
CLOUD_WHITE = (255, 255, 255)
CASTLE_BRICK = (128, 0, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
CREAM = (255, 204, 197)

# --- ENGINE CLASSES (exactly your original, unchanged) ---

class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def apply_rect(self, rect):
        return rect.move(self.camera.topleft)

    def update(self, target):
        x = -target.rect.centerx + int(SCREEN_WIDTH / 2)
        x = min(0, x) 
        if x < self.camera.x:
            self.camera.x = x

class Entity(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vel_x = 0
        self.vel_y = 0

class Decoration(pygame.sprite.Sprite):
    def __init__(self, x, y, type_, size=1):
        super().__init__()
        self.type = type_
        self.size = size
        self.rect = pygame.Rect(x, y, 0, 0)

    def draw(self, screen, camera):
        dest = camera.apply_rect(pygame.Rect(self.rect.x, self.rect.y, 1, 1))
        if dest.x < -300 or dest.x > SCREEN_WIDTH: return
        if self.type == "hill":
            h_width = 32 * (2 + self.size)
            h_height = 32 * (self.size + 0.5)
            base_x = dest.x
            base_y = SCREEN_HEIGHT - TILE_SIZE * 2
            points = [(base_x, base_y), (base_x + h_width/2, base_y - h_height), (base_x + h_width, base_y)]
            pygame.draw.polygon(screen, HILL_GREEN, points)
            pygame.draw.polygon(screen, HILL_OUTLINE, points, 3)
            pygame.draw.rect(screen, HILL_OUTLINE, (base_x + h_width/2 - 4, base_y - h_height/2, 8, 8))
        elif self.type == "cloud":
            c_width = 32 * (1 + self.size)
            base_x = dest.x
            base_y = dest.y
            pygame.draw.rect(screen, CLOUD_WHITE, (base_x, base_y, c_width, 24), border_radius=12)
            pygame.draw.circle(screen, CLOUD_WHITE, (base_x + 16, base_y), 16)
            if self.size > 1:
                pygame.draw.circle(screen, CLOUD_WHITE, (base_x + 48, base_y), 16)
            if self.size > 2:
                pygame.draw.circle(screen, CLOUD_WHITE, (base_x + 80, base_y), 16)
        elif self.type == "bush":
            b_width = 32 * (1 + self.size)
            base_x = dest.x
            base_y = SCREEN_HEIGHT - TILE_SIZE * 2 - 16
            pygame.draw.circle(screen, PIPE_LIGHT, (base_x + 16, base_y + 8), 16)
            pygame.draw.circle(screen, PIPE_LIGHT, (base_x + b_width - 16, base_y + 8), 16)
            pygame.draw.rect(screen, PIPE_LIGHT, (base_x + 16, base_y, b_width - 32, 24))
            pygame.draw.rect(screen, BLACK, (base_x, base_y + 8, b_width, 16), 2, border_radius=5)

class Mario(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 28, 30, MARIO_RED)
        self.on_ground = False
        self.facing_right = True
        self.is_dead = False
        self.state = "IDLE"
        self.visible = True
        self.frame_timer = 0
        self.walk_frame = 0

    def update(self, tiles, enemies, game_ref):
        if self.state == "VICTORY" or not self.visible:
            return
        if self.state == "SLIDE":
            self.vel_y = 3
            self.rect.y += self.vel_y
            hit_ground = False
            for tile in tiles:
                if tile.type in ["flagpole", "castle", "castle_door", "flag_top", "cloud", "hill", "bush"]: continue
                if self.rect.colliderect(tile.rect):
                    self.rect.bottom = tile.rect.top
                    hit_ground = True
            if hit_ground:
                self.rect.x += TILE_SIZE 
                self.state = "AUTO_WALK"
                self.facing_right = True
                self.vel_x = 0
            return
        if self.state == "AUTO_WALK":
            self.vel_x = 2
            self.vel_y += GRAVITY
            self.rect.x += self.vel_x
            self.rect.y += self.vel_y
            self.frame_timer += 1
            if self.frame_timer > 10:
                self.walk_frame = (self.walk_frame + 1) % 3
                self.frame_timer = 0
            for tile in tiles:
                if tile.type not in ["castle_door", "castle", "flagpole", "flag_top"]:
                    if self.rect.colliderect(tile.rect):
                        if self.vel_y > 0:
                            self.rect.bottom = tile.rect.top
                            self.vel_y = 0
            for tile in tiles:
                if tile.type == "castle_door":
                    if self.rect.colliderect(tile.rect):
                        self.visible = False 
                        game_ref.trigger_victory()
                        return
            return
        if self.is_dead:
            self.vel_y += GRAVITY
            self.rect.y += self.vel_y
            return
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.vel_x -= ACCEL
            self.facing_right = False
        elif keys[pygame.K_RIGHT]:
            self.vel_x += ACCEL
            self.facing_right = True
        else:
            if self.vel_x > 0: self.vel_x -= FRICTION
            if self.vel_x < 0: self.vel_x += FRICTION
            if abs(self.vel_x) < 0.1: self.vel_x = 0
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vel_y = JUMP_POWER
            self.on_ground = False
        if self.vel_x > MOVE_SPEED: self.vel_x = MOVE_SPEED
        if self.vel_x < -MOVE_SPEED: self.vel_x = -MOVE_SPEED
        self.vel_y += GRAVITY
        if not self.on_ground:
            self.walk_frame = 3
        elif abs(self.vel_x) > 0.5:
            self.frame_timer += 1
            if self.frame_timer > (10 - abs(self.vel_x)):
                self.walk_frame = (self.walk_frame + 1) % 3
                self.frame_timer = 0
        else:
            self.walk_frame = 0
        self.rect.x += self.vel_x
        self.collide(tiles, "x")
        self.rect.y += self.vel_y
        self.on_ground = False
        self.collide(tiles, "y")
        hit_list = pygame.sprite.spritecollide(self, enemies, False)
        for enemy in hit_list:
            if enemy.is_alive:
                if self.vel_y > 0 and self.rect.bottom < enemy.rect.centery + 15:
                    enemy.die()
                    game_ref.score += 100
                    self.vel_y = -6
                else:
                    self.die()
        if self.rect.y > SCREEN_HEIGHT:
            self.die()

    def collide(self, tiles, direction):
        for tile in tiles:
            if tile.type in ["castle", "flag_top", "castle_door", "bush", "cloud", "hill"]: continue
            if self.rect.colliderect(tile.rect):
                if tile.type == "flagpole":
                    self.start_flag_sequence(tile)
                    return
                if direction == "x":
                    if self.vel_x > 0:
                        self.rect.right = tile.rect.left
                        self.vel_x = 0
                    elif self.vel_x < 0:
                        self.rect.left = tile.rect.right
                        self.vel_x = 0
                if direction == "y":
                    if self.vel_y > 0:
                        self.rect.bottom = tile.rect.top
                        self.vel_y = 0
                        self.on_ground = True
                    elif self.vel_y < 0:
                        self.rect.top = tile.rect.bottom
                        self.vel_y = 0

    def start_flag_sequence(self, pole):
        self.state = "SLIDE"
        self.vel_x = 0
        self.vel_y = 0
        self.rect.right = pole.rect.left + 18

    def die(self):
        if not self.is_dead:
            self.is_dead = True
            self.vel_y = -10
            self.state = "DEAD"

    def draw(self, screen, camera):
        if not self.visible: return
        pos = camera.apply(self)
        direction = 1 if self.facing_right else -1
        hx = pos.x
        hy = pos.y
        pygame.draw.rect(screen, MARIO_RED, (hx, hy, 28, 10))
        if self.facing_right:
            pygame.draw.rect(screen, MARIO_RED, (hx+12, hy, 16, 4))
        else:
            pygame.draw.rect(screen, MARIO_RED, (hx, hy, 16, 4))
        face_x = hx + (6 if self.facing_right else 4)
        pygame.draw.rect(screen, MARIO_SKIN, (face_x, hy+8, 18, 10))
        hair_x = hx + (0 if self.facing_right else 20)
        pygame.draw.rect(screen, MARIO_BROWN, (hair_x, hy+10, 8, 6))
        mus_x = hx + (20 if self.facing_right else 0)
        pygame.draw.rect(screen, BLACK, (mus_x, hy+14, 8, 4))
        pygame.draw.rect(screen, MARIO_RED, (hx+4, hy+16, 20, 8))
        pygame.draw.rect(screen, MARIO_BROWN, (hx+4, hy+20, 20, 10))
        if self.walk_frame == 0:
            arm_x = hx - 2 if self.facing_right else hx + 22
            pygame.draw.rect(screen, MARIO_BROWN, (arm_x, hy+18, 8, 8))
        else:
            swing = 4 if (self.walk_frame == 1) else -4
            arm_x = hx - 2 + (swing * direction) if self.facing_right else hx + 22 + (swing * direction)
            pygame.draw.rect(screen, MARIO_BROWN, (arm_x, hy+18, 8, 8))
        leg_l_x = hx + 2
        leg_r_x = hx + 18
        leg_y = hy + 28
        if self.walk_frame == 0:
            pygame.draw.rect(screen, MARIO_BROWN, (leg_l_x, leg_y, 10, 4))
            pygame.draw.rect(screen, MARIO_BROWN, (leg_r_x, leg_y, 10, 4))
        elif self.walk_frame == 1:
            pygame.draw.rect(screen, MARIO_BROWN, (leg_l_x, leg_y, 10, 4))
            pygame.draw.rect(screen, MARIO_BROWN, (leg_r_x + (4*direction), leg_y-2, 10, 4))
        elif self.walk_frame == 3:
            pygame.draw.rect(screen, MARIO_BROWN, (leg_l_x + (4*direction), leg_y-4, 10, 8))
        else:
            pygame.draw.rect(screen, MARIO_BROWN, (leg_l_x - (4*direction), leg_y-2, 10, 4))
            pygame.draw.rect(screen, MARIO_BROWN, (leg_r_x + (4*direction), leg_y-2, 10, 4))

class Goomba(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 32, 32, GOOMBA_BODY)
        self.vel_x = -2
        self.is_alive = True
        self.frame = 0
        self.frame_timer = 0
        self.dead_timer = 0

    def update(self, tiles):
        if not self.is_alive:
            self.dead_timer += 1
            if self.dead_timer > 30: self.kill()
            return
        self.vel_y += GRAVITY
        self.frame_timer += 1
        if self.frame_timer > 10:
            self.frame = (self.frame + 1) % 2
            self.frame_timer = 0
        self.rect.x += self.vel_x
        for tile in tiles:
            if tile.type in ["castle", "flagpole", "flag_top", "castle_door", "bush", "hill", "cloud"]: continue
            if self.rect.colliderect(tile.rect):
                if self.vel_x > 0:
                    self.rect.right = tile.rect.left
                    self.vel_x = -2
                elif self.vel_x < 0:
                    self.rect.left = tile.rect.right
                    self.vel_x = 2
        self.rect.y += self.vel_y
        for tile in tiles:
            if tile.type in ["castle", "flagpole", "flag_top", "castle_door", "bush", "hill", "cloud"]: continue
            if self.rect.colliderect(tile.rect):
                if self.vel_y > 0:
                    self.rect.bottom = tile.rect.top
                    self.vel_y = 0

    def die(self):
        self.is_alive = False

    def draw(self, screen, camera):
        pos = camera.apply(self)
        if not self.is_alive:
            pygame.draw.rect(screen, GOOMBA_BODY, (pos.x+4, pos.y+16, 24, 16))
            pygame.draw.rect(screen, BLACK, (pos.x+8, pos.y+20, 6, 2))
            pygame.draw.rect(screen, BLACK, (pos.x+18, pos.y+20, 6, 2))
            return
        pygame.draw.rect(screen, GOOMBA_BODY, (pos.x+4, pos.y+8, 24, 20))
        pygame.draw.ellipse(screen, GOOMBA_BODY, (pos.x+2, pos.y, 28, 20))
        pygame.draw.rect(screen, WHITE, (pos.x+6, pos.y+10, 8, 10))
        pygame.draw.rect(screen, WHITE, (pos.x+18, pos.y+10, 8, 10))
        pygame.draw.rect(screen, BLACK, (pos.x+8, pos.y+12, 4, 6))
        pygame.draw.rect(screen, BLACK, (pos.x+20, pos.y+12, 4, 6))
        foot_color = BLACK
        if self.frame == 0:
            pygame.draw.rect(screen, foot_color, (pos.x, pos.y+26, 10, 6))
            pygame.draw.rect(screen, foot_color, (pos.x+20, pos.y+26, 10, 6))
        else:
            pygame.draw.rect(screen, foot_color, (pos.x+2, pos.y+26, 10, 6))
            pygame.draw.rect(screen, foot_color, (pos.x+22, pos.y+26, 10, 6))

class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y, type_):
        super().__init__()
        self.type = type_
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.frame_timer = 0
        self.q_color = (255, 200, 50)

    def draw(self, screen, camera):
        pos = camera.apply_rect(self.rect)
        if pos.right < 0 or pos.left > SCREEN_WIDTH: return
        if self.type == "ground":
            pygame.draw.rect(screen, GROUND_BROWN, pos)
            pygame.draw.line(screen, CREAM, (pos.x, pos.y+2), (pos.right, pos.y+2), 2)
            pygame.draw.rect(screen, BLACK, pos, 1)
            pygame.draw.rect(screen, (150, 50, 0), (pos.x+8, pos.y+8, 4, 4))
            pygame.draw.rect(screen, (150, 50, 0), (pos.x+20, pos.y+20, 4, 4))
        elif self.type == "brick":
            pygame.draw.rect(screen, BRICK_BROWN, pos)
            pygame.draw.line(screen, BLACK, (pos.x, pos.y), (pos.right, pos.y), 2)
            pygame.draw.line(screen, BLACK, (pos.x+16, pos.y), (pos.x+16, pos.y+8), 2)
            pygame.draw.line(screen, BLACK, (pos.x, pos.y+8), (pos.right, pos.y+8), 2)
            pygame.draw.line(screen, BLACK, (pos.x+8, pos.y+8), (pos.x+8, pos.y+16), 2)
            pygame.draw.line(screen, BLACK, (pos.x+24, pos.y+8), (pos.x+24, pos.y+16), 2)
            pygame.draw.line(screen, BLACK, (pos.x, pos.y+16), (pos.right, pos.y+16), 2)
            pygame.draw.line(screen, BLACK, (pos.x+16, pos.y+16), (pos.x+16, pos.y+24), 2)
            pygame.draw.line(screen, BLACK, (pos.x, pos.y+24), (pos.right, pos.y+24), 2)
            pygame.draw.line(screen, BLACK, (pos.x+8, pos.y+24), (pos.x+8, pos.bottom), 2)
            pygame.draw.line(screen, BLACK, (pos.x+24, pos.y+24), (pos.x+24, pos.bottom), 2)
        elif self.type == "block":
            self.frame_timer = (pygame.time.get_ticks() // 200) % 3
            main_color = BLOCK_GOLD if self.frame_timer != 1 else (255, 230, 200)
            pygame.draw.rect(screen, main_color, pos)
            pygame.draw.rect(screen, BLACK, pos, 1)
            pygame.draw.rect(screen, BRICK_BROWN, (pos.x+2, pos.y+2, 4, 4))
            pygame.draw.rect(screen, BRICK_BROWN, (pos.right-6, pos.y+2, 4, 4))
            pygame.draw.rect(screen, BRICK_BROWN, (pos.x+2, pos.bottom-6, 4, 4))
            pygame.draw.rect(screen, BRICK_BROWN, (pos.right-6, pos.bottom-6, 4, 4))
            q_color = BRICK_BROWN
            pygame.draw.rect(screen, q_color, (pos.x+12, pos.y+6, 8, 4))
            pygame.draw.rect(screen, q_color, (pos.right-10, pos.y+6, 4, 8))
            pygame.draw.rect(screen, q_color, (pos.x+12, pos.y+14, 8, 4))
            pygame.draw.rect(screen, q_color, (pos.x+14, pos.y+18, 4, 4))
            pygame.draw.rect(screen, q_color, (pos.x+14, pos.y+24, 4, 4))
        elif self.type == "pipe":
            pygame.draw.rect(screen, PIPE_GREEN, pos)
            pygame.draw.rect(screen, PIPE_DARK, pos, 2)
            pygame.draw.line(screen, PIPE_LIGHT, (pos.x+6, pos.y), (pos.x+6, pos.bottom), 4)
            pygame.draw.line(screen, PIPE_LIGHT, (pos.x+18, pos.y), (pos.x+18, pos.bottom), 2)
            pygame.draw.line(screen, PIPE_DARK, (pos.x+24, pos.y), (pos.x+24, pos.bottom), 2)
        elif self.type == "pipe_top":
            pygame.draw.rect(screen, PIPE_GREEN, (pos.x-2, pos.y, 36, 32))
            pygame.draw.rect(screen, PIPE_DARK, (pos.x-2, pos.y, 36, 32), 2)
            pygame.draw.line(screen, PIPE_LIGHT, (pos.x+4, pos.y+2), (pos.x+4, pos.bottom-2), 4)
        elif self.type == "flagpole":
            pygame.draw.rect(screen, (20, 180, 20), (pos.centerx-2, pos.y, 4, 32))
        elif self.type == "flag_top":
            pygame.draw.circle(screen, (20, 180, 20), (pos.centerx, pos.bottom), 6)
        elif self.type == "castle":
            pygame.draw.rect(screen, CASTLE_BRICK, pos)
            pygame.draw.rect(screen, BLACK, pos, 1)
            pygame.draw.line(screen, BLACK, (pos.x, pos.y+16), (pos.right, pos.y+16))
            pygame.draw.line(screen, BLACK, (pos.x+16, pos.y), (pos.x+16, pos.y+16))
            pygame.draw.line(screen, BLACK, (pos.x+16, pos.y+16), (pos.x+16, pos.bottom))
        elif self.type == "castle_door":
            pygame.draw.rect(screen, BLACK, pos)
            pygame.draw.circle(screen, CASTLE_BRICK, (pos.centerx, pos.y), 16)

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("ULTRA Mario 2D Bros - Famicom 60FPS")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 24, bold=True)
        self.big_font = pygame.font.SysFont("monospace", 72, bold=True)
        self.state = "MENU"
        self.menu_timer = 0
        self.reset()

    def reset(self):
        self.tiles = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.scenery = pygame.sprite.Group()
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.mario = Mario(100, SCREEN_HEIGHT - TILE_SIZE * 5)
        self.game_over = False
        self.flag_triggered = False
        self.score = 0
        self.coins = 0
        self.world = "1-1"
        self.time = 400
        self.time_ticker = 0
        self.generate_level()

    def trigger_victory(self):
        self.mario.state = "VICTORY"
        self.game_over = True

    def add_pipe(self, x, height):
        for h in range(height):
            self.tiles.add(Tile(x * TILE_SIZE, SCREEN_HEIGHT - (2+h) * TILE_SIZE, "pipe"))
        self.tiles.add(Tile(x * TILE_SIZE, SCREEN_HEIGHT - (2+height) * TILE_SIZE, "pipe_top"))

    def add_castle(self, x):
        for cx in range(5):
            for cy in range(2):
                self.tiles.add(Tile((x + cx) * TILE_SIZE, SCREEN_HEIGHT - (2+cy)*TILE_SIZE, "castle"))
        for cx in range(1, 4):
            for cy in range(2, 4):
                self.tiles.add(Tile((x + cx) * TILE_SIZE, SCREEN_HEIGHT - (2+cy)*TILE_SIZE, "castle"))
        self.tiles.add(Tile((x + 2) * TILE_SIZE, SCREEN_HEIGHT - 6*TILE_SIZE, "castle"))
        self.tiles.add(Tile((x + 2) * TILE_SIZE, SCREEN_HEIGHT - 3*TILE_SIZE, "castle_door"))

    def generate_level(self):
        map_width = 230
        pits = [69, 70, 86, 87, 88]
        for x in range(map_width):
            if x not in pits:
                self.tiles.add(Tile(x * TILE_SIZE, SCREEN_HEIGHT - TILE_SIZE, "ground"))
                self.tiles.add(Tile(x * TILE_SIZE, SCREEN_HEIGHT - TILE_SIZE * 2, "ground"))
        for x in range(0, map_width, 16):
            self.scenery.add(Decoration((x + 0) * TILE_SIZE, 0, "hill", size=2))
            self.scenery.add(Decoration((x + 16) * TILE_SIZE, 0, "hill", size=1))
            self.scenery.add(Decoration((x + 11) * TILE_SIZE, 0, "bush", size=2))
            self.scenery.add(Decoration((x + 23) * TILE_SIZE, 0, "bush", size=0))
            self.scenery.add(Decoration((x + 8) * TILE_SIZE, 100, "cloud", size=0))
            self.scenery.add(Decoration((x + 19) * TILE_SIZE, 60, "cloud", size=0))
            self.scenery.add(Decoration((x + 27) * TILE_SIZE, 80, "cloud", size=2))
        self.add_pipe(28, 1)
        self.add_pipe(38, 1)
        self.add_pipe(46, 1)
        self.add_pipe(57, 1)
        structures = [
            (16, 5, 'block'), (20, 5, 'brick'), (21, 5, 'block'), (22, 5, 'brick'),
            (23, 5, 'block'), (24, 5, 'brick'), (22, 9, 'block'),
            (77, 5, 'brick'), (78, 5, 'block'), (79, 5, 'brick'),
            (80, 9, 'brick'), (81, 9, 'brick'), (82, 9, 'brick'), (83, 9, 'brick'),
            (84, 9, 'brick'), (85, 9, 'brick'), (86, 9, 'brick'), (87, 9, 'brick'),
            (91, 9, 'brick'), (92, 9, 'brick'), (93, 9, 'block'), (94, 9, 'brick'),
            (94, 5, 'brick'), (100, 5, 'brick'), (101, 5, 'brick'), (102, 5, 'block'), 
            (103, 5, 'brick'), (118, 5, 'brick'), (121, 9, 'brick'), (122, 9, 'brick'), 
            (123, 9, 'brick'), (128, 9, 'brick'), (129, 5, 'block'), (130, 5, 'block'), (131, 5, 'brick'),
        ]
        for s in structures:
            self.tiles.add(Tile(s[0] * TILE_SIZE, SCREEN_HEIGHT - (2+s[1]) * TILE_SIZE, s[2]))
        def build_stair(start_x, height, reverse=False):
            for i in range(height):
                for h in range(i + 1):
                    x = start_x + (i if not reverse else (height - 1 - i))
                    self.tiles.add(Tile(x * TILE_SIZE, SCREEN_HEIGHT - (3+h)*TILE_SIZE, "block"))
        build_stair(134, 4)
        build_stair(140, 4, True)
        build_stair(148, 4)
        build_stair(152, 4, True)
        build_stair(181, 8)
        flag_x = 198
        for i in range(1, 10):
            self.tiles.add(Tile(flag_x * TILE_SIZE, SCREEN_HEIGHT - (2+i)*TILE_SIZE, "flagpole"))
        self.tiles.add(Tile(flag_x * TILE_SIZE, SCREEN_HEIGHT - (2+10)*TILE_SIZE, "flag_top"))
        self.tiles.add(Tile(flag_x * TILE_SIZE, SCREEN_HEIGHT - 3*TILE_SIZE, "block"))
        self.add_castle(202)
        goomba_locs = [22, 40, 50, 51, 80, 82, 97, 99, 114, 116, 124, 126, 128, 174, 176]
        for loc in goomba_locs:
            self.enemies.add(Goomba(loc * TILE_SIZE, SCREEN_HEIGHT - TILE_SIZE * 5))

    def draw_menu(self):
        self.screen.fill(SKY_BLUE)
        pygame.draw.rect(self.screen, GROUND_BROWN, (0, SCREEN_HEIGHT - 64, SCREEN_WIDTH, 64))
        pygame.draw.line(self.screen, CREAM, (0, SCREEN_HEIGHT - 62), (SCREEN_WIDTH, SCREEN_HEIGHT - 62), 4)
        ultra = self.big_font.render("ULTRA", True, MARIO_RED)
        mario_t = self.big_font.render("MARIO", True, BLOCK_GOLD)
        bros = self.font.render("2D BROS", True, WHITE)
        self.screen.blit(ultra, (SCREEN_WIDTH//2 - ultra.get_width()//2 - 80, 80))
        self.screen.blit(mario_t, (SCREEN_WIDTH//2 - mario_t.get_width()//2 + 90, 150))
        self.screen.blit(bros, (SCREEN_WIDTH//2 - bros.get_width()//2, 230))
        top = self.font.render("TOP-0042069", True, WHITE)
        self.screen.blit(top, (SCREEN_WIDTH//2 - top.get_width()//2, 290))
        self.menu_timer += 1
        if (self.menu_timer // 25) % 2 == 0:
            start_txt = self.font.render("PRESS START", True, (255, 255, 100))
            self.screen.blit(start_txt, (SCREEN_WIDTH//2 - start_txt.get_width()//2, 350))
        copy = self.font.render("© 1999-2026 AC HOLDINGS CATSDK", True, CREAM)
        self.screen.blit(copy, (SCREEN_WIDTH//2 - copy.get_width()//2, 420))

    def draw_hud(self):
        mario_lbl = self.font.render("MARIO", True, WHITE)
        world_lbl = self.font.render("WORLD", True, WHITE)
        time_lbl = self.font.render("TIME", True, WHITE)
        score_val = self.font.render(f"{self.score:06d}", True, WHITE)
        coin_val = self.font.render(f"x{self.coins:02d}", True, WHITE)
        world_val = self.font.render(self.world, True, WHITE)
        time_val = self.font.render(f"{self.time:03d}", True, WHITE)
        self.screen.blit(mario_lbl, (40, 20))
        self.screen.blit(score_val, (40, 45))
        self.screen.blit(coin_val, (300, 45))
        self.screen.blit(world_lbl, (480, 20))
        self.screen.blit(world_val, (490, 45))
        self.screen.blit(time_lbl, (680, 20))
        self.screen.blit(time_val, (690, 45))

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if self.state == "MENU":
                        if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                            self.state = "PLAYING"
                    if event.key == pygame.K_r and self.state != "MENU":
                        self.state = "PLAYING"
                        self.reset()

            if self.state == "PLAYING":
                if not self.game_over:
                    self.mario.update(self.tiles, self.enemies, self)
                    self.enemies.update(self.tiles)
                    self.camera.update(self.mario)
                    if self.mario.state == "SLIDE" and not self.flag_triggered:
                        self.flag_triggered = True
                        self.enemies.empty()
                    if self.mario.state == "DEAD" and self.mario.rect.y > SCREEN_HEIGHT + 100:
                        self.game_over = True
                    if self.mario.state == "VICTORY":
                        self.game_over = True
                    if self.mario.state not in ["DEAD", "VICTORY"]:
                        self.time_ticker += 1
                        if self.time_ticker >= 60:
                            self.time -= 1
                            self.time_ticker = 0
                            if self.time <= 0:
                                self.mario.die()

            if self.state == "MENU":
                self.draw_menu()
            else:
                self.screen.fill(SKY_BLUE)
                for decor in self.scenery:
                    decor.draw(self.screen, self.camera)
                for tile in self.tiles:
                    tile.draw(self.screen, self.camera)
                for enemy in self.enemies:
                    enemy.draw(self.screen, self.camera)
                self.mario.draw(self.screen, self.camera)
                self.draw_hud()
                if self.game_over:
                    if self.mario.state == "VICTORY":
                        msg = "COURSE CLEAR!"
                        txt = self.font.render(msg, True, WHITE)
                        self.screen.blit(txt, (SCREEN_WIDTH//2 - txt.get_width()//2, SCREEN_HEIGHT//3))
                        if self.time > 0:
                            countdown_step = 5 if self.time >= 5 else self.time
                            self.time -= countdown_step
                            self.score += 50 * countdown_step
                        else:
                            sub = self.font.render("Press R to Play Again", True, WHITE)
                            self.screen.blit(sub, (SCREEN_WIDTH//2 - sub.get_width()//2, SCREEN_HEIGHT//2))
                    else:
                        txt = self.font.render("GAME OVER", True, WHITE)
                        sub = self.font.render("Press R to Restart", True, WHITE)
                        self.screen.blit(txt, (SCREEN_WIDTH//2 - txt.get_width()//2, SCREEN_HEIGHT//3))
                        self.screen.blit(sub, (SCREEN_WIDTH//2 - sub.get_width()//2, SCREEN_HEIGHT//2))

            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()
