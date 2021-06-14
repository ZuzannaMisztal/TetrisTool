from enum import Enum

from more_itertools import pairwise
import numpy as np
import pygame
import random
from copy import deepcopy
from collections import Counter

pygame.init()
pygame.display.set_caption('TETRIS')

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
CLUE_COLOR = (218, 219, 208)

COLORS = {
    'white': WHITE,
    'ye': YELLOW,
    'bl': BLUE,
    're': RED,
    'gr': GREEN,
    'or': ORANGE,
    'pi': PINK,
    'aq': AQUA,
    'cc': CLUE_COLOR
}


class Difficulty(Enum):
    EASY = 0
    MEDIUM = 1
    HARD = 2


class Settings:
    def __init__(self):
        self.game_version = 1
        self.difficulty = Difficulty.MEDIUM


class Tetromino:
    def __init__(self, color, position, squares, max_rotation):
        self.color = color
        self.pos = position
        self.squares = squares
        self.max_rot = max_rotation

    def rotate(self, times=1):
        if self.max_rot > 1:
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


class Player:
    def __init__(self, tetromino, block_gird=np.full((BOARD_HEIGHT, BOARD_WIDTH), 'white')):
        self.block_grid = deepcopy(block_gird)
        self.tetromino = deepcopy(tetromino)
        self.lines_cleared = 0

    def is_valid_move(self, adj_x=0, adj_y=0, rot=0):
        test_tet = deepcopy(self.tetromino)
        test_tet.rotate(rot)
        test_tet.move_down(adj_y)
        test_tet.move_right(adj_x)
        for square in test_tet.squares:
            x = test_tet.pos[0] + square[0]
            y = test_tet.pos[1] + square[1]
            if self.is_outside_board(x, y) or self.is_colliding(x, y):
                return False
        return True

    @staticmethod
    def is_outside_board(x, y):
        return x < 0 or x > BOARD_WIDTH - 1 or y > BOARD_HEIGHT - 1

    def is_colliding(self, x, y):
        return self.block_grid[y][x] != 'white'

    def blend_tetromino(self):
        for square in self.tetromino.squares:
            x = self.tetromino.pos[0] + square[0]
            y = self.tetromino.pos[1] + square[1]
            self.block_grid[y][x] = self.tetromino.color

    def clear_lines(self):
        for i, row in enumerate(self.block_grid):
            if np.any([color == 'white' for color in row]):
                continue
            self.block_grid = np.delete(self.block_grid, i, axis=0)
            clear_row = np.full((1, BOARD_WIDTH), 'white')
            self.block_grid = np.vstack((clear_row, self.block_grid))
            self.lines_cleared += 1


class RealPlayer(Player):
    def __init__(self, tetromino, k_left=pygame.K_LEFT, k_right=pygame.K_RIGHT, k_up=pygame.K_UP, k_down=pygame.K_DOWN, k_space=pygame.K_SPACE):
        super().__init__(tetromino)
        self.k_left = k_left
        self.k_right = k_right
        self.k_up = k_up
        self.k_down = k_down
        self.k_space = k_space

    def respond_to_control(self, key):
        if key == self.k_right:
            if self.is_valid_move(adj_x=1):
                self.tetromino.move_right()
        if key == self.k_left:
            if self.is_valid_move(adj_x=-1):
                self.tetromino.move_right(-1)
        if key == self.k_down:
            if self.is_valid_move(adj_y=1):
                self.tetromino.move_down()
        if key == self.k_up:
            if self.is_valid_move(rot=1):
                self.tetromino.rotate()
        if key == self.k_space:
            while self.is_valid_move(adj_y=1):
                self.tetromino.move_down()


