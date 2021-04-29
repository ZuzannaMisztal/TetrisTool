from enum import Enum
import numpy as np
import pygame
import random
import copy

pygame.init()

BLOCK_SIZE = 30
BLOCK_FILLING = 28
BLOCK_MARGIN = 1
INFO_WIDTH = 200
BOARD_HEIGHT = 20
BOARD_WIDTH = 10
MAP_HEIGHT = BOARD_HEIGHT * BLOCK_SIZE
MAP_WIDTH = 2 * BOARD_WIDTH * BLOCK_SIZE + INFO_WIDTH
MAP_SIZE = [MAP_WIDTH, MAP_HEIGHT]
CLOCK = pygame.time.Clock()
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
BLUE = (71, 0, 178)
RED = (255, 0, 0)
GREEN = (0, 172, 23)
ORANGE = (255, 133, 0)
PINK = (255, 133, 155)
AQUA = (0, 255, 255)

COLORS = {
    'white': WHITE,
    'ye': YELLOW,
    'bl': BLUE,
    're': RED,
    'gr': GREEN,
    'or': ORANGE,
    'pi': PINK,
    'aq': AQUA
}


class Difficulty(Enum):
    EASY = 0
    MEDIUM = 1
    HARD = 2


class Settings:
    def __init__(self):
        self.number_of_players = 1
        self.difficulty = Difficulty.MEDIUM


class Tetromino:
    def __init__(self, color, position, squares, max_rotation):
        self.color = color
        self.pos = position
        self.squares = squares
        self.max_rot = max_rotation

    def rotate(self, times=1):
        for _ in range(times):
            for square in self.squares:
                square[0], square[1] = -square[1], square[0]

    def move_down(self, times=1):
        self.pos[1] += times

    def move_right(self, times=1):
        self.pos[0] += times


PIECES = {
    'S': Tetromino('re', [4, 1], [[-1, 0], [0, 0], [0, -1], [1, -1]], 2),
    'Z': Tetromino('gr', [4, 1], [[-1, -1], [0, -1], [0, 0], [1, 0]], 2),
    'J': Tetromino('pi', [4, 1], [[0, -1], [0, 0], [0, 1], [-1, 1]], 4),
    'L': Tetromino('or', [4, 1], [[0, -1], [0, 0], [0, 1], [1, 1]], 4),
    'I': Tetromino('bl', [4, 2], [[0, -2], [0, -1], [0, 0], [0, 1]], 2),
    'O': Tetromino('ye', [4, 0], [[0, 0], [1, 0], [0, 1], [1, 1]], 1),
    'T': Tetromino('aq', [4, 1], [[-1, 0], [0, 0], [1, 0], [0, -1]], 4)
}


def shut_down():
    pygame.quit()
    exit(1)


