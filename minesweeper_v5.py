import pygame
import random
import sys
import os

# 游戏配置

GRID_SIZE = 30
ROWS = 16
COLS = 30

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


def resource_path(relative_path):
    """ 获取打包后文件的绝对路径 """
    if hasattr(sys, '_MEIPASS'):
        # 打包后的临时目录
        base_path = sys._MEIPASS
    else:
        # 开发环境的当前目录
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# 初始化Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))

try:
    # 加载图标文件并创建Surface对象
    icon = pygame.image.load(resource_path("icons/favicon.ico")).convert_alpha()
    # 设置窗口的新图标
    pygame.display.set_icon(icon)
except:
    pass

pygame.display.set_caption("扫雷-自制版")
# font = pygame.font.SysFont("Arial", 20, bold=True)
# 使用系统自带中文字体（Windows/Mac通用方案）
font = pygame.font.SysFont("SimHei", max(int(20*COLS/30), 14))  # 黑体


clock = pygame.time.Clock()



class Cell:
    def __init__(self):
        self.is_mine = False
        self.revealed = False
        self.flagged = False
        self.question_mark = False  # 新增：表示该格子是否被打上了问号
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
        self.board = [[Cell() for _ in range(COLS)] for _ in range(ROWS)]  # 初始化时直接创建空棋盘
        self.game_over = False
        self.victory = False
        self.start_time = 0
        self.elapsed_time = 0
        self.cheat_count = 1  # 新增：作弊次数计数器
        self.first_click = True  # 新增：标记是否为第一次点击

    def create_board(self, first_click_row, first_click_col):
        return create_board_safe_first_click(first_click_row, first_click_col)

    def count_neighbor_mines(self, x, y):
        count = 0
        for i in range(max(0, x - 1), min(ROWS, x + 2)):
            for j in range(max(0, y - 1), min(COLS, y + 2)):
                if self.board[i][j].is_mine:
                    count += 1
        return count


def create_board_safe_first_click(first_click_row, first_click_col):
    """ 确保第一次点击的格子及其周围8个格子都不是雷 """
    board = [[Cell() for _ in range(COLS)] for _ in range(ROWS)]

    # 生成所有可能的地雷位置，排除第一次点击的格子及其周围8个格子
    safe_positions = set()
    for i in range(max(0, first_click_row - 1), min(ROWS, first_click_row + 2)):
        for j in range(max(0, first_click_col - 1), min(COLS, first_click_col + 2)):
            safe_positions.add(i * COLS + j)

    # 从所有可能的位置中排除安全位置
    all_positions = set(range(ROWS * COLS))
    mine_positions = random.sample(list(all_positions - safe_positions), MINES)

    # 布置地雷
    for pos in mine_positions:
        x, y = divmod(pos, COLS)
        board[x][y].is_mine = True

    # 计算相邻雷数
    for i in range(ROWS):
        for j in range(COLS):
            if not board[i][j].is_mine:
                board[i][j].neighbor_mines = count_neighbor_mines(board, i, j)
    return board


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


