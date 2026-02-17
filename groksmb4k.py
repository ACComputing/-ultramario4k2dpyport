import pygame
import sys

# ============================================================================
#  ULTRA Mario World v3 - SMW 60FPS + Debug Menu + Mario Maker Editor + HOTKEYS
#  SMB1 Menu + Full 1-1→8-4 + Level Editor + Instant D/E hotkeys
# ============================================================================

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480
FPS = 60
TILE_SIZE = 32

# Physics
GRAVITY = 0.6
JUMP_POWER = -14.5
MOVE_SPEED = 6
FRICTION = 0.85
ACCEL = 0.5

# Palette
SKY_BLUE = (92, 148, 252)
MARIO_RED = (216, 40, 0)
MARIO_BLUE = (0, 56, 168)
MARIO_SKIN = (252, 152, 56)
MARIO_BROWN = (136, 112, 0)
GROUND_BROWN = (200, 76, 12)
BRICK_BROWN = (184, 48, 0)
BLOCK_GOLD = (252, 188, 0)
PIPE_GREEN = (0, 168, 0)
PIPE_LIGHT = (88, 248, 152)
PIPE_DARK = (0, 80, 0)
GOOMBA_BODY = (228, 92, 16)
HILL_GREEN = (0, 168, 0)
HILL_OUTLINE = (0, 80, 0)
CLOUD_WHITE = (255, 255, 255)
CASTLE_BRICK = (184, 48, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
CREAM = (255, 204, 197)
YELLOW = (255, 255, 0)
TOOL_COLORS = {"ground": GROUND_BROWN, "brick": BRICK_BROWN, "block": BLOCK_GOLD, "pipe": PIPE_GREEN, "goomba": GOOMBA_BODY}

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
        elif self.type == "cloud":
            c_width = 32 * (1 + self.size)
            base_x = dest.x
            base_y = dest.y
            pygame.draw.rect(screen, CLOUD_WHITE, (base_x, base_y, c_width, 24), border_radius=12)
            pygame.draw.circle(screen, CLOUD_WHITE, (base_x + 16, base_y), 16)
            if self.size > 1: pygame.draw.circle(screen, CLOUD_WHITE, (base_x + 48, base_y), 16)
            if self.size > 2: pygame.draw.circle(screen, CLOUD_WHITE, (base_x + 80, base_y), 16)
        elif self.type == "bush":
            b_width = 32 * (1 + self.size)
            base_x = dest.x
            base_y = SCREEN_HEIGHT - TILE_SIZE * 2 - 16
            pygame.draw.circle(screen, PIPE_LIGHT, (base_x + 16, base_y + 8), 16)
            pygame.draw.circle(screen, PIPE_LIGHT, (base_x + b_width - 16, base_y + 8), 16)
            pygame.draw.rect(screen, PIPE_LIGHT, (base_x + 16, base_y, b_width - 32, 24))

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
        if self.state == "VICTORY" or not self.visible: return
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
                    if self.rect.colliderect(tile.rect) and self.vel_y > 0:
                        self.rect.bottom = tile.rect.top
                        self.vel_y = 0
            for tile in tiles:
                if tile.type == "castle_door" and self.rect.colliderect(tile.rect):
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
        hx, hy = pos.x, pos.y
        dir = 1 if self.facing_right else -1
        pygame.draw.rect(screen, MARIO_RED, (hx+2, hy+4, 24, 8))
        pygame.draw.rect(screen, MARIO_SKIN, (hx+6, hy+10, 16, 10))
        pygame.draw.rect(screen, MARIO_BROWN, (hx+4 if self.facing_right else hx+10, hy+8, 8, 6))
        pygame.draw.rect(screen, MARIO_RED, (hx+4, hy+18, 20, 6))
        pygame.draw.rect(screen, MARIO_BLUE, (hx+4, hy+22, 20, 8))
        pygame.draw.rect(screen, MARIO_BROWN, (hx+2, hy+28, 8, 4))
        pygame.draw.rect(screen, MARIO_BROWN, (hx+18, hy+28, 8, 4))
        arm_x = hx + (2 if self.facing_right else 18) + (4 * dir if self.walk_frame % 2 else 0)
        pygame.draw.rect(screen, MARIO_RED, (arm_x, hy+18, 6, 8))
        leg_offset = 3 if self.walk_frame == 1 else -3
        pygame.draw.rect(screen, MARIO_BLUE, (hx+6 + leg_offset*dir, hy+26, 6, 6))
        pygame.draw.rect(screen, MARIO_BLUE, (hx+16 - leg_offset*dir, hy+26, 6, 6))

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
                self.vel_x *= -1
        self.rect.y += self.vel_y
        for tile in tiles:
            if tile.type in ["castle", "flagpole", "flag_top", "castle_door", "bush", "hill", "cloud"]: continue
            if self.rect.colliderect(tile.rect) and self.vel_y > 0:
                self.rect.bottom = tile.rect.top
                self.vel_y = 0

    def die(self):
        self.is_alive = False

    def draw(self, screen, camera):
        pos = camera.apply(self)
        if not self.is_alive:
            pygame.draw.rect(screen, GOOMBA_BODY, (pos.x+4, pos.y+16, 24, 16))
            return
        pygame.draw.ellipse(screen, GOOMBA_BODY, (pos.x+2, pos.y, 28, 24))
        pygame.draw.rect(screen, WHITE, (pos.x+6, pos.y+8, 8, 8))
        pygame.draw.rect(screen, WHITE, (pos.x+18, pos.y+8, 8, 8))
        pygame.draw.rect(screen, BLACK, (pos.x+8, pos.y+10, 4, 4))
        pygame.draw.rect(screen, BLACK, (pos.x+20, pos.y+10, 4, 4))
        foot = (pos.x if self.frame == 0 else pos.x+2, pos.y+24, 10, 6)
        pygame.draw.rect(screen, BLACK, foot)
        foot2 = (pos.x+20 if self.frame == 0 else pos.x+18, pos.y+24, 10, 6)
        pygame.draw.rect(screen, BLACK, foot2)

class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y, type_):
        super().__init__()
        self.type = type_
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.frame_timer = 0

    def draw(self, screen, camera):
        pos = camera.apply_rect(self.rect)
        if pos.right < 0 or pos.left > SCREEN_WIDTH: return
        if self.type == "ground":
            pygame.draw.rect(screen, GROUND_BROWN, pos)
            pygame.draw.rect(screen, CREAM, (pos.x, pos.y+4, pos.width, 4))
        elif self.type == "brick":
            pygame.draw.rect(screen, BRICK_BROWN, pos)
            pygame.draw.rect(screen, BLACK, pos, 2)
        elif self.type == "block":
            self.frame_timer = (pygame.time.get_ticks() // 200) % 3
            col = BLOCK_GOLD if self.frame_timer != 1 else YELLOW
            pygame.draw.rect(screen, col, pos)
            pygame.draw.rect(screen, BLACK, pos, 2)
            pygame.draw.rect(screen, BLACK, (pos.x+8, pos.y+8, 16, 4))
        elif self.type == "pipe":
            pygame.draw.rect(screen, PIPE_GREEN, pos)
            pygame.draw.rect(screen, PIPE_DARK, pos, 4)
        elif self.type == "pipe_top":
            pygame.draw.rect(screen, PIPE_GREEN, (pos.x-4, pos.y-4, pos.width+8, 36))
            pygame.draw.rect(screen, PIPE_DARK, (pos.x-4, pos.y-4, pos.width+8, 36), 4)
        elif self.type == "flagpole":
            pygame.draw.rect(screen, (20, 180, 20), (pos.centerx-2, pos.y, 4, pos.height))
        elif self.type == "flag_top":
            pygame.draw.circle(screen, (20, 180, 20), (pos.centerx, pos.bottom), 8)
        elif self.type == "castle":
            pygame.draw.rect(screen, CASTLE_BRICK, pos)
            pygame.draw.rect(screen, BLACK, pos, 2)
        elif self.type == "castle_door":
            pygame.draw.rect(screen, BLACK, pos)
            pygame.draw.rect(screen, CASTLE_BRICK, (pos.x+8, pos.y+8, pos.width-16, pos.height-16))

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("SUPER MARIO WORLD - SMW 60FPS + HOTKEYS")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 24, bold=True)
        self.big_font = pygame.font.SysFont("monospace", 72, bold=True)
        self.state = "MENU"
        self.menu_selection = 0
        self.debug_world = 1
        self.debug_level = 1
        self.editor_tiles = pygame.sprite.Group()
        self.editor_enemies = pygame.sprite.Group()
        self.editor_camera = Camera(SCREEN_WIDTH * 3, SCREEN_HEIGHT)
        self.current_tool = "ground"
        self.saved_level = None
        self.world = 1
        self.level = 1
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
        self.time = 400
        self.time_ticker = 0
        self.generate_level()

    def next_stage(self):
        self.level += 1
        if self.level > 4:
            self.level = 1
            self.world += 1
        if self.world > 8:
            self.world = 8
            self.level = 4

    def trigger_victory(self):
        self.mario.state = "VICTORY"
        self.game_over = True

    def add_pipe(self, x, height, group):
        for h in range(height):
            group.add(Tile(x * TILE_SIZE, SCREEN_HEIGHT - (2+h) * TILE_SIZE, "pipe"))
        group.add(Tile(x * TILE_SIZE, SCREEN_HEIGHT - (2+height) * TILE_SIZE, "pipe_top"))

    def add_castle(self, x, group):
        for cx in range(5):
            for cy in range(2):
                group.add(Tile((x + cx) * TILE_SIZE, SCREEN_HEIGHT - (2+cy)*TILE_SIZE, "castle"))
        group.add(Tile((x + 2) * TILE_SIZE, SCREEN_HEIGHT - 3*TILE_SIZE, "castle_door"))

    def generate_level(self):
        map_width = 180 + self.world * 10
        pits = [69, 70, 86, 87, 88, 120 + self.world]
        for x in range(map_width):
            if x not in pits:
                self.tiles.add(Tile(x * TILE_SIZE, SCREEN_HEIGHT - TILE_SIZE, "ground"))
                self.tiles.add(Tile(x * TILE_SIZE, SCREEN_HEIGHT - TILE_SIZE * 2, "ground"))
        for x in range(0, map_width, 16):
            self.scenery.add(Decoration((x + 0) * TILE_SIZE, 0, "hill", size=2))
            self.scenery.add(Decoration((x + 16) * TILE_SIZE, 0, "hill", size=1))
            self.scenery.add(Decoration((x + 11) * TILE_SIZE, 0, "bush", size=2))
            self.scenery.add(Decoration((x + 8) * TILE_SIZE, 80, "cloud", size=2))
        self.add_pipe(28, 1, self.tiles)
        self.add_pipe(46, 2 if self.world > 3 else 1, self.tiles)
        structures = [(16,5,'block'),(22,5,'brick'),(22,9,'block'),(77,5,'brick'),(80,9,'brick'),(94,5,'brick')]
        for s in structures:
            self.tiles.add(Tile(s[0]*TILE_SIZE, SCREEN_HEIGHT-(2+s[1])*TILE_SIZE, s[2]))
        def build_stair(start_x, height, reverse=False):
            for i in range(height):
                for h in range(i+1):
                    x = start_x + (i if not reverse else height-1-i)
                    self.tiles.add(Tile(x*TILE_SIZE, SCREEN_HEIGHT-(3+h)*TILE_SIZE, "block"))
        build_stair(134, 4 + self.world//3)
        build_stair(181, 8)
        flag_x = 198
        for i in range(1, 10):
            self.tiles.add(Tile(flag_x * TILE_SIZE, SCREEN_HEIGHT - (2+i)*TILE_SIZE, "flagpole"))
        self.tiles.add(Tile(flag_x * TILE_SIZE, SCREEN_HEIGHT - (2+10)*TILE_SIZE, "flag_top"))
        self.add_castle(202, self.tiles)
        goomba_count = 12 + self.world * 2
        for loc in range(goomba_count):
            self.enemies.add(Goomba((20 + loc*12) * TILE_SIZE, SCREEN_HEIGHT - TILE_SIZE * 5))

    def draw_menu(self):
        self.screen.fill(BLACK)
        super_t = self.big_font.render("SUPER", True, YELLOW)
        mario_t = self.big_font.render("MARIO", True, MARIO_RED)
        bros_t = self.font.render("WORLD", True, WHITE)
        self.screen.blit(super_t, (SCREEN_WIDTH//2 - super_t.get_width()//2 - 80, 80))
        self.screen.blit(mario_t, (SCREEN_WIDTH//2 - mario_t.get_width()//2 + 90, 150))
        self.screen.blit(bros_t, (SCREEN_WIDTH//2 - bros_t.get_width()//2, 230))

        options = ["START GAME (1-1)", "DEBUG LEVEL SELECT", "MARIO MAKER EDITOR"]
        for i, txt in enumerate(options):
            color = YELLOW if i == self.menu_selection else WHITE
            t = self.font.render(txt, True, color)
            self.screen.blit(t, (SCREEN_WIDTH//2 - t.get_width()//2, 300 + i*40))

        # HOTKEY HINT
        hint = self.font.render("S/ENTER = Start   D = Debug   E = Editor", True, CREAM)
        self.screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, 420))

        copy = self.font.render("© 1985-2026 NINTENDO / AC HOLDINGS CATSDK", True, CREAM)
        self.screen.blit(copy, (SCREEN_WIDTH//2 - copy.get_width()//2, 450))

    def draw_debug_menu(self):
        self.screen.fill(BLACK)
        title = self.big_font.render("DEBUG SELECT", True, YELLOW)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 80))
        wtxt = self.font.render(f"WORLD: {self.debug_world}   LEVEL: {self.debug_level}", True, WHITE)
        self.screen.blit(wtxt, (SCREEN_WIDTH//2 - wtxt.get_width()//2, 200))
        hint = self.font.render("↑↓ world   ←→ level   ENTER play   ESC back", True, CREAM)
        self.screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2, 300))

    def draw_editor(self):
        self.screen.fill(SKY_BLUE)
        for tile in self.editor_tiles:
            tile.draw(self.screen, self.editor_camera)
        for enemy in self.editor_enemies:
            enemy.draw(self.screen, self.editor_camera)
        tool_txt = self.font.render(f"TOOL: {self.current_tool.upper()}", True, WHITE)
        self.screen.blit(tool_txt, (10, 10))
        pygame.draw.rect(self.screen, TOOL_COLORS[self.current_tool], (10, 50, 40, 40))
        hint = self.font.render("1-5 = tools   LEFT/RIGHT mouse = place/erase   SPACE = test play   S = save   ESC = menu", True, CREAM)
        self.screen.blit(hint, (10, SCREEN_HEIGHT - 30))

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if self.state == "MENU":
                        if event.key == pygame.K_DOWN:
                            self.menu_selection = (self.menu_selection + 1) % 3
                        if event.key == pygame.K_UP:
                            self.menu_selection = (self.menu_selection - 1) % 3
                        if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_s):
                            self.world = 1
                            self.level = 1
                            self.state = "PLAYING"
                            self.reset()
                        if event.key == pygame.K_d:
                            self.state = "DEBUG_MENU"
                        if event.key == pygame.K_e:
                            self.state = "EDITOR"
                            self.editor_tiles.empty()
                            self.editor_enemies.empty()
                            self.editor_camera.camera.x = 0
                            for x in range(25):
                                self.editor_tiles.add(Tile(x * TILE_SIZE, SCREEN_HEIGHT - TILE_SIZE, "ground"))
                            for x in range(25):
                                self.editor_tiles.add(Tile(x * TILE_SIZE, SCREEN_HEIGHT - TILE_SIZE*2, "ground"))

                    elif self.state == "DEBUG_MENU":
                        if event.key == pygame.K_UP:
                            self.debug_world = max(1, self.debug_world - 1)
                        if event.key == pygame.K_DOWN:
                            self.debug_world = min(8, self.debug_world + 1)
                        if event.key == pygame.K_LEFT:
                            self.debug_level = max(1, self.debug_level - 1)
                        if event.key == pygame.K_RIGHT:
                            self.debug_level = min(4, self.debug_level + 1)
                        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self.world = self.debug_world
                            self.level = self.debug_level
                            self.state = "PLAYING"
                            self.reset()
                        if event.key == pygame.K_ESCAPE:
                            self.state = "MENU"

                    elif self.state == "EDITOR":
                        if event.key == pygame.K_ESCAPE:
                            self.state = "MENU"
                        if event.key == pygame.K_1: self.current_tool = "ground"
                        if event.key == pygame.K_2: self.current_tool = "brick"
                        if event.key == pygame.K_3: self.current_tool = "block"
                        if event.key == pygame.K_4: self.current_tool = "pipe"
                        if event.key == pygame.K_5: self.current_tool = "goomba"
                        if event.key == pygame.K_SPACE:  # TEST PLAY
                            self.world = 99
                            self.level = 1
                            self.tiles = self.editor_tiles.copy()
                            self.enemies = self.editor_enemies.copy()
                            self.state = "PLAYING"
                            self.reset()
                            self.tiles.empty()
                            self.enemies.empty()
                            for t in self.editor_tiles: self.tiles.add(t)
                            for e in self.editor_enemies: self.enemies.add(e)
                        if event.key == pygame.K_s:
                            self.saved_level = (list(self.editor_tiles), list(self.editor_enemies))
                            print("★ LEVEL SAVED TO MEMORY ★")

                    if event.key == pygame.K_r and self.state == "PLAYING":
                        self.state = "PLAYING"
                        self.reset()

                if event.type == pygame.MOUSEBUTTONDOWN and self.state == "EDITOR":
                    mx, my = pygame.mouse.get_pos()
                    world_x = mx + self.editor_camera.camera.x
                    world_y = my
                    grid_x = (world_x // TILE_SIZE) * TILE_SIZE
                    grid_y = (world_y // TILE_SIZE) * TILE_SIZE
                    if event.button == 1:
                        if self.current_tool == "goomba":
                            self.editor_enemies.add(Goomba(grid_x, grid_y))
                        else:
                            new_tile = Tile(grid_x, grid_y, self.current_tool)
                            self.editor_tiles.add(new_tile)
                    elif event.button == 3:
                        for t in list(self.editor_tiles):
                            if t.rect.collidepoint(world_x, world_y):
                                t.kill()
                        for e in list(self.editor_enemies):
                            if e.rect.collidepoint(world_x, world_y):
                                e.kill()

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
            elif self.state == "DEBUG_MENU":
                self.draw_debug_menu()
            elif self.state == "EDITOR":
                self.draw_editor()
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
                        txt = self.font.render("COURSE CLEAR!", True, WHITE)
                        self.screen.blit(txt, (SCREEN_WIDTH//2 - txt.get_width()//2, SCREEN_HEIGHT//3))
                        sub = self.font.render(f"WORLD {self.world}-{self.level} COMPLETE", True, YELLOW)
                        self.screen.blit(sub, (SCREEN_WIDTH//2 - sub.get_width()//2, SCREEN_HEIGHT//2))
                        sub2 = self.font.render("Press R for next / ESC menu", True, WHITE)
                        self.screen.blit(sub2, (SCREEN_WIDTH//2 - sub2.get_width()//2, SCREEN_HEIGHT//2 + 60))
                    else:
                        txt = self.font.render("GAME OVER", True, WHITE)
                        sub = self.font.render("Press R to Restart", True, WHITE)
                        self.screen.blit(txt, (SCREEN_WIDTH//2 - txt.get_width()//2, SCREEN_HEIGHT//3))
                        self.screen.blit(sub, (SCREEN_WIDTH//2 - sub.get_width()//2, SCREEN_HEIGHT//2))

            pygame.display.flip()
            self.clock.tick(FPS)

    def draw_hud(self):
        mario_lbl = self.font.render("MARIO", True, WHITE)
        world_lbl = self.font.render("WORLD", True, WHITE)
        time_lbl = self.font.render("TIME", True, WHITE)
        score_val = self.font.render(f"{self.score:06d}", True, WHITE)
        world_val = self.font.render(f"{self.world}-{self.level}", True, WHITE)
        time_val = self.font.render(f"{self.time:03d}", True, WHITE)
        self.screen.blit(mario_lbl, (40, 20))
        self.screen.blit(score_val, (40, 45))
        self.screen.blit(world_lbl, (480, 20))
        self.screen.blit(world_val, (490, 45))
        self.screen.blit(time_lbl, (680, 20))
        self.screen.blit(time_val, (690, 45))

if __name__ == "__main__":
    game = Game()
    game.run()
