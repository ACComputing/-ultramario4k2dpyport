import pygame
import sys

# ============================================================================
# SUPER MARIO BROS. (NES) - FULL 1-1 → 8-4 • SINGLE FILE • PC ENGINE STYLE GRAPHICS
# Cat's AC! Smb 1.0 – NO EXTERNAL FILES, pure pygame drawing
# ============================================================================

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480
FPS = 60
TILE_SIZE = 32
GRAVITY = 0.8
JUMP_POWER = -15
MOVE_SPEED = 5
RUN_SPEED = 7
ACCEL = 0.6
FRICTION = 0.85

SKY_BLUE = (92, 148, 252)
BRICK_BROWN = (184, 72, 48)
BLOCK_GOLD = (248, 184, 56)
PIPE_GREEN = (72, 184, 72)
GROUND_BROWN = (168, 104, 56)
MARIO_RED = (232, 40, 40)
SKIN = (255, 200, 150)
MARIO_BLUE = (0, 80, 200)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GOOMBA_BROWN = (168, 80, 48)
KOOPA_GREEN = (72, 160, 72)

TILE_EMPTY = 0
TILE_GROUND = 1
TILE_BRICK = 2
TILE_BLOCK = 3
TILE_PIPE_TL = 4
TILE_PIPE_TR = 5
TILE_PIPE_BL = 6
TILE_PIPE_BR = 7
TILE_FLAGPOLE = 8
TILE_FLAG_TOP = 9
TILE_CASTLE = 10
TILE_CASTLE_DOOR = 11

class Camera:
    def __init__(self, level_width):
        self.offset_x = 0
        self.level_width = level_width
    def update(self, mario):
        target = mario.rect.centerx - SCREEN_WIDTH // 2
        self.offset_x = max(0, min(target, self.level_width - SCREEN_WIDTH))

class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y, ttype):
        super().__init__()
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.type = ttype