class Game:
    def __init__(self, game_display, settings):
        self.game_display = game_display
        self.settings = settings
        self.difficulty = settings.difficulty.value
        self.player = RealPlayer(self.generate_tetromino())
        self.next_tetromino = self.generate_tetromino()
        self.game_over = False
        self.count = 1
        self.falling_speed = [40, 28, 24, 21, 18, 15, 13, 12, 11, 10, 10, 10, 10, 10, 10, 10, 10]

    @property
    def shift(self):
        return (MAP_WIDTH / 2) - (BOARD_WIDTH * BLOCK_SIZE / 2)

    @property
    def level(self):
        level = self.player.lines_cleared // 10 + 1
        if level > 11:
            return 11
        else:
            return level

    @staticmethod
    def generate_tetromino():
        return deepcopy(random.choice(list(PIECES.values())))

    def run(self):
        while not self.game_over:
            if self.count % (self.falling_speed[self.difficulty + self.level - 1]) == 0:
                if self.player.is_valid_move(adj_y=1):
                    self.player.tetromino.move_down()
                else:
                    self.player.blend_tetromino()
                    self.player.clear_lines()
                    self.replace_tetromino()
                    if not self.player.is_valid_move():
                        self.game_over = True
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    shut_down()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        self.pause()
                    self.player.respond_to_control(event.key)
            self.draw()
            pygame.display.update()
            CLOCK.tick(FPS)
            self.count += 1
        self.show_results()

    def replace_tetromino(self):
        self.player.tetromino = self.next_tetromino
        self.next_tetromino = self.generate_tetromino()

    def draw(self):
        self.game_display.fill(BLACK)
        self.draw_board(self.player.block_grid, self.shift)
        self.draw_tetromino(self.player.tetromino, self.shift)
        self.draw_next_tetromino(self.shift + BOARD_WIDTH * BLOCK_SIZE + 50)
        self.print_score()

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
        text1 = font.render(f"Lines cleared: {self.player.lines_cleared}", True, WHITE)
        self.game_display.blit(text1, [self.shift + BOARD_WIDTH * BLOCK_SIZE + 30, MAP_HEIGHT / 2])

    def show_results(self):
        self.game_display.fill(BLACK)
        font = pygame.font.SysFont('monospace', 20)
        text1 = font.render(f"Congratulations!!! You cleared {self.player.lines_cleared} lines", True, WHITE)
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

    def pause(self):
        self.game_display.fill(BLACK)
        font = pygame.font.SysFont('monospace', 20)
        text = font.render("Press p to continue playing", True, WHITE)
        self.game_display.blit(text, [MAP_WIDTH / 2 - 150, MAP_HEIGHT / 2 - 30])
        text = font.render("Press b to go back to menu", True, WHITE)
        self.game_display.blit(text, [MAP_WIDTH / 2 - 150, MAP_HEIGHT / 2 + 30])
        pygame.display.update()
        loop = True
        while loop:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    shut_down()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_b:
                        loop = False
                        new_intro = Intro(self.game_display, self.settings)
                        new_intro.run()
                    if event.key == pygame.K_p:
                        loop = False


class GameFor2(Game):
    def __init__(self, game_display, settings):
        super().__init__(game_display, settings)
        self.player_left = RealPlayer(self.player.tetromino, k_left=pygame.K_a, k_right=pygame.K_d, k_up=pygame.K_w, k_down=pygame.K_s, k_space=pygame.K_t)
        self.left_exists = True
        self.right_exists = True

    @property
    def shift(self):
        return BOARD_WIDTH * BLOCK_SIZE + INFO_WIDTH

    @property
    def level(self):
        level = (self.player.lines_cleared + self.player_left.lines_cleared) // 20 + 1
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
                self.player.tetromino = self.next_tetromino
                self.player_left.tetromino = deepcopy(self.next_tetromino)
                self.next_tetromino = self.generate_tetromino()
                if not self.player.is_valid_move() or not self.player_left.is_valid_move():
                    self.game_over = True
                self.left_exists = True
                self.right_exists = True

            if self.count % speed == 0:
                if self.right_exists:
                    if self.player.is_valid_move(adj_y=1):
                        self.player.tetromino.move_down()
                    else:
                        self.player.blend_tetromino()
                        self.right_exists = False
                if self.left_exists:
                    if self.player_left.is_valid_move(adj_y=1):
                        self.player_left.tetromino.move_down()
                    else:
                        self.player_left.blend_tetromino()
                        self.left_exists = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    shut_down()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        self.pause()
                    if self.right_exists:
                        self.player.respond_to_control(event.key)
                    if self.left_exists:
                        self.player_left.respond_to_control(event.key)
            self.player.clear_lines()
            self.player_left.clear_lines()
            self.draw()
            CLOCK.tick(FPS)
            self.count += 1
        self.show_results()

    def show_results(self):
        self.game_display.fill(BLACK)
        font = pygame.font.SysFont('monospace', 20)
        text1 = font.render(f"Left player cleared {self.player_left.lines_cleared} lines", True, WHITE)
        self.game_display.blit(text1, [60, MAP_HEIGHT/2 - 60])
        text1 = font.render(f"Right player cleared {self.player.lines_cleared} lines", True, WHITE)
        self.game_display.blit(text1, [60, MAP_HEIGHT/2 - 30])
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
        self.draw_board(self.player.block_grid, self.shift)
        if self.right_exists:
            self.draw_tetromino(self.player.tetromino, self.shift)
        self.draw_board(self.player_left.block_grid, 0)
        if self.left_exists:
            self.draw_tetromino(self.player_left.tetromino, 0)
        self.draw_next_tetromino(BOARD_WIDTH * BLOCK_SIZE + 20)
        self.print_score()
        pygame.display.update()

    def print_score(self):
        font = pygame.font.SysFont('monospace', 12)
        text1 = font.render(f"Left lines cleared: {self.player_left.lines_cleared}", True, WHITE)
        self.game_display.blit(text1, [BOARD_WIDTH * BLOCK_SIZE + 10, MAP_HEIGHT / 2])
        text2 = font.render(f"Right lines cleared: {self.player.lines_cleared}", True, WHITE)
        self.game_display.blit(text2, [BOARD_WIDTH * BLOCK_SIZE + 10, MAP_HEIGHT / 2 - 30])


