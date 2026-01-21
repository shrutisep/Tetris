import os
import sys
import random
import math
import time
from typing import List, Tuple, Optional, Dict, Union
from dataclasses import dataclass, field
import pygame

# -------------------------
# Pygame init & constants
# -------------------------
# pylint: disable=no-member
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.font.init()
pygame.joystick.init()

# Screen & grid
SCREEN_WIDTH = 300
SCREEN_HEIGHT = 600
GRID_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
SIDEBAR_WIDTH = 200
FULL_WIDTH = SCREEN_WIDTH + SIDEBAR_WIDTH

# Colors & UI
TEXT_COLOR = (255, 255, 255)
BACKGROUND_ALPHA = 180
GHOST_ALPHA = 100
GRID_LINE_COLOR = (30, 30, 30)
GAME_OVER_OVERLAY_COLOR = (0, 0, 0, BACKGROUND_ALPHA)
GAME_OVER_TEXT_COLOR = (100, 150, 255)
RED = (240, 60, 60)
YELLOW = (255, 215, 90)

# Pastel palette used in the code you provided
VIBRANT_PASTELS = [
    (255, 182, 193), (173, 216, 230), (255, 255, 224),
    (221, 160, 221), (144, 238, 144), (255, 204, 229),
    (204, 255, 229), (229, 204, 255)
]

FPS = 60
BLOCKS_PER_STAGE = 5
MAX_STAGE = 3
STAGE_SPEEDS = [0.7, 0.5, 0.3, 0.18]  # seconds per step
STAGE_NAMES = ["Easy", "Medium", "Hard", "Super Hard"]
PREVIEW_COUNTS = [3, 2, 1, 0]

# Preview & visuals
PREVIEW_BOX_X = SCREEN_WIDTH + 20
PREVIEW_BOX_Y = 50
PREVIEW_BOX_SPACING = 90
PREVIEW_BOX_PADDING = 5
PREVIEW_BOX_BORDER_RADIUS = 5
PREVIEW_BOX_BORDER_WIDTH = 2
PREVIEW_PIECE_AREA_SIZE = 4
PREVIEW_ANIMATION_SPEED = 0.1
PREVIEW_ANIMATION_MAX_OFFSET = 2
PREVIEW_GLOW_BASE_ALPHA = 50
PREVIEW_GLOW_PULSE_MAGNITUDE = 30
PREVIEW_GLOW_PULSE_SPEED = 0.005
PREVIEW_HIGHLIGHT_BRIGHTNESS = 50
PREVIEW_HIGHLIGHT_ALPHA = 100
PREVIEW_HIGHLIGHT_BORDER_RADIUS = 2
SIDEBAR_ITEM_SPACING = 30
INFO_BOX_Y = 400
TEXT_OFFSET = 30
GAME_OVER_DELAY_MS = 50
STAGE_TRANSITION_FRAMES = 60
PIECE_PADDING = 2
GHOST_PADDING = 4

FONT_SMALL = pygame.font.SysFont('Arial', 18)
FONT_LARGE = pygame.font.SysFont('Arial', 36, bold=True)

# Starfield settings
STAR_SPAWN_CHANCE = 0.05
STAR_COUNT = 30
STAR_RADIUS_SMALL = 1
STAR_RADIUS_MEDIUM = 2
STAR_COLORS = [(255, 255, 255), (255, 240, 255), (220, 255, 255)]
STAR_TRAIL_LENGTH = 3
STAR_MIN_SPEED = 6
STAR_MAX_SPEED = 10
STAR_LIFESPAN_FRAMES = 20

# Particles
PARTICLE_EFFECTS = {
    "shrink_rate": 0.2, "glow_shrink_rate": 0.1, "glow_alpha": 50,
    "min_life": 40, "max_life": 80, "min_speed": 2, "max_speed": 6,
    "min_size": 5, "max_size": 12, "fade_rate": 3,
    "line_clear_count": 5, "block_land_count": 3
}

BACKGROUND_MUSIC_VOLUME = 0.25
SOUND_EFFECT_VOLUME = 0.7
SILENT_SOUND_BUFFER_SIZE = 44