class Game:
    def __init__(self, game_display, settings):
        self.game_display = game_display
        self.settings = settings
        self.difficulty = settings.difficulty.value
        self.block_grid = np.full((BOARD_HEIGHT, BOARD_WIDTH), 'white')
        self.tetromino = self.generate_tetromino()
        self.next_tetromino = self.generate_tetromino()
        self.lines_cleared = 0
        self.game_over = False
        self.count = 1
        self.falling_speed = [40, 28, 24, 21, 18, 15, 13, 12, 11, 10, 9, 9, 9, 9, 9, 9, 9]

    @property
    def shift(self):
        return (MAP_WIDTH / 2) - (BOARD_WIDTH * BLOCK_SIZE / 2)

    @property
    def level(self):
        level = self.lines_cleared // 10 + 1
        if level > 11:
            return 11
        else:
            return level

    @staticmethod
    def generate_tetromino():
        return copy.deepcopy(random.choice(list(PIECES.values())))

    def is_valid_position(self, tetromino: Tetromino, block_grid, adj_x=0, adj_y=0, rot=0):
        test_tet = copy.deepcopy(tetromino)
        test_tet.rotate(rot)
        test_tet.move_down(adj_y)
        test_tet.move_right(adj_x)
        for square in test_tet.squares:
            x = test_tet.pos[0] + square[0]
            y = test_tet.pos[1] + square[1]
            if self.is_outside_board(x, y) or self.is_colliding(x, y, block_grid):
                return False
        return True

    @staticmethod
    def is_outside_board(x, y):
        return x < 0 or x > BOARD_WIDTH - 1 or y > BOARD_HEIGHT - 1

    @staticmethod
    def is_colliding(x, y, block_grid):
        return block_grid[y][x] != 'white'

    def run(self):
        while not self.game_over:
            if self.count % (self.falling_speed[self.difficulty + self.level - 1]) == 0:
                if self.is_valid_position(self.tetromino, self.block_grid, adj_y=1):
                    self.tetromino.move_down()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    shut_down()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RIGHT:
                        if self.is_valid_position(self.tetromino, self.block_grid, adj_x=1):
                            self.tetromino.move_right()
                    if event.key == pygame.K_LEFT:
                        if self.is_valid_position(self.tetromino, self.block_grid, adj_x=-1):
                            self.tetromino.move_right(-1)
                    if event.key == pygame.K_DOWN:
                        if self.is_valid_position(self.tetromino, self.block_grid, adj_y=1):
                            self.tetromino.move_down()
                    if event.key == pygame.K_UP:
                        if self.is_valid_position(self.tetromino, self.block_grid, rot=1):
                            self.tetromino.rotate()
                    if event.key == pygame.K_SPACE:
                        while self.is_valid_position(self.tetromino, self.block_grid, adj_y=1):
                            self.tetromino.move_down()
            if not self.is_valid_position(self.tetromino, self.block_grid, adj_y=1):
                self.blend_tetromino(self.tetromino, self.block_grid)
                self.replace_tetromino()
                if not self.is_valid_position(self.tetromino, self.block_grid):
                    self.game_over = True
            self.clear_lines()
            self.draw()
            CLOCK.tick(FPS)
            self.count += 1
        self.show_results()

    @staticmethod
    def blend_tetromino(tetromino, block_grid):
        for square in tetromino.squares:
            x = tetromino.pos[0] + square[0]
            y = tetromino.pos[1] + square[1]
            block_grid[y][x] = tetromino.color

    def replace_tetromino(self):
        self.tetromino = self.next_tetromino
        self.next_tetromino = self.generate_tetromino()

    def clear_lines(self):
        for i, row in enumerate(self.block_grid):
            if np.any([color == 'white' for color in row]):
                continue
            self.block_grid = np.delete(self.block_grid, i, axis=0)
            clear_row = np.full((1, BOARD_WIDTH), 'white')
            self.block_grid = np.vstack((clear_row, self.block_grid))
            self.lines_cleared += 1

    def draw(self):
        self.game_display.fill(BLACK)
        self.draw_board(self.block_grid, self.shift)
        self.draw_tetromino(self.tetromino, self.shift)
        self.draw_next_tetromino(self.shift + BOARD_WIDTH * BLOCK_SIZE + 50)
        self.print_score()
        pygame.display.update()

    def draw_board(self, block_grid, shift):
        pygame.draw.rect(self.game_display, WHITE, [shift, 0, BOARD_WIDTH * BLOCK_SIZE, BOARD_HEIGHT * BLOCK_SIZE])
        for y, row in enumerate(block_grid):
            for x, color in enumerate(row):
                if color != 'white':
                    self.draw_rect(x, y, color, shift)

    def draw_rect(self, x, y, color, shift):
        pygame.draw.rect(self.game_display, BLACK,
                         [x * BLOCK_SIZE + shift, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE])
        pygame.draw.rect(self.game_display, COLORS[color],
                         [x * BLOCK_SIZE + BLOCK_MARGIN + shift,
                          y * BLOCK_SIZE + BLOCK_MARGIN,
                          BLOCK_FILLING, BLOCK_FILLING])

    def draw_tetromino(self, tetromino, shift):
        tet = tetromino
        for square in tet.squares:
            self.draw_rect(tet.pos[0] + square[0], tet.pos[1] + square[1], tet.color, shift)

    def print_score(self):
        font = pygame.font.SysFont('monospace', 20)
        text1 = font.render(f"Lines cleared: {self.lines_cleared}", True, WHITE)
        self.game_display.blit(text1, [self.shift + BOARD_WIDTH * BLOCK_SIZE + 30, MAP_HEIGHT / 2])

    def show_results(self):
        self.game_display.fill(BLACK)
        font = pygame.font.SysFont('monospace', 20)
        text1 = font.render(f"Congratulations!!! You cleared {self.lines_cleared} lines", True, WHITE)
        self.game_display.blit(text1, [60, MAP_HEIGHT/2 - 60])
        text2 = font.render("Press b to go back to menu", True, WHITE)
        self.game_display.blit(text2, [60, MAP_HEIGHT / 2])
        pygame.display.update()
        results = True
        while results:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    shut_down()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_b:
                        results = False
        intro = Intro(self.game_display, self.settings)
        intro.run()

    def draw_next_tetromino(self, shift):
        pygame.draw.rect(self.game_display, WHITE, [shift, BLOCK_SIZE, 5 * BLOCK_SIZE, 6 * BLOCK_SIZE])
        tet = self.next_tetromino
        for square in tet.squares:
            self.draw_rect(tet.pos[0] + square[0] - 2, tet.pos[1] + square[1] + 2, tet.color, shift)


