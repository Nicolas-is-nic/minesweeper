import pygame
import random
import sys

# 游戏配置

GRID_SIZE = 30
ROWS = 25
COLS = 25

WIDTH, HEIGHT = GRID_SIZE * COLS, GRID_SIZE * ROWS + 80
MINES = 99

COLORS = {
    "bg": (189, 189, 189),
    "grid": (105, 105, 105),
    "hidden": (160, 160, 160),
    "revealed": (215, 215, 215),
    "timer": (0, 0, 255),
    "mine_count": (255, 0, 0)
}

NUMBER_COLORS = {
    1: (0, 125, 10),
    2: (0, 30, 160),
    3: (255, 120, 0),
    4: (128, 128, 0),
    5: (214, 0, 0),
    6: (203, 0, 214),
    7: (7, 0, 120),
    8: (0, 0, 0)
}

# 初始化Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("扫雷-自制版")
font = pygame.font.SysFont("Arial", 20, bold=True)
clock = pygame.time.Clock()


class Cell:
    def __init__(self):
        self.is_mine = False
        self.revealed = False
        self.flagged = False
        self.neighbor_mines = 0


def create_board():
    """ 独立函数：创建新游戏盘 """
    board = [[Cell() for _ in range(COLS)] for _ in range(ROWS)]

    # 布置地雷
    mines_pos = random.sample(range(ROWS * COLS), MINES)
    for pos in mines_pos:
        x, y = divmod(pos, COLS)
        board[x][y].is_mine = True

    # 计算相邻雷数（修复关键错误）
    for i in range(ROWS):
        for j in range(COLS):
            if not board[i][j].is_mine:
                board[i][j].neighbor_mines = count_neighbor_mines(board, i, j)
    return board


def count_neighbor_mines(board, x, y):
    """ 独立函数：计算相邻雷数 """
    count = 0
    for i in range(max(0, x - 1), min(ROWS, x + 2)):
        for j in range(max(0, y - 1), min(COLS, y + 2)):
            if board[i][j].is_mine:
                count += 1
    return count


class GameState:
    def __init__(self):
        self.board = create_board()  # 调用独立函数
        self.game_over = False
        self.victory = False
        self.start_time = pygame.time.get_ticks()
        self.elapsed_time = 0
        self.cheat_count = 1  # 新增：作弊次数计数器

    def create_board(self):
        board = [[Cell() for _ in range(COLS)] for _ in range(ROWS)]

        # 布置地雷
        mines_pos = random.sample(range(ROWS * COLS), MINES)
        for pos in mines_pos:
            x, y = divmod(pos, COLS)
            board[x][y].is_mine = True

        # 计算相邻雷数
        for i in range(ROWS):
            for j in range(COLS):
                if not board[i][j].is_mine:
                    board[i][j].neighbor_mines = self.count_neighbor_mines(i, j)
        return board

    def count_neighbor_mines(self, x, y):
        count = 0
        for i in range(max(0, x - 1), min(ROWS, x + 2)):
            for j in range(max(0, y - 1), min(COLS, y + 2)):
                if self.board[i][j].is_mine:
                    count += 1
        return count


def reveal_safe_area(game, row, col):
    cell = game.board[row][col]
    if cell.revealed or cell.flagged or cell.is_mine:
        return

    cell.revealed = True
    if cell.neighbor_mines == 0:
        for i in range(max(0, row - 1), min(ROWS, row + 2)):
            for j in range(max(0, col - 1), min(COLS, col + 2)):
                if i != row or j != col:
                    reveal_safe_area(game, i, j)


def handle_middle_click(game, row, col):
    cell = game.board[row][col]
    if not cell.revealed or cell.flagged:
        return

    flags_around = 0
    neighbors = []
    for i in range(max(0, row - 1), min(ROWS, row + 2)):
        for j in range(max(0, col - 1), min(COLS, col + 2)):
            if i == row and j == col:
                continue
            neighbors.append((i, j))
            if game.board[i][j].flagged:
                flags_around += 1

    if flags_around == cell.neighbor_mines:
        for i, j in neighbors:
            if 0 <= i < ROWS and 0 <= j < COLS:
                neighbor = game.board[i][j]
                if not neighbor.flagged and not neighbor.revealed:
                    if neighbor.is_mine:
                        game.game_over = True
                    reveal_safe_area(game, i, j)


def check_victory(game):
    safe_unrevealed = sum(1 for row in game.board for cell in row
                          if not cell.is_mine and not cell.revealed)
    return safe_unrevealed == 0