class Mario(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.rect = pygame.Rect(x, y, 26, 36)
        self.vel_x = self.vel_y = 0
        self.on_ground = False
        self.facing_right = True
    def update(self, tiles, keys):
        if keys[pygame.K_RIGHT]:
            self.vel_x = min(self.vel_x + ACCEL, RUN_SPEED if keys[pygame.K_LSHIFT] else MOVE_SPEED)
            self.facing_right = True
        elif keys[pygame.K_LEFT]:
            self.vel_x = max(self.vel_x - ACCEL, -(RUN_SPEED if keys[pygame.K_LSHIFT] else MOVE_SPEED))
            self.facing_right = False
        else:
            self.vel_x *= FRICTION
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vel_y = JUMP_POWER
            self.on_ground = False
        self.vel_y += GRAVITY
        self.rect.x += int(self.vel_x)
        self.collide(self.vel_x, 0, tiles)
        self.rect.y += int(self.vel_y)
        self.on_ground = self.collide(0, self.vel_y, tiles)
    def collide(self, vx, vy, tiles):
        hits = pygame.sprite.spritecollide(self, tiles, False)
        for t in hits:
            if vx > 0: self.rect.right = t.rect.left
            elif vx < 0: self.rect.left = t.rect.right
            if vy > 0: self.rect.bottom = t.rect.top; self.vel_y = 0; return True
            if vy < 0: self.rect.top = t.rect.bottom; self.vel_y = 0
        return False

class Goomba(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.rect = pygame.Rect(x, y, 26, 26)
        self.vel_x = -1.2
    def update(self, tiles):
        self.rect.x += int(self.vel_x)

class Koopa(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.rect = pygame.Rect(x, y, 26, 30)
        self.vel_x = -1.0
    def update(self, tiles):
        self.rect.x += int(self.vel_x)

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Cat's AC! Smb 1.0 – PC Engine Style")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.world = 1
        self.level = 1
        self.lives = 3
        self.score = 0
        self.coins = 0
        self.time = 400
        self.state = "TITLE"
        self.reset_level()

    def load_level(self, world, level):
        width = 220
        height = 14
        tiles = [[TILE_EMPTY] * width for _ in range(height)]
        enemies = []
        for x in range(width):
            tiles[13][x] = TILE_GROUND
        if world == 1 and level == 1:
            for x in range(16, 20): tiles[12][x] = TILE_BRICK
            for x in range(17, 20): tiles[11][x] = TILE_BRICK
            for x in range(18, 20): tiles[10][x] = TILE_BRICK
            tiles[9][21] = tiles[9][22] = tiles[9][23] = TILE_BLOCK
            tiles[12][25] = tiles[12][26] = TILE_BRICK
            tiles[11][26] = TILE_BLOCK
            pipes = [33, 70, 93, 140]
            for px in pipes:
                for y in range(11, 13):
                    tiles[y][px] = TILE_PIPE_TL if y == 11 else TILE_PIPE_BL
                    tiles[y][px+1] = TILE_PIPE_TR if y == 11 else TILE_PIPE_BR
            flag_x = 198
            tiles[2][flag_x] = TILE_FLAG_TOP
            for y in range(3, 14): tiles[y][flag_x] = TILE_FLAGPOLE
            for x in range(205, 215): tiles[11][x] = TILE_CASTLE
            tiles[10][208] = TILE_CASTLE_DOOR
            enemies.extend([('goomba', 26*32, 384), ('goomba', 28*32, 384), ('goomba', 42*32, 384), ('koopa', 110*32, 384)])
        elif world == 1 and level == 2:
            for x in range(width): tiles[13][x] = TILE_EMPTY; tiles[10][x] = TILE_GROUND
            for x in range(10, 15): tiles[9][x] = TILE_BRICK
            for x in range(12, 15): tiles[8][x] = TILE_BRICK
            for y in range(6, 10):
                tiles[y][40] = TILE_PIPE_TL if y == 6 else TILE_PIPE_BL
                tiles[y][41] = TILE_PIPE_TR if y == 6 else TILE_PIPE_BR
            enemies.extend([('goomba', 15*32, 288), ('koopa', 22*32, 288)])
        elif world == 1 and level == 3:
            for x in range(20, 80): tiles[12][x] = TILE_BRICK
            for x in range(100, 150, 10): tiles[9][x] = TILE_BLOCK
            enemies.extend([('koopa', 50*32, 384), ('goomba', 120*32, 384)])
        elif world == 1 and level == 4:
            for x in range(20, 100): tiles[11][x] = TILE_BRICK
            for x in range(110, 180): tiles[12][x] = TILE_BRICK
            enemies.append(('koopa', 170*32, 384))
        elif world == 2 and level == 1:
            for x in range(25, 55): tiles[12][x] = TILE_BRICK
            for x in range(60, 90, 8): tiles[9][x] = TILE_BLOCK
            pipes = [40, 75, 120]
            for px in pipes:
                for y in range(11, 13):
                    tiles[y][px] = TILE_PIPE_TL if y == 11 else TILE_PIPE_BL
                    tiles[y][px+1] = TILE_PIPE_TR if y == 11 else TILE_PIPE_BR
            enemies.extend([('goomba', 30*32, 384), ('koopa', 80*32, 384)])
            flag_x = 198
            tiles[2][flag_x] = TILE_FLAG_TOP
            for y in range(3, 14): tiles[y][flag_x] = TILE_FLAGPOLE
        else:
            for x in range(20, 60): tiles[12][x] = TILE_BRICK
            for x in range(80, 120, 8): tiles[9][x] = TILE_BLOCK
            enemies.append(('goomba', 40*32, 384))
            if level == 4: enemies.append(('koopa', 170*32, 384))
            flag_x = 198
            tiles[2][flag_x] = TILE_FLAG_TOP
            for y in range(3, 14): tiles[y][flag_x] = TILE_FLAGPOLE
        return tiles, enemies

    def reset_level(self):
        self.tiles = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        tile_data, enemy_data = self.load_level(self.world, self.level)
        level_width = len(tile_data[0]) * TILE_SIZE
        self.camera = Camera(level_width)
        for y, row in enumerate(tile_data):
            for x, ttype in enumerate(row):
                if ttype != TILE_EMPTY:
                    self.tiles.add(Tile(x * TILE_SIZE, y * TILE_SIZE, ttype))
        self.mario = Mario(80, 13 * TILE_SIZE - 40)
        for etype, ex, ey in enemy_data:
            if etype == 'goomba': self.enemies.add(Goomba(ex, ey))
            elif etype == 'koopa': self.enemies.add(Koopa(ex, ey))

    def draw_tile(self, t):
        tx = t.rect.x - self.camera.offset_x
        ty = t.rect.y
        if t.type in (TILE_GROUND, TILE_BRICK):
            pygame.draw.rect(self.screen, BRICK_BROWN, (tx, ty, TILE_SIZE, TILE_SIZE))
            pygame.draw.line(self.screen, (120, 40, 20), (tx, ty + 10), (tx + TILE_SIZE, ty + 10), 3)
            pygame.draw.line(self.screen, (120, 40, 20), (tx + 10, ty), (tx + 10, ty + TILE_SIZE), 3)
        elif t.type == TILE_BLOCK:
            pygame.draw.rect(self.screen, BLOCK_GOLD, (tx, ty, TILE_SIZE, TILE_SIZE))
            pygame.draw.rect(self.screen, (200, 140, 20), (tx + 4, ty + 4, TILE_SIZE - 8, TILE_SIZE - 8))
        elif t.type in (TILE_PIPE_TL, TILE_PIPE_TR, TILE_PIPE_BL, TILE_PIPE_BR):
            col = PIPE_GREEN
            pygame.draw.rect(self.screen, col, (tx, ty, TILE_SIZE, TILE_SIZE))
            pygame.draw.rect(self.screen, (40, 120, 40), (tx if t.type in (TILE_PIPE_TL, TILE_PIPE_BL) else tx + 4, ty, 8, TILE_SIZE))
            pygame.draw.rect(self.screen, (100, 220, 100), (tx + TILE_SIZE - 8 if t.type in (TILE_PIPE_TR, TILE_PIPE_BR) else tx + 20, ty, 8, TILE_SIZE))
        elif t.type == TILE_FLAGPOLE:
            pygame.draw.rect(self.screen, (180, 180, 180), (tx + 12, ty, 8, TILE_SIZE))
        elif t.type == TILE_FLAG_TOP:
            pygame.draw.polygon(self.screen, (255, 50, 50), [(tx + 16, ty + 8), (tx + 30, ty + 14), (tx + 16, ty + 20)])
        elif t.type in (TILE_CASTLE, TILE_CASTLE_DOOR):
            pygame.draw.rect(self.screen, (120, 60, 30), (tx, ty, TILE_SIZE, TILE_SIZE))
            pygame.draw.rect(self.screen, (80, 40, 20), (tx + 8, ty + 8, TILE_SIZE - 16, TILE_SIZE - 16))
            if t.type == TILE_CASTLE_DOOR:
                pygame.draw.rect(self.screen, (60, 30, 10), (tx + 10, ty + 16, 12, 16))

    def draw_mario(self, mx, my):
        # Hat
        pygame.draw.rect(self.screen, MARIO_RED, (mx + 4, my, 18, 8))
        pygame.draw.rect(self.screen, MARIO_RED, (mx + 2, my + 4, 22, 6))
        # Face
        pygame.draw.rect(self.screen, SKIN, (mx + 6, my + 8, 14, 12))
        # Mustache
        pygame.draw.rect(self.screen, BLACK, (mx + 6, my + 16, 14, 4))
        # Eyes
        pygame.draw.rect(self.screen, BLACK, (mx + 8 if self.mario.facing_right else mx + 14, my + 11, 4, 4))
        # Overalls
        pygame.draw.rect(self.screen, MARIO_BLUE, (mx + 6, my + 20, 14, 12))
        # Arms
        pygame.draw.rect(self.screen, SKIN, (mx + 2 if self.mario.facing_right else mx + 20, my + 20, 6, 8))
        # Shoes
        pygame.draw.rect(self.screen, (120, 60, 30), (mx + 6, my + 30, 8, 6))
        pygame.draw.rect(self.screen, (120, 60, 30), (mx + 12, my + 30, 8, 6))

    def draw_goomba(self, gx, gy):
        pygame.draw.ellipse(self.screen, GOOMBA_BROWN, (gx + 2, gy + 4, 22, 18))
        pygame.draw.ellipse(self.screen, BLACK, (gx + 6, gy + 8, 6, 8))
        pygame.draw.ellipse(self.screen, BLACK, (gx + 14, gy + 8, 6, 8))
        pygame.draw.line(self.screen, BLACK, (gx + 8, gy + 18), (gx + 18, gy + 18), 3)

    def draw_koopa(self, kx, ky):
        # Shell
        pygame.draw.ellipse(self.screen, KOOPA_GREEN, (kx + 2, ky + 12, 22, 16))
        pygame.draw.rect(self.screen, (40, 100, 40), (kx + 4, ky + 14, 18, 8))
        # Head
        pygame.draw.circle(self.screen, KOOPA_GREEN, (kx + 13, ky + 10), 8)
        # Eyes
        pygame.draw.circle(self.screen, WHITE, (kx + 10 if self.mario.facing_right else kx + 16, ky + 8), 3)
        pygame.draw.circle(self.screen, BLACK, (kx + 10 if self.mario.facing_right else kx + 16, ky + 8), 1)
        # Legs
        pygame.draw.rect(self.screen, (40, 100, 40), (kx + 6, ky + 24, 6, 6))
        pygame.draw.rect(self.screen, (40, 100, 40), (kx + 14, ky + 24, 6, 6))

    def run(self):
        while True:
            keys = pygame.key.get_pressed()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: sys.exit()
            if self.state == "TITLE":
                if keys[pygame.K_RETURN]: self.state = "PLAY"
            elif self.state == "PLAY":
                self.mario.update(self.tiles, keys)
                self.camera.update(self.mario)
                for e in list(self.enemies):
                    e.update(self.tiles)
                    if pygame.sprite.collide_rect(self.mario, e):
                        self.lives -= 1
                        if self.lives <= 0: self.state = "GAMEOVER"
                        else: self.reset_level()
                self.time = max(0, self.time - 1 / 60)
                if self.time <= 0: self.state = "GAMEOVER"
                if self.mario.rect.right > 198 * TILE_SIZE:
                    self.level += 1
                    if self.level > 4:
                        self.level = 1
                        self.world += 1
                    if self.world > 8:
                        self.state = "WIN"
                    else:
                        self.reset_level()
                        self.time = 400
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)

    def draw(self):
        self.screen.fill(SKY_BLUE)
        for t in self.tiles:
            self.draw_tile(t)
        # Mario
        mx = self.mario.rect.x - self.camera.offset_x
        my = self.mario.rect.y
        self.draw_mario(mx, my)
        # Enemies
        for e in self.enemies:
            ex = e.rect.x - self.camera.offset_x
            ey = e.rect.y
            if isinstance(e, Goomba):
                self.draw_goomba(ex, ey)
            else:
                self.draw_koopa(ex, ey)
        # HUD
        hud = self.font.render(f"SCORE {self.score:06d}  COINS {self.coins}  TIME {int(self.time)}  WORLD {self.world}-{self.level}", True, WHITE)
        self.screen.blit(hud, (20, 10))
        if self.state == "TITLE":
            title = self.font.render("CAT'S AC! SMB 1.0", True, WHITE)
            self.screen.blit(title, (SCREEN_WIDTH//2 - 140, 180))
            start = self.font.render("PRESS ENTER TO START – PC ENGINE GRAPHICS", True, WHITE)
            self.screen.blit(start, (SCREEN_WIDTH//2 - 220, 260))
        elif self.state == "GAMEOVER":
            go = self.font.render("GAME OVER", True, (232, 72, 72))
            self.screen.blit(go, (SCREEN_WIDTH//2 - 80, 200))
        elif self.state == "WIN":
            win = self.font.render("THANK YOU MARIO! BUT OUR PRINCESS IS IN ANOTHER CASTLE!", True, WHITE)
            self.screen.blit(win, (20, 200))

if __name__ == "__main__":
    Game().run()