class GameFor2(Game):
    def __init__(self, game_display, settings):
        super().__init__(game_display, settings)
        self.tetromino_left = copy.deepcopy(self.tetromino)
        self.block_grid_left = np.full((BOARD_HEIGHT, BOARD_WIDTH), 'white')
        self.lines_cleared_left = 0
        self.left_exists = True
        self.right_exists = True

    @property
    def shift(self):
        return BOARD_WIDTH * BLOCK_SIZE + INFO_WIDTH

    @property
    def level(self):
        level = (self.lines_cleared + self.lines_cleared_left) // 20 + 1
        if level > 11:
            return 11
        else:
            return level

    def run(self):
        while not self.game_over:
            if self.left_exists and self.right_exists:
                speed = self.falling_speed[self.difficulty + self.level - 1]
            else:
                speed = self.falling_speed[self.difficulty + self.level + 2]
            if not self.left_exists and not self.right_exists:
                self.tetromino = self.next_tetromino
                self.tetromino_left = copy.deepcopy(self.tetromino)
                self.next_tetromino = self.generate_tetromino()
                if not self.is_valid_position(self.tetromino, self.block_grid) or not self.is_valid_position(self.tetromino_left, self.block_grid_left):
                    self.game_over = True
                self.left_exists = True
                self.right_exists = True

            if self.count % speed == 0:
                if self.right_exists:
                    if self.is_valid_position(self.tetromino, self.block_grid, adj_y=1):
                        self.tetromino.move_down()
                if self.left_exists:
                    if self.is_valid_position(self.tetromino_left, self.block_grid_left, adj_y=1):
                        self.tetromino_left.move_down()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    shut_down()
                if event.type == pygame.KEYDOWN:
                    if self.right_exists:
                        if event.key == pygame.K_RIGHT:
                            if self.is_valid_position(self.tetromino, self.block_grid, adj_x=1):
                                self.tetromino.move_right()
                        if event.key == pygame.K_LEFT:
                            if self.is_valid_position(self.tetromino, self.block_grid, adj_x=-1):
                                self.tetromino.move_right(-1)
                        if event.key == pygame.K_DOWN:
                            if self.is_valid_position(self.tetromino, self.block_grid, adj_y=1):
                                self.tetromino.move_down()
                        if event.key == pygame.K_UP:
                            if self.is_valid_position(self.tetromino, self.block_grid, rot=1):
                                self.tetromino.rotate()
                        if event.key == pygame.K_SPACE:
                            while self.is_valid_position(self.tetromino, self.block_grid, adj_y=1):
                                self.tetromino.move_down()
                    if self.left_exists:
                        if event.key == pygame.K_d:
                            if self.is_valid_position(self.tetromino_left, self.block_grid_left, adj_x=1):
                                self.tetromino_left.move_right()
                        if event.key == pygame.K_a:
                            if self.is_valid_position(self.tetromino_left, self.block_grid_left, adj_x=-1):
                                self.tetromino_left.move_right(-1)
                        if event.key == pygame.K_s:
                            if self.is_valid_position(self.tetromino_left, self.block_grid_left, adj_y=1):
                                self.tetromino_left.move_down()
                        if event.key == pygame.K_w:
                            if self.is_valid_position(self.tetromino_left, self.block_grid_left, rot=1):
                                self.tetromino_left.rotate()
                        if event.key == pygame.K_t:
                            while self.is_valid_position(self.tetromino_left, self.block_grid_left, adj_y=1):
                                self.tetromino_left.move_down()
            if self.right_exists:
                if not self.is_valid_position(self.tetromino, self.block_grid, adj_y=1):
                    self.blend_tetromino(self.tetromino, self.block_grid)
                    self.right_exists = False
            if self.left_exists:
                if not self.is_valid_position(self.tetromino_left, self.block_grid_left, adj_y=1):
                    self.blend_tetromino(self.tetromino_left, self.block_grid_left)
                    self.left_exists = False
            self.clear_lines()
            self.draw()
            CLOCK.tick(FPS)
            self.count += 1
        self.show_results()

    def show_results(self):
        self.game_display.fill(BLACK)
        font = pygame.font.SysFont('monospace', 20)
        text1 = font.render(f"Congratulations!!! You cleared {self.lines_cleared} lines", True, WHITE)
        self.game_display.blit(text1, [60, MAP_HEIGHT/2 - 60])
        text2 = font.render("Press b to go back to menu", True, WHITE)
        self.game_display.blit(text2, [60, MAP_HEIGHT / 2])
        pygame.display.update()
        results = True
        while results:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    shut_down()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_b:
                        results = False
        intro = Intro(self.game_display, self.settings)
        intro.run()

    def draw(self):
        self.game_display.fill(BLACK)
        self.draw_board(self.block_grid, self.shift)
        if self.right_exists:
            self.draw_tetromino(self.tetromino, self.shift)
        self.draw_board(self.block_grid_left, 0)
        if self.left_exists:
            self.draw_tetromino(self.tetromino_left, 0)
        #self.draw_tetromino(self.tetromino_left, 0)
        self.draw_next_tetromino(BOARD_WIDTH * BLOCK_SIZE + 20)
        self.print_score()
        pygame.display.update()

    def print_score(self):
        font = pygame.font.SysFont('monospace', 12)
        text1 = font.render(f"Left lines cleared: {self.lines_cleared_left}", True, WHITE)
        self.game_display.blit(text1, [BOARD_WIDTH * BLOCK_SIZE + 10, MAP_HEIGHT / 2])
        text2 = font.render(f"Right lines cleared: {self.lines_cleared}", True, WHITE)
        self.game_display.blit(text2, [BOARD_WIDTH * BLOCK_SIZE + 10, MAP_HEIGHT / 2 - 30])

    def clear_lines(self):
        super().clear_lines()
        for i, row in enumerate(self.block_grid_left):
            if np.any([color == 'white' for color in row]):
                continue
            self.block_grid_left = np.delete(self.block_grid_left, i, axis=0)
            clear_row = np.full((1, BOARD_WIDTH), 'white')
            self.block_grid_left = np.vstack((clear_row, self.block_grid_left))
            self.lines_cleared_left += 1