def draw_board(game):
    screen.fill(COLORS["bg"])

    # 获取鼠标位置
    mouse_x, mouse_y = pygame.mouse.get_pos()
    mouse_row = mouse_y // GRID_SIZE
    mouse_col = mouse_x // GRID_SIZE

    # 绘制网格
    for i in range(ROWS):
        for j in range(COLS):
            cell = game.board[i][j]
            rect = pygame.Rect(j * GRID_SIZE, i * GRID_SIZE, GRID_SIZE - 2, GRID_SIZE - 2)

            if cell.revealed:
                pygame.draw.rect(screen, COLORS["revealed"], rect)
                if cell.neighbor_mines > 0 and not cell.is_mine:
                    color = NUMBER_COLORS[cell.neighbor_mines]
                    text = font.render(str(cell.neighbor_mines), True, color)
                    screen.blit(text, (j * GRID_SIZE + (GRID_SIZE / 2 - 5) - 1, i * GRID_SIZE + (GRID_SIZE / 2 - 10) - 1))
                elif cell.is_mine:
                    # 如果鼠标悬停在已翻开的格子上，且该格子是地雷且未被标记，则改变颜色
                    if (i == mouse_row and j == mouse_col) and not cell.flagged:
                        pygame.draw.circle(screen, (255, 182, 193),
                                           (j * GRID_SIZE + (GRID_SIZE / 2) - 1, i * GRID_SIZE + (GRID_SIZE / 2) - 1), 8)
                    else:
                        pygame.draw.circle(screen, (0, 0, 0),
                                           (j * GRID_SIZE + (GRID_SIZE / 2) - 1, i * GRID_SIZE + (GRID_SIZE / 2) - 1), 8)
            else:
                pygame.draw.rect(screen, COLORS["hidden"], rect)
                if cell.flagged:
                    # 绘制红色三角形旗帜
                    pygame.draw.polygon(screen, (255, 0, 0), [
                        (j * GRID_SIZE + GRID_SIZE // 2, i * GRID_SIZE + (GRID_SIZE // 4)),
                        (j * GRID_SIZE + (GRID_SIZE // 2), i * GRID_SIZE + (GRID_SIZE // 1.5)),
                        (j * GRID_SIZE + (GRID_SIZE // 4), i * GRID_SIZE + (GRID_SIZE // 1.5))
                    ])

    # 如果按下M键且鼠标悬停在已翻开的格子上，检查周围8格的地雷情况
    keys = pygame.key.get_pressed()
    if keys[pygame.K_m] and 0 <= mouse_row < ROWS and 0 <= mouse_col < COLS and game.cheat_count > 0:
        cell = game.board[mouse_row][mouse_col]
        if cell.revealed:
            for i in range(max(0, mouse_row - 1), min(ROWS, mouse_row + 2)):
                for j in range(max(0, mouse_col - 1), min(COLS, mouse_col + 2)):
                    if i == mouse_row and j == mouse_col:
                        continue
                    neighbor = game.board[i][j]
                    if neighbor.is_mine and not neighbor.flagged:
                        # 将未标记的地雷格子颜色变为淡红色
                        rect = pygame.Rect(j * GRID_SIZE, i * GRID_SIZE, GRID_SIZE - 2, GRID_SIZE - 2)
                        pygame.draw.rect(screen, (255, 182, 193), rect)
                        neighbor.cheat_highlighted = True  # 标记为作弊高亮
            game.cheat_count -= 1  # 减少作弊次数

    # 绘制被作弊高亮的地雷格子
    for i in range(ROWS):
        for j in range(COLS):
            cell = game.board[i][j]
            if hasattr(cell, 'cheat_highlighted') and cell.cheat_highlighted and cell.is_mine and not cell.flagged:
                rect = pygame.Rect(j * GRID_SIZE, i * GRID_SIZE, GRID_SIZE - 2, GRID_SIZE - 2)
                pygame.draw.rect(screen, (255, 182, 193), rect)

    # 状态显示
    if game.game_over or game.victory:
        status_text = "Game Over!" if game.game_over else "You Win!"
        text = font.render(status_text, True, COLORS["mine_count"])
        screen.blit(text, (WIDTH // 2 - 60, HEIGHT - 70))
        text = font.render("Press R to restart", True, COLORS["mine_count"])
        screen.blit(text, (WIDTH // 2 - 70, HEIGHT - 40))

    # 剩余雷数
    remaining = MINES - sum(cell.flagged for row in game.board for cell in row)
    text = font.render(f"Mines left: {remaining}", True, COLORS["mine_count"])
    screen.blit(text, (10, HEIGHT - 40))

    # 游戏时间
    if not game.game_over and not game.victory:  # 游戏未结束时才更新时间
        game.elapsed_time = (pygame.time.get_ticks() - game.start_time) // 1000
    time_text = font.render(f"Time: {game.elapsed_time}s", True, COLORS["timer"])
    screen.blit(time_text, (WIDTH - 120, HEIGHT - 40))

    # 剩余作弊次数（调整位置到左上角）
    cheat_text = font.render(f"Cheats: {game.cheat_count}", True, COLORS["mine_count"])
    screen.blit(cheat_text, (10, HEIGHT - 70))

    pygame.display.flip()


def main():
    game = GameState()
    running = True

    while running:
        # 游戏时间更新移到draw_board函数中

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and not game.game_over and not game.victory:
                x, y = event.pos
                col = x // GRID_SIZE
                row = y // GRID_SIZE

                if not (0 <= row < ROWS and 0 <= col < COLS):
                    continue

                cell = game.board[row][col]

                if event.button == 1:  # 左键
                    if cell.flagged:
                        continue
                    if cell.is_mine:
                        # 显示所有地雷
                        for r in game.board:
                            for c in r:
                                if c.is_mine:
                                    c.revealed = True
                        game.game_over = True
                    else:
                        reveal_safe_area(game, row, col)

                elif event.button == 3:  # 右键
                    if not cell.revealed:
                        cell.flagged = not cell.flagged

                # 检测左右键同时按下
                if pygame.mouse.get_pressed() == (1, 0, 1):  # 左键和右键同时按下
                    handle_middle_click(game, row, col)

                game.victory = check_victory(game)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # 重置游戏
                    game = GameState()
                elif event.key == pygame.K_SPACE:  # 空格键
                    x, y = pygame.mouse.get_pos()
                    col = x // GRID_SIZE
                    row = y // GRID_SIZE
                    if 0 <= row < ROWS and 0 <= col < COLS:
                        handle_middle_click(game, row, col)

        draw_board(game)
        clock.tick(30)


if __name__ == "__main__":
    main()