# Shapes (standard 7 tetromino templates)
SHAPES = [
    [[1, 1, 1, 1]],      # I
    [[1, 0, 0], [1, 1, 1]],  # J
    [[0, 0, 1], [1, 1, 1]],  # L
    [[1, 1], [1, 1]],      # O
    [[0, 1, 1], [1, 1, 0]],  # S
    [[0, 1, 0], [1, 1, 1]],  # T
    [[1, 1, 0], [0, 1, 1]]   # Z
]

# Controller constants
AXIS_THRESHOLD = 0.3
MOVEMENT_COOLDOWN_MS = 130

# -------------------------
# Data classes
# -------------------------
@dataclass
class Tetromino:
    shape: List[List[int]]
    color: Tuple[int, int, int]
    x: int
    y: int

@dataclass
class GameStateData:
    score: int = 0
    lines: int = 0
    blocks_placed: int = 0
    game_over: bool = False

@dataclass
class StageInfo:
    active: bool = False
    timer: int = 0
    text: str = ""
    last_stage: int = 0

@dataclass
class VisualEffects:
    stars: List['ShootingStar'] = field(default_factory=list)
    particles: List['Particle'] = field(default_factory=list)

# -------------------------
# Sound manager (robust)
# -------------------------
class SoundManager:
    def __init__(self) -> None:
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.load_sounds()

    def _get_resource_path(self, filename: str) -> str:
        # look in multiple places (script dir, cwd, assets)
        possible_dirs = [
            os.path.dirname(os.path.abspath(__file__)),
            os.getcwd(),
            getattr(sys, '_MEIPASS', None),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets'),
            os.path.join(os.getcwd(), 'assets')
        ]
        possible_dirs = [d for d in possible_dirs if d is not None]
        for base_dir in possible_dirs:
            file_path = os.path.join(base_dir, filename)
            if os.path.exists(file_path):
                return file_path
        return filename

    def load_sounds(self) -> None:
        sound_files = {
            "clear": "clear.mp3",
            "explosion": "explosion.mp3",
            "gameover": "gameover.mp3",
            "background": "sounds_music.ogg"
        }
        silent_sound = self._create_silent_sound()
        for name, filename in sound_files.items():
            try:
                file_path = self._get_resource_path(filename)
                if name == "background":
                    self._load_background_music(file_path)
                else:
                    self._load_sound_effect(name, file_path, silent_sound)
            except (pygame.error, FileNotFoundError) as err:
                print(f"Error loading sound '{filename}' at '{file_path}': {err}")
                if name != "background":
                    self.sounds[name] = silent_sound

    def _load_background_music(self, file_path: str) -> None:
        if not os.path.exists(file_path):
            print(f"Background music not found: {file_path} (skipping)")
            return
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.set_volume(BACKGROUND_MUSIC_VOLUME)
        except Exception as e:
            print("Failed to load background music:", e)

    def _load_sound_effect(self, name: str, file_path: str,
                           silent: pygame.mixer.Sound) -> None:
        if not os.path.exists(file_path):
            print(f"Sound file '{file_path}' not found! Using silent sound.")
            self.sounds[name] = silent
            return
        sound = pygame.mixer.Sound(file_path)
        sound.set_volume(SOUND_EFFECT_VOLUME)
        self.sounds[name] = sound

    @staticmethod
    def _create_silent_sound() -> pygame.mixer.Sound:
        # create a tiny silent WAV-like buffer
        try:
            return pygame.mixer.Sound(buffer=bytearray(SILENT_SOUND_BUFFER_SIZE))
        except Exception:
            return None  # type: ignore

    def play(self, sound_name: str) -> None:
        if sound_name in self.sounds and self.sounds[sound_name]:
            try:
                self.sounds[sound_name].stop()
                self.sounds[sound_name].play()
            except Exception as err:
                print("Error playing sound:", err)

    @staticmethod
    def play_music() -> None:
        try:
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.play(-1)
        except Exception as err:
            print("Error playing music:", err)

    @staticmethod
    def stop_music() -> None:
        try:
            pygame.mixer.music.stop()
        except Exception as err:
            print("Error stopping music:", err)