class Intro:
    def __init__(self, game_display=pygame.display.set_mode(MAP_SIZE), settings=Settings()):
        self.game_display = game_display
        self.settings = settings

    def run(self):
        intro = True
        while intro:
            self.draw()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    shut_down()
                if event.type == pygame.KEYDOWN:  #  Wszystko do zamiany na klikanie
                    if event.key == pygame.K_1:
                        self.settings.number_of_players = 1
                    if event.key == pygame.K_2:
                        self.settings.number_of_players = 2
                    if event.key == pygame.K_e:
                        self.settings.difficulty = Difficulty.EASY
                    if event.key == pygame.K_m:
                        self.settings.difficulty = Difficulty.MEDIUM
                    if event.key == pygame.K_h:
                        self.settings.difficulty = Difficulty.HARD
                    if event.key == pygame.K_p:
                        intro = False
            CLOCK.tick(FPS)
        if self.settings.number_of_players == 1:
            game = Game(self.game_display, self.settings)
        else:
            game = GameFor2(self.game_display, self.settings)
            pass
        game.run()

    def draw(self):
        self.game_display.fill(BLACK)
        self._print_instructions()  #  zamiast tego wyświetlanie przycisków
        pygame.display.update()

    def _print_instructions(self):
        font = pygame.font.SysFont('monospace', 20)
        text1 = font.render("Press 1 or 2 to choose number of players", True, WHITE)
        text2 = font.render("Press e, m or h to choose difficulty", True, WHITE)
        self.game_display.blit(text1, [110, MAP_HEIGHT / 2 - 40])
        self.game_display.blit(text2, [110, MAP_HEIGHT / 2 - 10])
        text3 = font.render("Press p to play", True, WHITE)
        self.game_display.blit(text3, [110, MAP_HEIGHT / 2 + 20])


if __name__ == '__main__':
    intro = Intro()
    intro.run()
