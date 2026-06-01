from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field

try:
    import pygame
except ImportError as exc:  # pragma: no cover - helpful runtime message only
    pygame = None
    PYGAME_IMPORT_ERROR = exc
else:
    PYGAME_IMPORT_ERROR = None


ROWS = 6
COLS = 7
EMPTY = 0
HUMAN = 1
AI = 2

CELL_SIZE = 92
TOP_SPACE = 150
BOARD_MARGIN = 24
PANEL_WIDTH = 320
WINDOW_WIDTH = COLS * CELL_SIZE + PANEL_WIDTH + BOARD_MARGIN * 3
WINDOW_HEIGHT = TOP_SPACE + ROWS * CELL_SIZE + BOARD_MARGIN
FPS = 60

APP_BG = (8, 13, 26)
BOARD_COLOR = (56, 116, 245)
BOARD_FRAME = (31, 76, 194)
BOARD_GLOW = (121, 170, 255)
PANEL_BG = (16, 24, 39)
PANEL_CARD_BG = (23, 34, 54)
TEXT_COLOR = (241, 245, 249)
MUTED_TEXT = (148, 163, 184)
HUMAN_COLOR = (239, 68, 68)
AI_COLOR = (245, 196, 24)
EMPTY_COLOR = (216, 223, 236)
SLOT_COLOR = (9, 24, 58)
SLOT_RING = (93, 141, 255)
BUTTON_BG = (41, 96, 214)
BUTTON_HOVER = (59, 130, 246)
BUTTON_ACTIVE = (14, 165, 233)
STATUS_WIN = (22, 163, 74)
STATUS_DRAW = (71, 85, 105)
OUTLINE_COLOR = (33, 51, 76)
SHADOW_COLOR = (2, 6, 23)

POSITION_WEIGHTS = [
    [3, 4, 5, 7, 5, 4, 3],
    [4, 6, 8, 10, 8, 6, 4],
    [5, 8, 11, 13, 11, 8, 5],
    [5, 8, 11, 13, 11, 8, 5],
    [4, 6, 8, 10, 8, 6, 4],
    [3, 4, 5, 7, 5, 4, 3],
]


@dataclass(frozen=True)
class DifficultyProfile:
    name: str
    depth: int
    weights: dict[str, int]
    random_move_chance: float = 0.0


@dataclass
class SearchStats:
    nodes: int = 0
    prunes: int = 0


@dataclass
class AIReport:
    elapsed: float
    nodes: int
    prunes: int
    best_score: int
    top_moves: list[tuple[int, int]] = field(default_factory=list)


@dataclass
class UIButton:
    label: str
    action: str
    rect: "pygame.Rect"


def clamp_channel(value: float) -> int:
    return max(0, min(255, int(value)))