# -------------------------
# Particles + Stars
# -------------------------
class Particle:
    def __init__(self, x: float, y: float, color: Tuple[int, int, int]) -> None:
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(PARTICLE_EFFECTS["min_size"], PARTICLE_EFFECTS["max_size"])
        self.speed = random.uniform(PARTICLE_EFFECTS["min_speed"], PARTICLE_EFFECTS["max_speed"])
        self.angle = random.uniform(0, 2 * math.pi)
        self.life = random.randint(PARTICLE_EFFECTS["min_life"], PARTICLE_EFFECTS["max_life"])
        self.alpha = 255.0
        self.glow_size = self.size * 2.0

    def update(self) -> None:
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.life -= 1
        self.size = max(0, self.size - PARTICLE_EFFECTS["shrink_rate"])
        self.glow_size = max(0, self.glow_size - PARTICLE_EFFECTS["glow_shrink_rate"])
        self.alpha = max(0, self.alpha - PARTICLE_EFFECTS["fade_rate"])

    def draw(self, surface: pygame.Surface) -> None:
        if self.life > 0:
            self._draw_glow(surface)
            self._draw_core(surface)

    def _create_alpha_surface(self, size: int) -> pygame.Surface:
        return pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)

    def _draw_glow(self, surface: pygame.Surface) -> None:
        glow_alpha = min(PARTICLE_EFFECTS["glow_alpha"], self.alpha)
        glow_color = (*self.color, int(glow_alpha))
        glow_surf = self._create_alpha_surface(int(self.glow_size))
        pygame.draw.circle(glow_surf, glow_color, (int(self.glow_size), int(self.glow_size)), int(self.glow_size))
        surface.blit(glow_surf, (self.x - self.glow_size, self.y - self.glow_size))

    def _draw_core(self, surface: pygame.Surface) -> None:
        particle_color = (*self.color, int(self.alpha))
        core_surf = self._create_alpha_surface(int(self.size))
        pygame.draw.circle(core_surf, particle_color, (int(self.size), int(self.size)), int(self.size))
        surface.blit(core_surf, (self.x - self.size, self.y - self.size))

class ShootingStar:
    def __init__(self, x: int, y: int, color: Tuple[int, int, int]) -> None:
        self.x = float(x)
        self.y = float(y)
        self.color = color
        self.life = STAR_LIFESPAN_FRAMES
        self.dx = random.uniform(-2, 2)
        self.dy = random.uniform(STAR_MIN_SPEED, STAR_MAX_SPEED)

    def update(self) -> None:
        self.x += self.dx
        self.y += self.dy
        self.life -= 1

    def draw(self, surface: pygame.Surface) -> None:
        if self.life > 0:
            start_pos = (int(self.x), int(self.y))
            end_pos = (int(self.x - self.dx * STAR_TRAIL_LENGTH), int(self.y - self.dy * STAR_TRAIL_LENGTH))
            pygame.draw.line(surface, self.color, start_pos, end_pos, 2)