def show_cheat_confirmation(screen):
    """ 使用pygame实现作弊确认对话框 """
    # 创建半透明背景
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 128))  # 半透明黑色背景
    screen.blit(overlay, (0, 0))

    # 绘制对话框
    dialog_width = 400
    dialog_height = 200
    dialog_x = (WIDTH - dialog_width) // 2
    dialog_y = (HEIGHT - dialog_height) // 2
    pygame.draw.rect(screen, (255, 255, 255), (dialog_x, dialog_y, dialog_width, dialog_height))

    # 绘制提示文字
    text = font.render("确定要使用作弊功能吗？", True, (0, 0, 0))
    text_rect = text.get_rect(center=(WIDTH // 2, dialog_y + 60))
    screen.blit(text, text_rect)

    # 绘制确认按钮
    confirm_button = pygame.Rect(dialog_x + 50, dialog_y + 120, 120, 50)
    pygame.draw.rect(screen, (0, 200, 0), confirm_button)
    confirm_text = font.render("确定", True, (255, 255, 255))
    confirm_text_rect = confirm_text.get_rect(center=confirm_button.center)
    screen.blit(confirm_text, confirm_text_rect)

    # 绘制取消按钮
    cancel_button = pygame.Rect(dialog_x + 230, dialog_y + 120, 120, 50)
    pygame.draw.rect(screen, (200, 0, 0), cancel_button)
    cancel_text = font.render("取消", True, (255, 255, 255))
    cancel_text_rect = cancel_text.get_rect(center=cancel_button.center)
    screen.blit(cancel_text, cancel_text_rect)

    pygame.display.flip()

    # 等待用户点击
    while True:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                if confirm_button.collidepoint(event.pos):
                    return True
                elif cancel_button.collidepoint(event.pos):
                    return False


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

            if cell.revealed or game.game_over or game.victory:  # 修改：游戏结束时显示所有地雷
                pygame.draw.rect(screen, COLORS["revealed"], rect)
                if cell.neighbor_mines > 0 and not cell.is_mine:
                    if cell.flagged:
                        # 实际不为地雷的旗帜格子，显示为打叉
                        pygame.draw.line(screen, (255, 0, 0),
                                         (j * GRID_SIZE + GRID_SIZE // 4, i * GRID_SIZE + GRID_SIZE // 4),
                                         (j * GRID_SIZE + 3 * GRID_SIZE // 4, i * GRID_SIZE + 3 * GRID_SIZE // 4), 3)
                        pygame.draw.line(screen, (255, 0, 0),
                                         (j * GRID_SIZE + GRID_SIZE // 4, i * GRID_SIZE + 3 * GRID_SIZE // 4),
                                         (j * GRID_SIZE + 3 * GRID_SIZE // 4, i * GRID_SIZE + GRID_SIZE // 4), 3)
                    else:
                        color = NUMBER_COLORS[cell.neighbor_mines]
                        text = font.render(str(cell.neighbor_mines), True, color)
                        screen.blit(text, (j * GRID_SIZE + (GRID_SIZE / 2 - 5) - 1, i * GRID_SIZE + (GRID_SIZE / 2 - 10) - 1))
                elif cell.is_mine:
                    if game.game_over or game.victory:
                        if cell.flagged:
                            # 保持旗帜不变
                            pygame.draw.polygon(screen, (255, 0, 0), [
                                (j * GRID_SIZE + GRID_SIZE // 2, i * GRID_SIZE + (GRID_SIZE // 4)),
                                (j * GRID_SIZE + (GRID_SIZE // 2), i * GRID_SIZE + (GRID_SIZE // 1.5)),
                                (j * GRID_SIZE + (GRID_SIZE // 4), i * GRID_SIZE + (GRID_SIZE // 1.5))
                            ])
                        else:
                            # 显示地雷
                            pygame.draw.circle(screen, (0, 0, 0),
                                               (j * GRID_SIZE + (GRID_SIZE / 2) - 1, i * GRID_SIZE + (GRID_SIZE / 2) - 1), 8)
                    else:
                        # 正常显示地雷
                        pygame.draw.circle(screen, (0, 0, 0),
                                           (j * GRID_SIZE + (GRID_SIZE / 2) - 1, i * GRID_SIZE + (GRID_SIZE / 2) - 1), 8)
            else:
                pygame.draw.rect(screen, COLORS["hidden"], rect)
                if cell.flagged:
                    # 保持旗帜不变
                    pygame.draw.polygon(screen, (255, 0, 0), [
                        (j * GRID_SIZE + GRID_SIZE // 2, i * GRID_SIZE + (GRID_SIZE // 4)),
                        (j * GRID_SIZE + (GRID_SIZE // 2), i * GRID_SIZE + (GRID_SIZE // 1.5)),
                        (j * GRID_SIZE + (GRID_SIZE // 4), i * GRID_SIZE + (GRID_SIZE // 1.5))
                    ])
                elif cell.question_mark:
                    # 绘制问号
                    text = font.render("?", True, (0, 0, 0))
                    screen.blit(text, (j * GRID_SIZE + (GRID_SIZE / 2 - 5) - 1, i * GRID_SIZE + (GRID_SIZE / 2 - 10) - 1))

    # 如果按下M键且鼠标悬停在已翻开的格子上，检查周围8格的地雷情况
    keys = pygame.key.get_pressed()
    if keys[pygame.K_m] and 0 <= mouse_row < ROWS and 0 <= mouse_col < COLS and game.cheat_count > 0:
        cell = game.board[mouse_row][mouse_col]
        if cell.revealed:
            # 使用pygame显示作弊确认对话框
            response = show_cheat_confirmation(screen)
            if response:
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
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))  # 修改：将文字显示在屏幕中央
        screen.blit(text, text_rect)
        text = font.render("Press R to restart", True, COLORS["mine_count"])
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))  # 修改：将文字显示在屏幕中央
        screen.blit(text, text_rect)

    # 剩余雷数
    remaining = MINES - sum(cell.flagged for row in game.board for cell in row)
    text = font.render(f"Mines left: {remaining}", True, COLORS["mine_count"])
    text_rect = text.get_rect(topleft=(10, HEIGHT - 40))
    screen.blit(text, text_rect)

    # 游戏时间
    if not game.game_over and not game.victory and (game.first_click is False):  # 游戏未结束时才更新时间
        game.elapsed_time = (pygame.time.get_ticks() - game.start_time) // 1000
    time_text = font.render(f"Time: {game.elapsed_time}s", True, COLORS["timer"])
    text_rect = time_text.get_rect(topright=(WIDTH - 10, HEIGHT - 40))
    screen.blit(time_text, text_rect)

    # 剩余作弊次数（调整位置到左上角）
    cheat_text = font.render(f"Cheats(Press M): {game.cheat_count}", True, COLORS["mine_count"])
    text_rect = cheat_text.get_rect(topleft=(10, HEIGHT - 70))
    screen.blit(cheat_text, text_rect)

    pygame.display.flip()


def show_setting_dialog(screen):
    """ 使用pygame实现设置对话框 """
    # 创建半透明背景
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 128))  # 半透明黑色背景
    screen.blit(overlay, (0, 0))

    # 绘制对话框
    dialog_width = 400
    dialog_height = 300
    dialog_x = (WIDTH - dialog_width) // 2
    dialog_y = (HEIGHT - dialog_height) // 2
    pygame.draw.rect(screen, (255, 255, 255), (dialog_x, dialog_y, dialog_width, dialog_height))

    # 绘制提示文字
    text = font.render("自定义游戏设置", True, (0, 0, 0))
    text_rect = text.get_rect(center=(WIDTH // 2, dialog_y + 30))
    screen.blit(text, text_rect)

    # 绘制行数输入框
    rows_text = font.render("行数 (9-30):", True, (0, 0, 0))
    screen.blit(rows_text, (dialog_x + 50, dialog_y + 70))
    rows_input = pygame.Rect(dialog_x + 200, dialog_y + 70, 100, 30)
    pygame.draw.rect(screen, (200, 200, 200), rows_input)

    # 绘制列数输入框
    cols_text = font.render("列数 (9-30):", True, (0, 0, 0))
    screen.blit(cols_text, (dialog_x + 50, dialog_y + 120))
    cols_input = pygame.Rect(dialog_x + 200, dialog_y + 120, 100, 30)
    pygame.draw.rect(screen, (200, 200, 200), cols_input)

    # 绘制雷数输入框
    mines_text = font.render("雷数 (1-199):", True, (0, 0, 0))
    screen.blit(mines_text, (dialog_x + 50, dialog_y + 170))
    mines_input = pygame.Rect(dialog_x + 200, dialog_y + 170, 100, 30)
    pygame.draw.rect(screen, (200, 200, 200), mines_input)

    # 绘制确认按钮
    confirm_button = pygame.Rect(dialog_x + 50, dialog_y + 230, 120, 50)
    pygame.draw.rect(screen, (0, 200, 0), confirm_button)
    confirm_text = font.render("确定", True, (255, 255, 255))
    confirm_text_rect = confirm_text.get_rect(center=confirm_button.center)
    screen.blit(confirm_text, confirm_text_rect)

    # 绘制取消按钮
    cancel_button = pygame.Rect(dialog_x + 230, dialog_y + 230, 120, 50)
    pygame.draw.rect(screen, (200, 0, 0), cancel_button)
    cancel_text = font.render("取消", True, (255, 255, 255))
    cancel_text_rect = cancel_text.get_rect(center=cancel_button.center)
    screen.blit(cancel_text, cancel_text_rect)

    pygame.display.flip()

    # 输入框内容，设置默认值
    rows_value = "16"
    cols_value = "30"
    mines_value = "99"

    # 光标相关变量
    cursor_visible = True
    cursor_timer = 0
    active_input = None  # 当前激活的输入框

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if confirm_button.collidepoint(event.pos):
                    try:
                        rows = int(rows_value)
                        cols = int(cols_value)
                        mines = int(mines_value)
                        if 9 <= rows <= 30 and 9 <= cols <= 30 and 1 <= mines <= min(rows * cols - 9, 199):
                            return rows, cols, mines
                    except ValueError:
                        pass
                elif cancel_button.collidepoint(event.pos):
                    return None
                # 检测点击输入框
                if rows_input.collidepoint(event.pos):
                    active_input = 'rows'
                elif cols_input.collidepoint(event.pos):
                    active_input = 'cols'
                elif mines_input.collidepoint(event.pos):
                    active_input = 'mines'
                else:
                    active_input = None
            if event.type == pygame.KEYDOWN and active_input:
                if event.key == pygame.K_BACKSPACE:
                    if active_input == 'rows':
                        rows_value = rows_value[:-1]
                    elif active_input == 'cols':
                        cols_value = cols_value[:-1]
                    elif active_input == 'mines':
                        mines_value = mines_value[:-1]
                else:
                    if event.unicode.isdigit():
                        if active_input == 'rows':
                            rows_value += event.unicode
                        elif active_input == 'cols':
                            cols_value += event.unicode
                        elif active_input == 'mines':
                            mines_value += event.unicode

        # 更新输入框内容
        pygame.draw.rect(screen, (200, 200, 200), rows_input)
        rows_text = font.render(rows_value, True, (0, 0, 0))
        screen.blit(rows_text, (rows_input.x + 5, rows_input.y + 5))
        if active_input == 'rows' and cursor_visible:
            cursor_x = rows_input.x + 5 + rows_text.get_width()
            pygame.draw.line(screen, (0, 0, 0), (cursor_x, rows_input.y + 5), (cursor_x, rows_input.y + 25))

        pygame.draw.rect(screen, (200, 200, 200), cols_input)
        cols_text = font.render(cols_value, True, (0, 0, 0))
        screen.blit(cols_text, (cols_input.x + 5, cols_input.y + 5))
        if active_input == 'cols' and cursor_visible:
            cursor_x = cols_input.x + 5 + cols_text.get_width()
            pygame.draw.line(screen, (0, 0, 0), (cursor_x, cols_input.y + 5), (cursor_x, cols_input.y + 25))

        pygame.draw.rect(screen, (200, 200, 200), mines_input)
        mines_text = font.render(mines_value, True, (0, 0, 0))
        screen.blit(mines_text, (mines_input.x + 5, mines_input.y + 5))
        if active_input == 'mines' and cursor_visible:
            cursor_x = mines_input.x + 5 + mines_text.get_width()
            pygame.draw.line(screen, (0, 0, 0), (cursor_x, mines_input.y + 5), (cursor_x, mines_input.y + 25))

        # 光标闪烁效果
        cursor_timer += 1
        if cursor_timer >= 400:
            cursor_visible = not cursor_visible
            cursor_timer = 0

        pygame.display.flip()


def main():
    global ROWS, COLS, MINES, WIDTH, HEIGHT, GRID_SIZE, font, screen

    # 初始化屏幕
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    # 显示设置对话框
    settings = show_setting_dialog(screen)
    if settings is None:
        pygame.quit()
        sys.exit()

    ROWS, COLS, MINES = settings
    WIDTH, HEIGHT = GRID_SIZE * COLS, GRID_SIZE * ROWS + 80

    font = pygame.font.SysFont("SimHei", max(int(20*COLS/30), 14))

    # 重新初始化屏幕
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("扫雷-自制版")

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

                if game.first_click:
                    # 第一次点击时创建棋盘，确保点击的格子及其周围8个格子都不是雷
                    game.start_time = pygame.time.get_ticks()
                    game.board = game.create_board(row, col)
                    game.first_click = False

                cell = game.board[row][col]

                if event.button == 1:  # 左键点击
                    if not cell.flagged and not cell.question_mark:
                        if cell.is_mine:
                            game.game_over = True
                        else:
                            reveal_safe_area(game, row, col)
                            if check_victory(game):
                                game.victory = True
                elif event.button == 3:  # 右键点击
                    if not cell.revealed:
                        if not cell.flagged and not cell.question_mark:
                            cell.flagged = True
                        elif cell.flagged:
                            cell.flagged = False
                            cell.question_mark = True
                        elif cell.question_mark:
                            cell.question_mark = False

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