class GameWithAI(Game):
    def __init__(self, game_display, settings):
        super().__init__(game_display, settings)
        self.best_move = self.find_best_move()
        self.clue_tetromino = self.fit_clue_tetromino()

    def fit_clue_tetromino(self):
        player_AI = Player(deepcopy(self.player.tetromino), deepcopy(self.player.block_grid))
        player_AI.tetromino.rotate(times=self.best_move[0])
        player_AI.tetromino.move_right(times=self.best_move[1])
        while player_AI.is_valid_move(adj_y=1):
            player_AI.tetromino.move_down()
        player_AI.tetromino.color = 'cc'
        return deepcopy(player_AI.tetromino)

    def find_initial_moves(self):
        move_list = []
        score_list = []
        for rot in range(self.player.tetromino.max_rot):
            for sideways in range(-4, 6):
                move = (rot, sideways)
                result_board, lines_cleared = self.hypothetic_settle(move)
                if result_board is not None:
                    score = Calculator(result_board, lines_cleared).calculate()
                    move_list.append(move)
                    score_list.append(score)
        move_to_score = Counter(dict(zip(move_list, score_list)))
        best_moves = [move for move, score in move_to_score.most_common(4)]
        return best_moves

    def hypothetic_settle(self, move):
        player = Player(deepcopy(self.player.tetromino), deepcopy(self.player.block_grid))
        player.tetromino.rotate(move[0])
        player.tetromino.move_right(move[1])
        if not player.is_valid_move():
            return None, 0
        while player.is_valid_move(adj_y=1):
            player.tetromino.move_down()
        player.blend_tetromino()
        player.clear_lines()
        return player.block_grid, player.lines_cleared

    def draw(self):
        self.game_display.fill(BLACK)
        self.draw_board(self.player.block_grid, self.shift)
        self.draw_tetromino(self.clue_tetromino, self.shift)
        self.draw_tetromino(self.player.tetromino, self.shift)
        self.draw_next_tetromino(self.shift + BOARD_WIDTH * BLOCK_SIZE + 50)
        self.print_score()

    def replace_tetromino(self):
        super().replace_tetromino()
        self.best_move = self.find_best_move()
        self.clue_tetromino = self.fit_clue_tetromino()

    def find_best_move(self):
        move_list = []
        score_list = []
        for rot in range(self.player.tetromino.max_rot):
            for sideways in range(-4, 6):
                move = [rot, sideways]
                result_board, lines_cleared = self.hypothetic_settle(move)
                if result_board is not None:
                    score = Calculator(result_board, lines_cleared).calculate()
                    move_list.append(move)
                    score_list.append(score)
        return move_list[score_list.index(max(score_list))]