# -------------------------
# Renderer (visuals & UI)
# -------------------------
class TetrisRenderer:
    def __init__(self):
        self.preview_animation_offset = 0.0
        self.preview_animation_direction = 1

    def draw_galaxy_background(self, surface: pygame.Surface) -> None:
        # vertical gradient like the earlier code
        for y_pos in range(SCREEN_HEIGHT):
            red = 20 + int(20 + 40 * math.sin(y_pos * 0.02))
            green = 20 + int(20 + 50 * math.sin(y_pos * 0.015 + 1))
            blue = 50 + int(50 + 50 * math.sin(y_pos * 0.01 + 2))
            color = (max(0, min(red, 255)), max(0, min(green, 255)), max(0, min(blue, 255)))
            surface.fill(color, (0, y_pos, FULL_WIDTH, 1))
        # sprinkle a few static stars (random)
        for _ in range(STAR_COUNT):
            x_pos = random.randint(0, FULL_WIDTH)
            y_pos = random.randint(0, SCREEN_HEIGHT)
            radius = random.choice([STAR_RADIUS_SMALL, STAR_RADIUS_MEDIUM])
            color = random.choice(STAR_COLORS)
            pygame.draw.circle(surface, color, (x_pos, y_pos), radius)

    def draw_grid(self, surface: pygame.Surface, grid: List[List[Union[int, Tuple[int, int, int]]]]) -> None:
        for y_pos, row in enumerate(grid):
            for x_pos, cell in enumerate(row):
                rect = pygame.Rect(x_pos * GRID_SIZE, y_pos * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                if cell and isinstance(cell, tuple):
                    pygame.draw.rect(surface, cell, rect.inflate(-PIECE_PADDING, -PIECE_PADDING))
                pygame.draw.rect(surface, GRID_LINE_COLOR, rect, 1)

    def draw_piece(self, surface: pygame.Surface, piece: Tetromino, is_ghost: bool = False) -> None:
        for y_offset, row in enumerate(piece.shape):
            for x_offset, val in enumerate(row):
                if val:
                    self._draw_block(surface, piece, x_offset, y_offset, is_ghost)

    def _draw_block(self, surface: pygame.Surface, piece: Tetromino, x_offset: int, y_offset: int, is_ghost: bool) -> None:
        rect = pygame.Rect((piece.x + x_offset) * GRID_SIZE, (piece.y + y_offset) * GRID_SIZE, GRID_SIZE, GRID_SIZE)
        if is_ghost:
            ghost_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(ghost_surface, (*TEXT_COLOR, GHOST_ALPHA), ghost_surface.get_rect(), PREVIEW_BOX_BORDER_WIDTH)
            surface.blit(ghost_surface, rect.topleft)
        else:
            pygame.draw.rect(surface, piece.color, rect.inflate(-PIECE_PADDING, -PIECE_PADDING))

    def draw_sidebar(self, surface: pygame.Surface, score: int, lines: int, stage: int) -> None:
        info = [f"Score: {score}", f"Lines: {lines}", f"Stage: {STAGE_NAMES[stage]}"]
        for i, text in enumerate(info):
            txt_img = FONT_SMALL.render(text, True, TEXT_COLOR)
            surface.blit(txt_img, (SCREEN_WIDTH + 20, INFO_BOX_Y + i * SIDEBAR_ITEM_SPACING))

    def draw_next_pieces(self, surface: pygame.Surface, next_pieces: List[Tetromino], stage: int) -> None:
        preview_count = PREVIEW_COUNTS[stage]
        if not preview_count:
            return
        self._update_preview_animation()
        title = FONT_SMALL.render("Next Pieces:", True, TEXT_COLOR)
        surface.blit(title, (PREVIEW_BOX_X, PREVIEW_BOX_Y - TEXT_OFFSET))
        for i in range(preview_count):
            if i < len(next_pieces):
                self._draw_single_preview(surface, next_pieces[i], i)

    def _update_preview_animation(self) -> None:
        self.preview_animation_offset += (PREVIEW_ANIMATION_SPEED * self.preview_animation_direction)
        if abs(self.preview_animation_offset) > PREVIEW_ANIMATION_MAX_OFFSET:
            self.preview_animation_direction *= -1

    def _draw_single_preview(self, surface: pygame.Surface, piece: Tetromino, index: int) -> None:
        box_y = (PREVIEW_BOX_Y + index * PREVIEW_BOX_SPACING + int(self.preview_animation_offset))
        box_size = GRID_SIZE * PREVIEW_PIECE_AREA_SIZE + PREVIEW_BOX_PADDING * 2
        box_rect = pygame.Rect(PREVIEW_BOX_X - PREVIEW_BOX_PADDING, box_y - PREVIEW_BOX_PADDING, box_size, box_size)
        self._draw_preview_box(surface, box_rect, index)
        self._draw_preview_piece(surface, piece, box_y)

    def _draw_preview_box(self, surface: pygame.Surface, rect: pygame.Rect, index: int) -> None:
        time_ticks = pygame.time.get_ticks()
        pulse = math.sin(time_ticks * PREVIEW_GLOW_PULSE_SPEED + index)
        glow_alpha = (PREVIEW_GLOW_BASE_ALPHA + int(PREVIEW_GLOW_PULSE_MAGNITUDE * pulse))
        border_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
        color_index = index % len(VIBRANT_PASTELS)
        border_color = (*VIBRANT_PASTELS[color_index], max(10, glow_alpha))
        pygame.draw.rect(border_surf, border_color, border_surf.get_rect(), border_radius=PREVIEW_BOX_BORDER_RADIUS)
        outline_color = (255, 255, 255, max(6, glow_alpha // 2))
        pygame.draw.rect(border_surf, outline_color, border_surf.get_rect(), PREVIEW_BOX_BORDER_WIDTH, border_radius=PREVIEW_BOX_BORDER_RADIUS)
        surface.blit(border_surf, rect.topleft)

    def _draw_preview_piece(self, surface: pygame.Surface, piece: Tetromino, box_y: int) -> None:
        max_width = max(len(row) for row in piece.shape)
        max_height = len(piece.shape)
        x_start = (PREVIEW_BOX_X + (PREVIEW_PIECE_AREA_SIZE - max_width) * GRID_SIZE // 2)
        y_start = (box_y + (PREVIEW_PIECE_AREA_SIZE - max_height) * GRID_SIZE // 2)
        for y_offset, row in enumerate(piece.shape):
            for x_offset, val in enumerate(row):
                if val:
                    rect = pygame.Rect(x_start + x_offset * GRID_SIZE, y_start + y_offset * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                    pygame.draw.rect(surface, piece.color, rect.inflate(-PIECE_PADDING, -PIECE_PADDING))
                    self._draw_piece_highlight(surface, rect, piece.color)

    def _draw_piece_highlight(self, surface: pygame.Surface, rect: pygame.Rect, color: tuple) -> None:
        highlight_color = tuple(min(c + PREVIEW_HIGHLIGHT_BRIGHTNESS, 255) for c in color)
        highlight_alpha_color = (*highlight_color, PREVIEW_HIGHLIGHT_ALPHA)
        highlight_rect = rect.inflate(-GHOST_PADDING, -GHOST_PADDING)
        highlight_rect.height //= 2
        # draw highlight with alpha
        highlight_surf = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(highlight_surf, highlight_alpha_color, highlight_surf.get_rect(), border_radius=PREVIEW_HIGHLIGHT_BORDER_RADIUS)
        surface.blit(highlight_surf, (highlight_rect.x, highlight_rect.y))

    def draw_game_over(self, surface: pygame.Surface) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(GAME_OVER_OVERLAY_COLOR)
        surface.blit(overlay, (0, 0))
        game_over_text = FONT_LARGE.render("LOST IN SPACE!", True, GAME_OVER_TEXT_COLOR)
        text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 50))
        surface.blit(game_over_text, text_rect)
        restart_text = FONT_SMALL.render("Press R or Start to Restart", True, TEXT_COLOR)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 20))
        surface.blit(restart_text, restart_rect)

    def draw_stage_transition(self, surface: pygame.Surface, text: str) -> None:
        text_render = FONT_LARGE.render(text, True, TEXT_COLOR)
        rect = text_render.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
        surface.blit(text_render, rect)

# -------------------------
# Tetris Game core (merged)
# -------------------------
class TetrisGameMerged:
    def __init__(self) -> None:
        # board is GRID_HEIGHT rows by GRID_WIDTH cols
        self.grid: List[List[Union[int, Tuple[int, int, int]]]] = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece: Optional[Tetromino] = None
        self.next_pieces: List[Tetromino] = []
        self.game_state = GameStateData()
        self.stage_info = StageInfo()
        self.effects = VisualEffects()
        self.renderer = TetrisRenderer()
        self.sound_manager = SoundManager()
        self.joystick: Optional[pygame.joystick.Joystick] = None
        self.last_movement_time = 0
        self.last_axis_time = {"left": 0, "right": 0, "down": 0}
        self.move_cooldown = MOVEMENT_COOLDOWN_MS
        self._init_joystick()
        self._init_visuals()
        self.reset_game()

    def _init_joystick(self) -> None:
        if pygame.joystick.get_count() > 0:
            try:
                self.joystick = pygame.joystick.Joystick(0)
                self.joystick.init()
                print("Controller detected:", self.joystick.get_name())
            except Exception as e:
                print("Failed to init joystick:", e)
                self.joystick = None
        else:
            print("No controller found — using keyboard controls")

    def _init_visuals(self) -> None:
        # initialize some stars and an empty particles list
        for _ in range(STAR_COUNT):
            self.effects.stars.append(ShootingStar(random.randint(0, FULL_WIDTH), random.randint(0, SCREEN_HEIGHT), random.choice(STAR_COLORS)))
        self.effects.particles = []

    def reset_game(self) -> None:
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.game_state = GameStateData()
        self.stage_info = StageInfo()
        self.effects = VisualEffects(stars=[], particles=[])
        self.renderer = TetrisRenderer()
        self.next_pieces = [self._new_piece() for _ in range(MAX_STAGE + 1)]
        self.spawn_piece()
        # start background music if available
        self.sound_manager.play_music()

        # re-init visuals
        self._init_visuals()
        self.last_movement_time = 0
        self.fall_time_ms = 0
        self.fall_speed = STAGE_SPEEDS[0]

    def stage(self) -> int:
        return min(MAX_STAGE, self.game_state.blocks_placed // BLOCKS_PER_STAGE)

    def _new_piece(self) -> Tetromino:
        shape = random.choice(SHAPES)
        color = random.choice(VIBRANT_PASTELS)
        return Tetromino(shape=[row[:] for row in shape], color=color, x=GRID_WIDTH // 2 - 1, y=-len(shape))

    def spawn_piece(self) -> None:
        if self.game_state.game_over:
            return
        self.current_piece = self.next_pieces.pop(0)
        self.next_pieces.append(self._new_piece())
        # if spawn collides -> game over
        if not self._is_valid_position(self.current_piece):
            self._handle_game_over()

    def _is_valid_position(self, piece: Tetromino, dx: int = 0, dy: int = 0, shape: Optional[List[List[int]]] = None) -> bool:
        if shape is None:
            shape = piece.shape
        for y_offset, row in enumerate(shape):
            for x_offset, val in enumerate(row):
                if val:
                    x = piece.x + x_offset + dx
                    y = piece.y + y_offset + dy
                    if x < 0 or x >= GRID_WIDTH or y >= GRID_HEIGHT:
                        return False
                    if y >= 0 and self.grid[y][x] != 0:
                        return False
        return True

    def _lock_piece(self) -> None:
        piece = self.current_piece
        if piece is None:
            return
        for y_offset, row in enumerate(piece.shape):
            for x_offset, val in enumerate(row):
                if val:
                    x = piece.x + x_offset
                    y = piece.y + y_offset
                    if y < 0:
                        # locked above playing field -> game over
                        self._handle_game_over()
                        return
                    self.grid[y][x] = piece.color
        # particles for landing
        self._spawn_block_land_particles(piece)
        self.game_state.blocks_placed += 1
        # swap in next piece and check lines
        self.spawn_piece()
        self._clear_lines()

    def _clear_lines(self) -> None:
        lines = 0
        for y in range(GRID_HEIGHT - 1, -1, -1):
            if all(self.grid[y][x] != 0 for x in range(GRID_WIDTH)):
                # remove row and insert empty at top
                del self.grid[y]
                self.grid.insert(0, [0 for _ in range(GRID_WIDTH)])
                lines += 1
        if lines > 0:
            self.game_state.lines += lines
            self.game_state.score += lines * 100
            self._spawn_line_clear_particles(lines)
            self.sound_manager.play("clear")

    def _spawn_line_clear_particles(self, lines: int) -> None:
        count = PARTICLE_EFFECTS["line_clear_count"] * lines
        for _ in range(count):
            x = random.uniform(0, SCREEN_WIDTH)
            y = random.uniform(0, SCREEN_HEIGHT)
            color = random.choice(VIBRANT_PASTELS)
            self.effects.particles.append(Particle(x, y, color))

    def _spawn_block_land_particles(self, piece: Tetromino) -> None:
        count = PARTICLE_EFFECTS["block_land_count"]
        for _ in range(count):
            # spawn near piece center
            px = (piece.x + 1) * GRID_SIZE
            py = (piece.y + 1) * GRID_SIZE
            color = piece.color
            self.effects.particles.append(Particle(px + random.uniform(-10, 10), py + random.uniform(-10, 10), color))
        self.sound_manager.play("explosion")

    def _rotate_current(self) -> None:
        if not self.current_piece:
            return
        shape = self.current_piece.shape
        rotated = [list(row) for row in zip(*shape[::-1])]
        if self._is_valid_position(self.current_piece, shape=rotated):
            self.current_piece.shape = rotated
            self.sound_manager.play("explosion")

    def _hard_drop(self) -> None:
        if not self.current_piece:
            return
        while self._is_valid_position(self.current_piece, dy=1):
            self.current_piece.y += 1
        self.sound_manager.play("explosion")
        self._lock_piece()

    def _move(self, dx: int, dy: int = 0) -> None:
        if not self.current_piece:
            return
        if dx != 0:
            if self._is_valid_position(self.current_piece, dx=dx):
                self.current_piece.x += dx
        if dy != 0:
            if self._is_valid_position(self.current_piece, dy=dy):
                self.current_piece.y += dy
            else:
                # if can't move down, lock it
                self._lock_piece()

    def _get_ghost_piece(self) -> Optional[Tetromino]:
        if not self.current_piece:
            return None
        ghost = Tetromino(shape=[row[:] for row in self.current_piece.shape], color=self.current_piece.color, x=self.current_piece.x, y=self.current_piece.y)
        while self._is_valid_position(ghost, dy=1):
            ghost.y += 1
        return ghost

    def _handle_game_over(self) -> None:
        self.game_state.game_over = True
        self.sound_manager.play("gameover")
        pygame.mixer.music.stop()

    # -------------------------
    # Input handlers (keyboard + joystick)
    # -------------------------
    def handle_keydown(self, key: int) -> None:
        if key == pygame.K_LEFT:
            self._move(-1, 0)
        elif key == pygame.K_RIGHT:
            self._move(1, 0)
        elif key == pygame.K_DOWN:
            self._move(0, 1)
        elif key == pygame.K_UP:
            self._rotate_current()
        elif key == pygame.K_SPACE:
            self._hard_drop()
        elif key == pygame.K_r:
            if self.game_state.game_over:
                self.reset_game()

    def handle_joystick_button(self, button: int) -> None:
        # restart on Start (common index 7)
        if self.game_state.game_over:
            if button == 7:
                self.reset_game()
            return
        # button mappings: try to be flexible
        if button in [0, 2]:  # A/X
            self._rotate_current()
        elif button in [1, 3]:  # B/Y
            self._hard_drop()
        elif button == 7:  # Start to restart
            if self.game_state.game_over:
                self.reset_game()

    def handle_joystick_axis(self, axis: int, value: float) -> None:
        now = pygame.time.get_ticks()
        if axis == 0:
            # left / right
            if value < -AXIS_THRESHOLD and now - self.last_axis_time["left"] > self.move_cooldown:
                self._move(-1, 0)
                self.last_axis_time["left"] = now
            elif value > AXIS_THRESHOLD and now - self.last_axis_time["right"] > self.move_cooldown:
                self._move(1, 0)
                self.last_axis_time["right"] = now
        elif axis == 1:
            # down (soft drop)
            if value > AXIS_THRESHOLD and now - self.last_axis_time["down"] > self.move_cooldown:
                self._move(0, 1)
                self.last_axis_time["down"] = now

    def handle_hat(self, hat_value: Tuple[int, int]) -> None:
        hx, hy = hat_value
        if hx == -1:
            self._move(-1, 0)
        elif hx == 1:
            self._move(1, 0)
        if hy == -1:
            self._move(0, 1)

    # -------------------------
    # Update & render loop
    # -------------------------
    def update(self, dt_ms: int) -> None:
        # update effects
        for star in list(self.effects.stars):
            star.update()
            if star.life <= 0:
                self.effects.stars.remove(star)
        # maybe spawn a new star occasionally
        if random.random() < STAR_SPAWN_CHANCE:
            self.effects.stars.append(ShootingStar(random.randint(0, FULL_WIDTH), -10, random.choice(STAR_COLORS)))

        for p in list(self.effects.particles):
            p.update()
            if p.life <= 0 or p.alpha <= 0:
                try:
                    self.effects.particles.remove(p)
                except ValueError:
                    pass

        # update fall speed based on stage
        current_stage = self.stage()
        self.fall_speed = STAGE_SPEEDS[current_stage]
        # automatic falling: accumulate time
        if not hasattr(self, 'fall_time_ms'):
            self.fall_time_ms = 0
        self.fall_time_ms += dt_ms
        if self.fall_time_ms >= int(self.fall_speed * 1000):
            self.fall_time_ms = 0
            if self.current_piece and self._is_valid_position(self.current_piece, dy=1):
                self.current_piece.y += 1
            else:
                # can't move down -> lock piece (if exists)
                if self.current_piece:
                    self._lock_piece()

    def draw(self, surface: pygame.Surface) -> None:
        # background & starfield
        self.renderer.draw_galaxy_background(surface)
        for star in self.effects.stars:
            star.draw(surface)

        # playfield surface
        play_surf = pygame.Surface((GRID_WIDTH * GRID_SIZE, GRID_HEIGHT * GRID_SIZE), pygame.SRCALPHA)
        self.renderer.draw_grid(play_surf, self.grid)

        # ghost piece
        ghost = self._get_ghost_piece()
        if ghost:
            self.renderer.draw_piece(play_surf, ghost, is_ghost=True)

        # current piece
        if self.current_piece:
            self.renderer.draw_piece(play_surf, self.current_piece, is_ghost=False)

        # blit playfield
        surface.blit(play_surf, (0, 0))

        # next previews & UI on sidebar
        self.renderer.draw_next_pieces(surface, self.next_pieces, self.stage())
        self.renderer.draw_sidebar(surface, self.game_state.score, self.game_state.lines, self.stage())

        # draw particles on top
        for p in self.effects.particles:
            p.draw(surface)

        # Game over overlay
        if self.game_state.game_over:
            self.renderer.draw_game_over(surface)

    # -------------------------
    # Main run loop
    # -------------------------
    def run(self) -> None:
        clock = pygame.time.Clock()
        screen = pygame.display.set_mode((FULL_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Galaxy Tetris (Controller + Pastel Theme)")

        running = True
        while running:
            dt_ms = clock.tick(FPS)
            # event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_keydown(event.key)
                elif event.type == pygame.JOYBUTTONDOWN:
                    self.handle_joystick_button(event.button)
                elif event.type == pygame.JOYAXISMOTION:
                    self.handle_joystick_axis(event.axis, event.value)
                elif event.type == pygame.JOYHATMOTION:
                    self.handle_hat(event.value)
            # also support keyboard holding for smooth movement based on real time
            keys = pygame.key.get_pressed()
            now = pygame.time.get_ticks()
            if keys[pygame.K_LEFT] and now - self.last_movement_time > self.move_cooldown:
                self._move(-1, 0)
                self.last_movement_time = now
            if keys[pygame.K_RIGHT] and now - self.last_movement_time > self.move_cooldown:
                self._move(1, 0)
                self.last_movement_time = now
            if keys[pygame.K_DOWN] and now - self.last_movement_time > self.move_cooldown:
                self._move(0, 1)
                self.last_movement_time = now

            # update world
            self.update(dt_ms)
            # draw
            screen.fill((0, 0, 0))
            self.draw(screen)
            pygame.display.flip()

        pygame.quit()
        sys.exit()

# -------------------------
# Run game if main
# -------------------------
if __name__ == "__main__":
    game = TetrisGameMerged()
    game.run()