def brighten(color: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    return tuple(clamp_channel(c + (255 - c) * amount) for c in color)


def darken(color: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    return tuple(clamp_channel(c * (1 - amount)) for c in color)


DIFFICULTY_PROFILES = {
    "Easy": DifficultyProfile(
        name="Easy",
        depth=3,
        weights={
            "four": 100000,
            "three": 40,
            "two": 8,
            "block_three": 55,
            "block_two": 4,
            "center": 3,
            "position": 1,
        },
        random_move_chance=0.20,
    ),
    "Medium": DifficultyProfile(
        name="Medium",
        depth=4,
        weights={
            "four": 100000,
            "three": 90,
            "two": 12,
            "block_three": 120,
            "block_two": 10,
            "center": 4,
            "position": 1,
        },
        random_move_chance=0.05,
    ),
    "Hard": DifficultyProfile(
        name="Hard",
        depth=5,
        weights={
            "four": 100000,
            "three": 140,
            "two": 18,
            "block_three": 180,
            "block_two": 14,
            "center": 5,
            "position": 1,
        },
        random_move_chance=0.0,
    ),
}


class ConnectFourGame:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.board = [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]
        self.current_player = HUMAN
        self.game_over = False
        self.winner = EMPTY

    def is_valid_move(self, col: int, board: list[list[int]] | None = None) -> bool:
        board = self.board if board is None else board
        return 0 <= col < COLS and board[0][col] == EMPTY

    def get_valid_moves(self, board: list[list[int]] | None = None) -> list[int]:
        board = self.board if board is None else board
        return [col for col in range(COLS) if board[0][col] == EMPTY]

    def get_next_open_row(
        self, col: int, board: list[list[int]] | None = None
    ) -> int | None:
        board = self.board if board is None else board
        for row in range(ROWS - 1, -1, -1):
            if board[row][col] == EMPTY:
                return row
        return None

    def drop_piece(
        self, col: int, piece: int, board: list[list[int]] | None = None
    ) -> int | None:
        board = self.board if board is None else board
        row = self.get_next_open_row(col, board)
        if row is None:
            return None
        board[row][col] = piece
        return row

    def board_full(self, board: list[list[int]] | None = None) -> bool:
        board = self.board if board is None else board
        return all(board[0][col] != EMPTY for col in range(COLS))

    def get_winning_line(
        self, piece: int, board: list[list[int]] | None = None
    ) -> list[tuple[int, int]]:
        board = self.board if board is None else board

        for row in range(ROWS):
            for col in range(COLS - 3):
                if all(board[row][col + offset] == piece for offset in range(4)):
                    return [(row, col + offset) for offset in range(4)]

        for row in range(ROWS - 3):
            for col in range(COLS):
                if all(board[row + offset][col] == piece for offset in range(4)):
                    return [(row + offset, col) for offset in range(4)]

        for row in range(ROWS - 3):
            for col in range(COLS - 3):
                if all(board[row + offset][col + offset] == piece for offset in range(4)):
                    return [(row + offset, col + offset) for offset in range(4)]

        for row in range(3, ROWS):
            for col in range(COLS - 3):
                if all(board[row - offset][col + offset] == piece for offset in range(4)):
                    return [(row - offset, col + offset) for offset in range(4)]

        return []

    def check_winner(self, piece: int, board: list[list[int]] | None = None) -> bool:
        return bool(self.get_winning_line(piece, board))

    def iter_windows(self, board: list[list[int]]) -> list[list[int]]:
        windows: list[list[int]] = []

        for row in range(ROWS):
            for col in range(COLS - 3):
                windows.append([board[row][col + offset] for offset in range(4)])

        for row in range(ROWS - 3):
            for col in range(COLS):
                windows.append([board[row + offset][col] for offset in range(4)])

        for row in range(ROWS - 3):
            for col in range(COLS - 3):
                windows.append([board[row + offset][col + offset] for offset in range(4)])

        for row in range(3, ROWS):
            for col in range(COLS - 3):
                windows.append([board[row - offset][col + offset] for offset in range(4)])

        return windows

    def evaluate_window(self, window: list[int], weights: dict[str, int]) -> int:
        score = 0
        ai_count = window.count(AI)
        human_count = window.count(HUMAN)
        empty_count = window.count(EMPTY)

        if ai_count == 4:
            score += weights["four"]
        elif ai_count == 3 and empty_count == 1:
            score += weights["three"]
        elif ai_count == 2 and empty_count == 2:
            score += weights["two"]

        if human_count == 4:
            score -= weights["four"]
        elif human_count == 3 and empty_count == 1:
            score -= weights["block_three"]
        elif human_count == 2 and empty_count == 2:
            score -= weights["block_two"]

        return score

    def score_position(self, board: list[list[int]], weights: dict[str, int]) -> int:
        if self.check_winner(AI, board):
            return 1_000_000
        if self.check_winner(HUMAN, board):
            return -1_000_000

        score = 0
        center_col = COLS // 2

        for row in range(ROWS):
            if board[row][center_col] == AI:
                score += weights["center"]
            elif board[row][center_col] == HUMAN:
                score -= weights["center"]

        for row in range(ROWS):
            for col in range(COLS):
                if board[row][col] == AI:
                    score += POSITION_WEIGHTS[row][col] * weights["position"]
                elif board[row][col] == HUMAN:
                    score -= POSITION_WEIGHTS[row][col] * weights["position"]

        for window in self.iter_windows(board):
            score += self.evaluate_window(window, weights)

        return score


class ConnectFourAI:
    def __init__(self, game: ConnectFourGame) -> None:
        self.game = game

    def order_moves(
        self,
        board: list[list[int]],
        valid_moves: list[int],
        piece: int,
        weights: dict[str, int],
    ) -> list[int]:
        ranked_moves: list[tuple[int, int, int]] = []

        for col in valid_moves:
            row = self.game.get_next_open_row(col, board)
            if row is None:
                continue

            board[row][col] = piece
            score = self.game.score_position(board, weights)
            board[row][col] = EMPTY

            if piece == HUMAN:
                score = -score

            center_bias = -abs((COLS // 2) - col)
            ranked_moves.append((score, center_bias, col))

        ranked_moves.sort(reverse=True)
        return [col for _, _, col in ranked_moves]

    def minimax(
        self,
        board: list[list[int]],
        depth: int,
        alpha: float,
        beta: float,
        maximizing_player: bool,
        weights: dict[str, int],
        stats: SearchStats,
    ) -> tuple[int | None, int]:
        stats.nodes += 1

        valid_moves = self.game.get_valid_moves(board)
        ai_wins = self.game.check_winner(AI, board)
        human_wins = self.game.check_winner(HUMAN, board)

        if depth == 0 or ai_wins or human_wins or not valid_moves:
            if ai_wins:
                return None, 1_000_000 + depth
            if human_wins:
                return None, -1_000_000 - depth
            if not valid_moves:
                return None, 0
            return None, self.game.score_position(board, weights)

        if maximizing_player:
            best_score = -math.inf
            best_col = valid_moves[0]

            for col in self.order_moves(board, valid_moves, AI, weights):
                row = self.game.get_next_open_row(col, board)
                if row is None:
                    continue

                board[row][col] = AI
                _, score = self.minimax(
                    board, depth - 1, alpha, beta, False, weights, stats
                )
                board[row][col] = EMPTY

                if score > best_score:
                    best_score = score
                    best_col = col

                alpha = max(alpha, best_score)
                if alpha >= beta:
                    stats.prunes += 1
                    break

            return best_col, int(best_score)

        best_score = math.inf
        best_col = valid_moves[0]

        for col in self.order_moves(board, valid_moves, HUMAN, weights):
            row = self.game.get_next_open_row(col, board)
            if row is None:
                continue

            board[row][col] = HUMAN
            _, score = self.minimax(board, depth - 1, alpha, beta, True, weights, stats)
            board[row][col] = EMPTY

            if score < best_score:
                best_score = score
                best_col = col

            beta = min(beta, best_score)
            if alpha >= beta:
                stats.prunes += 1
                break

        return best_col, int(best_score)

    def choose_move(
        self, board: list[list[int]], profile: DifficultyProfile
    ) -> tuple[int | None, AIReport]:
        valid_moves = self.game.get_valid_moves(board)
        if not valid_moves:
            return None, AIReport(0.0, 0, 0, 0, [])

        if profile.random_move_chance and random.random() < profile.random_move_chance:
            chosen_col = random.choice(valid_moves)
            row = self.game.get_next_open_row(chosen_col, board)
            best_score = 0
            if row is not None:
                board[row][chosen_col] = AI
                best_score = self.game.score_position(board, profile.weights)
                board[row][chosen_col] = EMPTY
            report = AIReport(
                elapsed=0.0,
                nodes=0,
                prunes=0,
                best_score=int(best_score),
                top_moves=[(chosen_col, int(best_score))],
            )
            return chosen_col, report

        stats = SearchStats()
        start = time.perf_counter()
        best_score = -math.inf
        best_col = valid_moves[0]
        root_scores: list[tuple[int, int]] = []

        for col in self.order_moves(board, valid_moves, AI, profile.weights):
            row = self.game.get_next_open_row(col, board)
            if row is None:
                continue

            board[row][col] = AI
            _, score = self.minimax(
                board,
                profile.depth - 1,
                -math.inf,
                math.inf,
                False,
                profile.weights,
                stats,
            )
            board[row][col] = EMPTY

            root_scores.append((col, int(score)))
            if score > best_score:
                best_score = score
                best_col = col

        elapsed = time.perf_counter() - start
        top_moves = sorted(root_scores, key=lambda item: item[1], reverse=True)[:3]
        report = AIReport(
            elapsed=elapsed,
            nodes=stats.nodes,
            prunes=stats.prunes,
            best_score=int(best_score),
            top_moves=top_moves,
        )
        return best_col, report


class ConnectFourUI:
    def __init__(self, headless: bool = False) -> None:
        if pygame is None:
            raise SystemExit(
                "Pygame is not installed. Install it with "
                "'python -m pip install pygame-ce' and run again."
            ) from PYGAME_IMPORT_ERROR

        pygame.init()
        pygame.font.init()

        self.headless = headless
        self.screen = (
            pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            if headless
            else pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        )
        if not headless:
            pygame.display.set_caption("Connect Four AI")

        self.clock = pygame.time.Clock()
        self.game = ConnectFourGame()
        self.ai = ConnectFourAI(self.game)
        self.running = True
        self.ai_pending = False
        self.ai_ready_at = 0.0
        self.difficulty_name = "Medium"
        self.status_message = ""

        self.board_x = BOARD_MARGIN
        self.board_y = TOP_SPACE
        self.panel_x = self.board_x + COLS * CELL_SIZE + BOARD_MARGIN
        self.panel_y = BOARD_MARGIN

        self.title_font = pygame.font.SysFont("Trebuchet MS", 38, bold=True)
        self.section_font = pygame.font.SysFont("Segoe UI", 22, bold=True)
        self.text_font = pygame.font.SysFont("Segoe UI", 18)
        self.small_font = pygame.font.SysFont("Segoe UI", 15)
        self.button_font = pygame.font.SysFont("Segoe UI", 20, bold=True)
        self.status_font = pygame.font.SysFont("Trebuchet MS", 28, bold=True)

        self.buttons = self.create_buttons()
        self.sync_status()

    def create_buttons(self) -> list[UIButton]:
        return [
            UIButton(
                "New Game",
                "new_game",
                pygame.Rect(self.panel_x + 24, self.panel_y + 72, 272, 46),
            ),
            UIButton(
                "Easy",
                "difficulty:Easy",
                pygame.Rect(self.panel_x + 24, self.panel_y + 164, 84, 40),
            ),
            UIButton(
                "Medium",
                "difficulty:Medium",
                pygame.Rect(self.panel_x + 118, self.panel_y + 164, 84, 40),
            ),
            UIButton(
                "Hard",
                "difficulty:Hard",
                pygame.Rect(self.panel_x + 212, self.panel_y + 164, 84, 40),
            ),
        ]

    def get_profile(self) -> DifficultyProfile:
        return DIFFICULTY_PROFILES[self.difficulty_name]

    def sync_status(self) -> None:
        if self.game.game_over:
            if self.game.winner == HUMAN:
                self.status_message = "You Win"
            elif self.game.winner == AI:
                self.status_message = "AI Wins"
            else:
                self.status_message = "Draw"
            return

        if self.ai_pending or self.game.current_player == AI:
            self.status_message = "AI Turn"
        else:
            self.status_message = "Your Turn"

    def get_status_color(self) -> tuple[int, int, int]:
        if self.status_message == "You Win":
            return STATUS_WIN
        if self.status_message == "AI Wins":
            return darken(AI_COLOR, 0.15)
        if self.status_message == "Draw":
            return STATUS_DRAW
        if self.status_message == "AI Turn":
            return darken(AI_COLOR, 0.10)
        return darken(HUMAN_COLOR, 0.12)

    def set_difficulty(self, name: str) -> None:
        self.difficulty_name = name

    def new_game(self) -> None:
        self.game.reset()
        self.ai_pending = False
        self.ai_ready_at = 0.0
        self.sync_status()

    def play_move(self, piece: int, col: int, _report: AIReport | None = None) -> None:
        row = self.game.drop_piece(col, piece)
        if row is None:
            return

        if self.game.check_winner(piece):
            self.game.game_over = True
            self.game.winner = piece
            self.ai_pending = False
            self.sync_status()
            return

        if self.game.board_full():
            self.game.game_over = True
            self.game.winner = EMPTY
            self.ai_pending = False
            self.sync_status()
            return

        self.game.current_player = AI if piece == HUMAN else HUMAN
        if self.game.current_player == AI:
            self.ai_pending = True
            self.ai_ready_at = time.perf_counter() + 0.18

        self.sync_status()

    def play_ai_turn(self) -> None:
        if self.game.game_over or self.game.current_player != AI:
            self.ai_pending = False
            self.sync_status()
            return

        chosen_col, report = self.ai.choose_move(self.game.board, self.get_profile())
        self.ai_pending = False

        if chosen_col is None:
            self.game.game_over = True
            self.game.winner = EMPTY
            self.sync_status()
            return

        self.play_move(AI, chosen_col, report)

    def handle_button(self, action: str) -> None:
        if action == "new_game":
            self.new_game()
            return
        if action.startswith("difficulty:"):
            self.set_difficulty(action.split(":", 1)[1])

    def handle_mouse_click(self, pos: tuple[int, int]) -> None:
        for button in self.buttons:
            if button.rect.collidepoint(pos):
                self.handle_button(button.action)
                return

        if self.ai_pending or self.game.game_over or self.game.current_player != HUMAN:
            return

        col = self.get_clicked_column(pos)
        if col is None:
            return

        if not self.game.is_valid_move(col):
            return

        self.play_move(HUMAN, col)

    def handle_keydown(self, key: int) -> None:
        if key == pygame.K_n:
            self.new_game()
        elif key == pygame.K_1:
            self.set_difficulty("Easy")
        elif key == pygame.K_2:
            self.set_difficulty("Medium")
        elif key == pygame.K_3:
            self.set_difficulty("Hard")

    def get_clicked_column(self, pos: tuple[int, int]) -> int | None:
        x, y = pos
        board_width = COLS * CELL_SIZE
        board_height = ROWS * CELL_SIZE

        inside_x = self.board_x <= x < self.board_x + board_width
        inside_y = self.board_y <= y < self.board_y + board_height
        if not (inside_x and inside_y):
            return None

        return (x - self.board_x) // CELL_SIZE

    def draw(self) -> None:
        mouse_pos = (0, 0) if self.headless else pygame.mouse.get_pos()

        self.draw_background()
        self.draw_header(mouse_pos)
        self.draw_board(mouse_pos)
        self.draw_panel(mouse_pos)

    def draw_background(self) -> None:
        self.screen.fill(APP_BG)
        self.draw_alpha_circle((120, 90), 150, BOARD_GLOW, 28)
        self.draw_alpha_circle((self.panel_x + 180, 540), 170, BUTTON_HOVER, 18)
        self.draw_alpha_circle((self.board_x + 300, self.board_y + 180), 240, BOARD_COLOR, 12)

    def draw_header(self, mouse_pos: tuple[int, int]) -> None:
        shadow = self.title_font.render("Connect Four", True, darken(TEXT_COLOR, 0.8))
        title = self.title_font.render("Connect Four", True, TEXT_COLOR)
        self.screen.blit(shadow, (BOARD_MARGIN + 3, 26))
        self.screen.blit(title, (BOARD_MARGIN, 22))

        if (
            not self.game.game_over
            and not self.ai_pending
            and self.game.current_player == HUMAN
            and self.board_x <= mouse_pos[0] < self.board_x + COLS * CELL_SIZE
        ):
            col = (mouse_pos[0] - self.board_x) // CELL_SIZE
            if self.game.is_valid_move(col):
                center_x = self.board_x + col * CELL_SIZE + CELL_SIZE // 2
                self.draw_disc(
                    (center_x, self.board_y - 40),
                    CELL_SIZE // 2 - 14,
                    HUMAN_COLOR,
                )

    def draw_board(self, mouse_pos: tuple[int, int]) -> None:
        board_rect = pygame.Rect(
            self.board_x,
            self.board_y,
            COLS * CELL_SIZE,
            ROWS * CELL_SIZE,
        )
        frame_rect = board_rect.inflate(24, 24)
        self.draw_shadow(frame_rect, 34, offset=(0, 18), alpha=110, expand=12)
        self.draw_alpha_rect(frame_rect.inflate(10, 10), BOARD_GLOW, 32, radius=38)
        pygame.draw.rect(self.screen, BOARD_FRAME, frame_rect, border_radius=34)
        pygame.draw.rect(self.screen, BOARD_COLOR, board_rect.inflate(8, 8), border_radius=28)
        pygame.draw.rect(
            self.screen,
            brighten(BOARD_GLOW, 0.12),
            pygame.Rect(frame_rect.x + 18, frame_rect.y + 12, frame_rect.w - 36, 10),
            border_radius=6,
        )

        hover_col = self.get_hover_column(mouse_pos)
        if hover_col is not None:
            highlight_rect = pygame.Rect(
                self.board_x + hover_col * CELL_SIZE + 10,
                self.board_y + 8,
                CELL_SIZE - 20,
                ROWS * CELL_SIZE - 16,
            )
            self.draw_alpha_rect(highlight_rect, brighten(BOARD_GLOW, 0.2), 26, radius=18)

        winning_cells = set()
        if self.game.game_over and self.game.winner != EMPTY:
            winning_cells = set(self.game.get_winning_line(self.game.winner))

        for row in range(ROWS):
            for col in range(COLS):
                piece = self.game.board[row][col]
                center_x = self.board_x + col * CELL_SIZE + CELL_SIZE // 2
                center_y = self.board_y + row * CELL_SIZE + CELL_SIZE // 2
                center = (center_x, center_y)
                radius = CELL_SIZE // 2 - 12

                if piece == EMPTY:
                    self.draw_slot(center, radius)
                else:
                    color = HUMAN_COLOR if piece == HUMAN else AI_COLOR
                    self.draw_disc(center, radius, color, (row, col) in winning_cells)

    def draw_panel(self, mouse_pos: tuple[int, int]) -> None:
        panel_rect = pygame.Rect(
            self.panel_x,
            self.panel_y,
            PANEL_WIDTH,
            WINDOW_HEIGHT - BOARD_MARGIN * 2,
        )
        self.draw_shadow(panel_rect, 28, offset=(0, 16), alpha=95, expand=10)
        pygame.draw.rect(self.screen, PANEL_BG, panel_rect, border_radius=28)
        pygame.draw.rect(self.screen, OUTLINE_COLOR, panel_rect, width=2, border_radius=28)

        controls_card = pygame.Rect(self.panel_x + 14, self.panel_y + 16, PANEL_WIDTH - 28, 210)
        status_card = pygame.Rect(self.panel_x + 14, self.panel_y + 244, PANEL_WIDTH - 28, 130)
        info_card = pygame.Rect(self.panel_x + 14, self.panel_y + 392, PANEL_WIDTH - 28, 192)

        for card in (controls_card, status_card, info_card):
            self.draw_alpha_rect(card, PANEL_CARD_BG, 255, radius=22)
            pygame.draw.rect(self.screen, OUTLINE_COLOR, card, width=2, border_radius=22)

        self.blit_text("Controls", self.section_font, TEXT_COLOR, controls_card.x + 16, controls_card.y + 14)
        self.blit_text("Difficulty", self.small_font, MUTED_TEXT, controls_card.x + 16, controls_card.y + 116)

        for button in self.buttons:
            active = button.action == f"difficulty:{self.difficulty_name}"
            self.draw_button(button, mouse_pos, active)

        self.blit_text("Game Status", self.section_font, TEXT_COLOR, status_card.x + 16, status_card.y + 14)
        badge_rect = pygame.Rect(status_card.x + 18, status_card.y + 58, status_card.w - 36, 46)
        self.draw_shadow(badge_rect, 18, offset=(0, 8), alpha=70, expand=6)
        pygame.draw.rect(self.screen, self.get_status_color(), badge_rect, border_radius=18)
        pygame.draw.rect(
            self.screen,
            brighten(self.get_status_color(), 0.22),
            pygame.Rect(badge_rect.x + 8, badge_rect.y + 6, badge_rect.w - 16, 8),
            border_radius=4,
        )
        self.blit_text_center(self.status_message, self.status_font, TEXT_COLOR, badge_rect)

        self.blit_text("Players", self.section_font, TEXT_COLOR, info_card.x + 16, info_card.y + 14)
        self.draw_disc((info_card.x + 34, info_card.y + 72), 18, HUMAN_COLOR)
        self.blit_text("You", self.text_font, TEXT_COLOR, info_card.x + 64, info_card.y + 58)
        self.draw_disc((info_card.x + 34, info_card.y + 118), 18, AI_COLOR)
        self.blit_text("AI", self.text_font, TEXT_COLOR, info_card.x + 64, info_card.y + 104)

        hint_rect = pygame.Rect(info_card.x + 16, info_card.y + 148, info_card.w - 32, 30)
        self.draw_alpha_rect(hint_rect, APP_BG, 150, radius=14)
        hint = "Click the board to play"
        self.blit_text_center(hint, self.small_font, MUTED_TEXT, hint_rect)

    def draw_button(
        self, button: UIButton, mouse_pos: tuple[int, int], active: bool = False
    ) -> None:
        hovered = button.rect.collidepoint(mouse_pos)
        base_color = BUTTON_BG
        if active:
            base_color = BUTTON_ACTIVE
        elif hovered:
            base_color = BUTTON_HOVER

        self.draw_shadow(button.rect, 14, offset=(0, 8), alpha=70, expand=6)
        pygame.draw.rect(self.screen, base_color, button.rect, border_radius=14)
        pygame.draw.rect(
            self.screen,
            brighten(base_color, 0.18),
            pygame.Rect(button.rect.x + 8, button.rect.y + 6, button.rect.w - 16, 8),
            border_radius=4,
        )
        pygame.draw.rect(self.screen, OUTLINE_COLOR, button.rect, width=2, border_radius=14)

        label = self.button_font.render(button.label, True, TEXT_COLOR)
        label_rect = label.get_rect(center=button.rect.center)
        self.screen.blit(label, label_rect)

    def get_hover_column(self, mouse_pos: tuple[int, int]) -> int | None:
        if self.game.game_over or self.ai_pending or self.game.current_player != HUMAN:
            return None
        return self.get_clicked_column(mouse_pos)

    def draw_slot(self, center: tuple[int, int], radius: int) -> None:
        shadow_center = (center[0] + 4, center[1] + 7)
        pygame.draw.circle(self.screen, darken(SHADOW_COLOR, 0.1), shadow_center, radius)
        pygame.draw.circle(self.screen, SLOT_COLOR, center, radius)
        pygame.draw.circle(self.screen, brighten(SLOT_RING, 0.1), center, radius, width=3)
        self.draw_alpha_circle((center[0] - 10, center[1] - 12), radius // 2, EMPTY_COLOR, 18)

    def draw_disc(
        self,
        center: tuple[int, int],
        radius: int,
        color: tuple[int, int, int],
        highlighted: bool = False,
    ) -> None:
        shadow_center = (center[0] + 5, center[1] + 8)
        pygame.draw.circle(self.screen, darken(color, 0.78), shadow_center, radius)

        if highlighted:
            self.draw_alpha_circle(center, radius + 10, brighten(color, 0.22), 90)

        pygame.draw.circle(self.screen, darken(color, 0.22), center, radius)
        pygame.draw.circle(self.screen, color, (center[0] - 1, center[1] - 2), radius - 4)
        self.draw_alpha_circle((center[0] - 13, center[1] - 14), max(8, radius // 4), TEXT_COLOR, 55)

    def draw_shadow(
        self,
        rect: "pygame.Rect",
        radius: int,
        offset: tuple[int, int] = (0, 12),
        alpha: int = 70,
        expand: int = 8,
    ) -> None:
        shadow_rect = rect.move(offset[0], offset[1]).inflate(expand * 2, expand * 2)
        self.draw_alpha_rect(shadow_rect, SHADOW_COLOR, alpha, radius + expand)

    def draw_alpha_rect(
        self,
        rect: "pygame.Rect",
        color: tuple[int, int, int],
        alpha: int,
        radius: int = 0,
    ) -> None:
        surface = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        pygame.draw.rect(surface, (*color, alpha), surface.get_rect(), border_radius=radius)
        self.screen.blit(surface, rect.topleft)

    def draw_alpha_circle(
        self,
        center: tuple[int, int],
        radius: int,
        color: tuple[int, int, int],
        alpha: int,
    ) -> None:
        size = radius * 2
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(surface, (*color, alpha), (radius, radius), radius)
        self.screen.blit(surface, (center[0] - radius, center[1] - radius))

    def blit_text(
        self,
        text: str,
        font: "pygame.font.Font",
        color: tuple[int, int, int],
        x: int,
        y: int,
    ) -> None:
        surface = font.render(text, True, color)
        self.screen.blit(surface, (x, y))

    def blit_text_center(
        self,
        text: str,
        font: "pygame.font.Font",
        color: tuple[int, int, int],
        rect: "pygame.Rect",
    ) -> None:
        surface = font.render(text, True, color)
        surface_rect = surface.get_rect(center=rect.center)
        self.screen.blit(surface, surface_rect)

    def tick_ai(self) -> None:
        if not self.ai_pending:
            return

        if time.perf_counter() < self.ai_ready_at:
            return

        self.draw()
        if not self.headless:
            pygame.display.flip()
            pygame.event.pump()
        self.play_ai_turn()

    def run(self) -> None:
        if self.headless:
            self.draw()
            return

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_mouse_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    self.handle_keydown(event.key)

            self.tick_ai()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()


if __name__ == "__main__":
    ConnectFourUI().run()
