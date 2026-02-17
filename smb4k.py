import pygame
import sys

# ============================================================================
#  Super Mario Python 1-1 (Procedural / No Assets)
#  Python 3.14 + Pygame-ce
# ============================================================================

# --- CONFIGURATION ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480
FPS = 60
TILE_SIZE = 32

# Physics
GRAVITY = 0.5
JUMP_POWER = -13
MOVE_SPEED = 5
FRICTION = 0.8
ACCEL = 0.4

# Palette (NES Style)
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
GOOMBA_COLOR = (112, 28, 0)
CLOUD_WHITE = (255, 255, 255)
CASTLE_BRICK = (128, 0, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# --- ENGINE CLASSES ---

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

class Mario(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 28, 32, MARIO_RED)
        self.on_ground = False
        self.facing_right = True
        self.is_dead = False
        self.state = "IDLE"
        self.visible = True

    def update(self, tiles, enemies, game_ref):
        if self.state == "VICTORY" or not self.visible:
            return

        # Flagpole Slide Animation
        if self.state == "SLIDE":
            self.vel_y = 3
            self.rect.y += self.vel_y
            hit_ground = False
            for tile in tiles:
                if tile.type in ["flagpole", "castle", "castle_door", "flag_top"]:
                    continue
                if self.rect.colliderect(tile.rect):
                    self.rect.bottom = tile.rect.top
                    hit_ground = True
            if hit_ground:
                # Hop off pole
                self.rect.x += TILE_SIZE 
                self.state = "AUTO_WALK"
                self.facing_right = True
                self.vel_x = 0
            return

        # Auto-walk to castle
        if self.state == "AUTO_WALK":
            self.vel_x = 2
            self.vel_y += GRAVITY
            self.rect.x += self.vel_x
            self.rect.y += self.vel_y
            
            # Check collisions with ground only
            for tile in tiles:
                if tile.type not in ["castle_door", "castle", "flagpole", "flag_top"]:
                    if self.rect.colliderect(tile.rect):
                        if self.vel_y > 0:
                            self.rect.bottom = tile.rect.top
                            self.vel_y = 0

            # Check collision with castle door
            for tile in tiles:
                if tile.type == "castle_door":
                    if self.rect.colliderect(tile.rect):
                        self.visible = False # Disappear into castle
                        game_ref.trigger_victory()
                        return
            return

        # Death Animation
        if self.is_dead:
            self.vel_y += GRAVITY
            self.rect.y += self.vel_y
            return

        # Input Handling
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.vel_x -= ACCEL
            self.facing_right = False
        elif keys[pygame.K_RIGHT]:
            self.vel_x += ACCEL
            self.facing_right = True
        else:
            self.vel_x *= FRICTION

        if keys[pygame.K_SPACE] and self.on_ground:
            self.vel_y = JUMP_POWER
            self.on_ground = False

        # Physics Limits
        if self.vel_x > MOVE_SPEED: self.vel_x = MOVE_SPEED
        if self.vel_x < -MOVE_SPEED: self.vel_x = -MOVE_SPEED

        self.vel_y += GRAVITY

        # X Movement & Collision
        self.rect.x += self.vel_x
        self.collide(tiles, "x")

        # Y Movement & Collision
        self.rect.y += self.vel_y
        self.on_ground = False
        self.collide(tiles, "y")

        # Enemy Interaction
        hit_list = pygame.sprite.spritecollide(self, enemies, False)
        for enemy in hit_list:
            if enemy.is_alive:
                # Mario is falling onto enemy
                if self.vel_y > 0 and self.rect.bottom < enemy.rect.centery + 10:
                    enemy.die()
                    game_ref.score += 100
                    self.vel_y = -6 # Bounce
                else:
                    self.die()

        # Pit Death
        if self.rect.y > SCREEN_HEIGHT:
            self.die()

    def collide(self, tiles, direction):
        for tile in tiles:
            if self.rect.colliderect(tile.rect):
                if tile.type == "flagpole":
                    self.start_flag_sequence(tile)
                    return
                elif tile.type == "castle":
                    continue # Non-solid background object
                elif tile.type == "castle_door":
                    continue 

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
        self.rect.right = pole.rect.left + 14

    def die(self):
        if not self.is_dead:
            self.is_dead = True
            self.vel_y = -10
            self.state = "DEAD"

    def draw(self, screen, camera):
        if not self.visible: return
        pos = camera.apply(self)

        # Draw Mario (Pixel Art Style via Rects)
        # Head
        pygame.draw.rect(screen, MARIO_RED, (pos.x, pos.y, 28, 8))
        # Brim
        off_x = 10 if self.facing_right else -4
        pygame.draw.rect(screen, MARIO_RED, (pos.x + off_x, pos.y, 22, 4))
        # Face
        pygame.draw.rect(screen, MARIO_SKIN, (pos.x+4, pos.y+8, 20, 8))
        # Body
        pygame.draw.rect(screen, MARIO_RED, (pos.x+4, pos.y+16, 20, 10))
        # Straps
        pygame.draw.rect(screen, MARIO_RED, (pos.x+4, pos.y+16, 4, 8))
        pygame.draw.rect(screen, MARIO_RED, (pos.x+20, pos.y+16, 4, 8))
        # Arms
        arm_x = -2 if self.facing_right else 24
        pygame.draw.rect(screen, MARIO_BROWN, (pos.x + arm_x, pos.y+16, 6, 10))
        # Legs
        pygame.draw.rect(screen, MARIO_BROWN, (pos.x, pos.y+26, 10, 6))
        pygame.draw.rect(screen, MARIO_BROWN, (pos.x+18, pos.y+26, 10, 6))

class Goomba(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 32, 32, GOOMBA_COLOR)
        self.vel_x = -1
        self.is_alive = True

    def update(self, tiles):
        if not self.is_alive: return

        self.vel_y += GRAVITY
        
        # Move X
        self.rect.x += self.vel_x
        for tile in tiles:
            if tile.type in ["castle", "flagpole", "flag_top", "castle_door"]: continue
            if self.rect.colliderect(tile.rect):
                if self.vel_x > 0:
                    self.rect.right = tile.rect.left
                    self.vel_x = -1
                elif self.vel_x < 0:
                    self.rect.left = tile.rect.right
                    self.vel_x = 1

        # Move Y
        self.rect.y += self.vel_y
        for tile in tiles:
            if tile.type in ["castle", "flagpole", "flag_top", "castle_door"]: continue
            if self.rect.colliderect(tile.rect):
                if self.vel_y > 0:
                    self.rect.bottom = tile.rect.top
                    self.vel_y = 0

    def die(self):
        self.is_alive = False

    def draw(self, screen, camera):
        if not self.is_alive: return
        pos = camera.apply(self)
        
        # Animation Bob
        anim = (pygame.time.get_ticks() // 200) % 2 * 4
        
        # Body
        pygame.draw.rect(screen, GOOMBA_COLOR, (pos.x+2, pos.y+4, 28, 24))
        pygame.draw.rect(screen, GOOMBA_COLOR, (pos.x+6, pos.y, 20, 8))
        # Eyes
        pygame.draw.rect(screen, CLOUD_WHITE, (pos.x+6, pos.y+8, 8, 10))
        pygame.draw.rect(screen, CLOUD_WHITE, (pos.x+18, pos.y+8, 8, 10))
        pygame.draw.rect(screen, BLACK, (pos.x+8, pos.y+10, 4, 6))
        pygame.draw.rect(screen, BLACK, (pos.x+20, pos.y+10, 4, 6))
        # Feet
        pygame.draw.rect(screen, BLACK, (pos.x+2, pos.y+28 - anim, 10, 4))
        pygame.draw.rect(screen, BLACK, (pos.x+20, pos.y+28 - (4-anim), 10, 4))

class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y, type_):
        super().__init__()
        self.type = type_
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)

    def draw(self, screen, camera):
        pos = camera.apply_rect(self.rect)
        # Culling optimization
        if pos.right < 0 or pos.left > SCREEN_WIDTH: return

        if self.type == "ground":
            pygame.draw.rect(screen, GROUND_BROWN, pos)
            pygame.draw.rect(screen, BLACK, pos, 1)
            pygame.draw.rect(screen, (220, 90, 20), (pos.x+4, pos.y+4, 24, 24), 2)

        elif self.type == "brick":
            pygame.draw.rect(screen, BRICK_BROWN, pos)
            pygame.draw.rect(screen, BLACK, pos, 1)
            # Brick pattern details
            pygame.draw.line(screen, BLACK, (pos.x, pos.y+16), (pos.right, pos.y+16))
            pygame.draw.line(screen, BLACK, (pos.x+16, pos.y), (pos.x+16, pos.y+16))
            pygame.draw.line(screen, BLACK, (pos.x+8, pos.y+16), (pos.x+8, pos.bottom))
            pygame.draw.line(screen, BLACK, (pos.x+24, pos.y+16), (pos.x+24, pos.bottom))

        elif self.type == "block":
            pygame.draw.rect(screen, BLOCK_GOLD, pos)
            pygame.draw.rect(screen, BLACK, pos, 1)
            pygame.draw.rect(screen, (180, 100, 0), (pos.x+4, pos.y+4, 24, 24), 2)
            pygame.draw.circle(screen, BLACK, (pos.centerx+2, pos.centery+2), 2)

        elif self.type == "pipe":
            pygame.draw.rect(screen, PIPE_GREEN, pos)
            pygame.draw.rect(screen, PIPE_DARK, pos, 2)
            pygame.draw.rect(screen, PIPE_LIGHT, (pos.x+4, pos.y, 4, pos.height))

        elif self.type == "pipe_top":
            pygame.draw.rect(screen, PIPE_GREEN, (pos.x-2, pos.y, 36, 32))
            pygame.draw.rect(screen, PIPE_DARK, (pos.x-2, pos.y, 36, 32), 2)
            pygame.draw.rect(screen, PIPE_LIGHT, (pos.x+4, pos.y, 4, 32))

        elif self.type == "flagpole":
            pygame.draw.rect(screen, (20, 180, 20), (pos.centerx-2, pos.y, 4, 32))

        elif self.type == "flag_top":
            pygame.draw.circle(screen, (20, 180, 20), (pos.centerx, pos.bottom), 6)

        elif self.type == "castle":
            pygame.draw.rect(screen, CASTLE_BRICK, pos)
            pygame.draw.rect(screen, BLACK, pos, 1)

        elif self.type == "castle_door":
            pygame.draw.rect(screen, BLACK, pos)
            pygame.draw.circle(screen, CASTLE_BRICK, (pos.centerx, pos.y), 16)

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Super Mario Python 1-1")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 24, bold=True)
        self.reset()

    def reset(self):
        self.tiles = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.mario = Mario(100, SCREEN_HEIGHT - TILE_SIZE * 5)
        self.game_over = False
        self.flag_triggered = False
        self.score = 0
        self.coins = 0
        self.world = "1-1"
        self.time = 400
        self.time_ticker = 0
        self.score_counted = False
        self.generate_level()

    def trigger_victory(self):
        self.mario.state = "VICTORY"

    def add_pipe(self, x, height):
        for h in range(height):
            self.tiles.add(Tile(x * TILE_SIZE, SCREEN_HEIGHT - (2+h) * TILE_SIZE, "pipe"))
        self.tiles.add(Tile(x * TILE_SIZE, SCREEN_HEIGHT - (2+height) * TILE_SIZE, "pipe_top"))

    def add_castle(self, x):
        # Decorative Castle
        for cx in range(5):
            for cy in range(2):
                self.tiles.add(Tile((x + cx) * TILE_SIZE, SCREEN_HEIGHT - (2+cy)*TILE_SIZE, "castle"))
        for cx in range(1, 4):
            for cy in range(2, 4):
                self.tiles.add(Tile((x + cx) * TILE_SIZE, SCREEN_HEIGHT - (2+cy)*TILE_SIZE, "castle"))
        self.tiles.add(Tile((x + 2) * TILE_SIZE, SCREEN_HEIGHT - 6*TILE_SIZE, "castle"))
        self.tiles.add(Tile((x + 2) * TILE_SIZE, SCREEN_HEIGHT - 3*TILE_SIZE, "castle_door"))

    def generate_level(self):
        # 1-1 Map Data
        map_width = 230
        pits = [69, 70, 86, 87, 88] # Locations of pits

        # Ground
        for x in range(map_width):
            if x not in pits:
                self.tiles.add(Tile(x * TILE_SIZE, SCREEN_HEIGHT - TILE_SIZE, "ground"))
                self.tiles.add(Tile(x * TILE_SIZE, SCREEN_HEIGHT - TILE_SIZE * 2, "ground"))

        # Pipes
        self.add_pipe(28, 1)
        self.add_pipe(38, 1)
        self.add_pipe(46, 1)
        self.add_pipe(57, 1)

        # Bricks and Blocks
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

        # Stairs
        def build_stair(start_x, height, reverse=False):
            for i in range(height):
                for h in range(i + 1):
                    x = start_x + (i if not reverse else (height - 1 - i))
                    self.tiles.add(Tile(x * TILE_SIZE, SCREEN_HEIGHT - (3+h)*TILE_SIZE, "block"))

        build_stair(134, 4)
        build_stair(140, 4, True)
        build_stair(148, 4)
        build_stair(152, 4, True)
        build_stair(181, 8) # Big stair at end

        # Flagpole
        flag_x = 198
        for i in range(1, 10):
            self.tiles.add(Tile(flag_x * TILE_SIZE, SCREEN_HEIGHT - (2+i)*TILE_SIZE, "flagpole"))
        self.tiles.add(Tile(flag_x * TILE_SIZE, SCREEN_HEIGHT - (2+10)*TILE_SIZE, "flag_top"))
        self.tiles.add(Tile(flag_x * TILE_SIZE, SCREEN_HEIGHT - 3*TILE_SIZE, "block")) # Base

        self.add_castle(202)

        # Enemies
        goomba_locs = [22, 40, 50, 51, 80, 82, 97, 99, 114, 116, 124, 126, 128, 174, 176]
        for loc in goomba_locs:
            self.enemies.add(Goomba(loc * TILE_SIZE, SCREEN_HEIGHT - TILE_SIZE * 5))

    def draw_hud(self):
        # MARIO   WORLD   TIME
        # 000000   1-1    000
        
        # Labels
        mario_lbl = self.font.render("MARIO", True, WHITE)
        world_lbl = self.font.render("WORLD", True, WHITE)
        time_lbl = self.font.render("TIME", True, WHITE)
        
        # Values
        score_val = self.font.render(f"{self.score:06d}", True, WHITE)
        coin_val = self.font.render(f"x{self.coins:02d}", True, WHITE)
        world_val = self.font.render(self.world, True, WHITE)
        time_val = self.font.render(f"{self.time:03d}", True, WHITE)

        # Positions (SMB1 Layout)
        self.screen.blit(mario_lbl, (40, 20))
        self.screen.blit(score_val, (40, 45))
        
        self.screen.blit(coin_val, (300, 45)) # Simplified coin display
        
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
                    if event.key == pygame.K_r:
                        self.reset()

            if not self.game_over:
                self.mario.update(self.tiles, self.enemies, self)
                self.enemies.update(self.tiles)
                self.camera.update(self.mario)

                # Flag Logic
                if self.mario.state == "SLIDE" and not self.flag_triggered:
                    self.flag_triggered = True
                    self.enemies.empty() # Despawn enemies for victory lap

                # Win/Loss Conditions
                if self.mario.state == "DEAD" and self.mario.rect.y > SCREEN_HEIGHT + 100:
                    self.game_over = True
                
                # Victory handled by Mario update now (when entering castle)
                if self.mario.state == "VICTORY":
                    self.game_over = True

                # Timer Logic
                if self.mario.state not in ["DEAD", "VICTORY"]:
                    self.time_ticker += 1
                    if self.time_ticker >= 60: # Approx 1 second
                        self.time -= 1
                        self.time_ticker = 0
                        if self.time <= 0:
                            self.mario.die()

            # Draw
            self.screen.fill(SKY_BLUE)
            for tile in self.tiles: tile.draw(self.screen, self.camera)
            for enemy in self.enemies: enemy.draw(self.screen, self.camera)
            self.mario.draw(self.screen, self.camera)
            self.draw_hud()

            # End Sequence / UI
            if self.game_over:
                if self.mario.state == "VICTORY":
                    # Draw "COURSE CLEAR!" immediately
                    msg = "COURSE CLEAR!"
                    txt = self.font.render(msg, True, WHITE)
                    self.screen.blit(txt, (SCREEN_WIDTH//2 - txt.get_width()//2, SCREEN_HEIGHT//3))

                    # Score Countdown Animation
                    if self.time > 0:
                        # Count down faster (5 units per frame) for effect
                        countdown_step = 5 if self.time >= 5 else self.time
                        self.time -= countdown_step
                        self.score += 50 * countdown_step
                        # Play sound here if available
                    else:
                        # Only show restart prompt when countdown finishes
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