class Calculator:
    def __init__(self, block_grid, lines_cleared):
        self.block_grid = block_grid
        self.lines_cleared = lines_cleared

    def calculate(self):
        score = 40 * self.lines_cleared
        score += -2 * self.bumpiness()
        score += -30 * self.holes_simple()
        if self.is_it_game_over():
            score += -2000
        return score

    def bumpiness(self):
        column_heights = [self.column_height(column) for column in self.block_grid.T]
        result = sum(abs(pair[0] - pair[1]) for pair in pairwise(column_heights))
        if column_heights[1] > column_heights[0]:
            result += column_heights[1] - column_heights[0]
        if column_heights[-2] > column_heights[-1]:
            result += column_heights[-2] - column_heights[-1]
        return result

    def holes_simple(self):
        return sum(self.column_holes(column) for column in self.block_grid.T)

    def is_it_game_over(self):
        danger_zone = [[3, 2], [4, 2], [5, 2], [4, 3]]
        return np.any([self.block_grid[y][x] != 'white' for x, y in danger_zone])

    @staticmethod
    def column_height(column):
        height = BOARD_HEIGHT
        for color in column:
            if color != 'white':
                break
            height -= 1
        return height

    def column_holes(self, column):
        highest = self.column_height(column)
        return sum(1 for i in range(BOARD_HEIGHT - highest, BOARD_HEIGHT) if (column[i] == 'white'))


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
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        self.settings.game_version = 1
                    if event.key == pygame.K_2:
                        self.settings.game_version = 2
                    if event.key == pygame.K_3:
                        self.settings.game_version = 3
                    if event.key == pygame.K_e:
                        self.settings.difficulty = Difficulty.EASY
                    if event.key == pygame.K_m:
                        self.settings.difficulty = Difficulty.MEDIUM
                    if event.key == pygame.K_h:
                        self.settings.difficulty = Difficulty.HARD
                    if event.key == pygame.K_p:
                        intro = False
            CLOCK.tick(FPS)
        if self.settings.game_version == 1:
            game = Game(self.game_display, self.settings)
        elif self.settings.game_version == 2:
            game = GameFor2(self.game_display, self.settings)
        elif self.settings.game_version == 3:
            game = GameWithAI(self.game_display, self.settings)
        game.run()

    def draw(self):
        self.game_display.fill(BLACK)
        self._print_instructions()
        pygame.display.update()

    def _print_instructions(self):
        font0 = pygame.font.SysFont('monospace', 45)
        text0 = font0.render("TETRIS", True, WHITE)
        self.game_display.blit(text0, [627, 10])
        font = pygame.font.SysFont('monospace', 20)
        text1 = font.render("Press 1 for classic game", True, WHITE)
        text2 = font.render("Press 2 for two player game", True, WHITE)
        text3 = font.render("Press 3 for game with hints", True, WHITE)
        text4 = font.render("Press e, m or h to choose difficulty", True, WHITE)
        self.game_display.blit(text1, [200, 70])
        self.game_display.blit(text2, [200, 100])
        self.game_display.blit(text3, [200, 130])
        self.game_display.blit(text4, [200, 180])
        if self.settings.game_version != 2:
            text5 = font.render("Controls:", True, WHITE)
            text6 = font.render("Use arrows to move tetromino", True, WHITE)
            text7 = font.render("Use up arrow to rotate", True, WHITE)
            text8 = font.render("Use space to drop", True, WHITE)
            self.game_display.blit(text5, [130, 290])
            self.game_display.blit(text6, [40, 345])
            self.game_display.blit(text7, [70, 375])
            self.game_display.blit(text8, [100, 405])
        else:
            text5 = font.render("Controls:", True, WHITE)
            self.game_display.blit(text5, [320, 260])
            text6 = font.render("Right player", True, WHITE)
            text7 = font.render("Use arrows to move tetromino", True, WHITE)
            text8 = font.render("Use up arrow to rotate", True, WHITE)
            text9 = font.render("Use space to drop", True, WHITE)
            self.game_display.blit(text6, [500, 320])
            self.game_display.blit(text7, [410, 370])
            self.game_display.blit(text8, [440, 400])
            self.game_display.blit(text9, [470, 430])
            text10 = font.render("Left player", True, WHITE)
            text11 = font.render("Use a s d to move tetromino", True, WHITE)
            text12 = font.render("Use w to rotate", True, WHITE)
            text13 = font.render("Use t to drop", True, WHITE)
            self.game_display.blit(text10, [120, 320])
            self.game_display.blit(text11, [30, 370])
            self.game_display.blit(text12, [100, 400])
            self.game_display.blit(text13, [110, 430])
        text = font.render("Press p to play", True, WHITE)
        self.game_display.blit(text, [600, 550])


if __name__ == '__main__':
    intro = Intro()
    intro.run()
