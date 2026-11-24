
import pygame
import sys
import random
import heapq

# دریافت تنظیمات موردنیاز از فایل settings.py
from settings import (
    WIDTH, HEIGHT, FPS,
    COLS, ROWS,
    GRID_COLOR, GRID_LINE_WIDTH,
    BACKGROUND_COLOR,
    FREE, WALL, BLACK, WALL_DENSITY, START_POS, GOAL_POS, START_COLOR, GOAL_COLOR, DIRECTIONS, STEP_COST
)


# راه‌اندازی اولیه کتابخانه Pygame
pygame.init()

# ساخت پنجره بازی با عرض و ارتفاع مشخص‌شده در تنظیمات
screen = pygame.display.set_mode((WIDTH, HEIGHT))

# تعیین عنوان پنجره بازی
pygame.display.set_caption("Maze Game")

# ساخت ساعت برای کنترل نرخ اجرای بازی (FPS)
clock = pygame.time.Clock()

# محاسبه عرض هر خانه بر اساس تعداد ستون‌ها
CELL_WIDTH = WIDTH / COLS

# محاسبه ارتفاع هر خانه بر اساس تعداد سطرها
CELL_HEIGHT = HEIGHT / ROWS


def generate_grid():
    """
    ساخت ماتریس محیط بازی و ایجاد دیوارهای تصادفی
    """

    # ساخت ماتریس اولیه با خانه‌های خالی
    grid = [
        [FREE for _ in range(COLS)]
        for _ in range(ROWS)
    ]

    # محاسبه تعداد دیوارهای موردنیاز
    wall_count = int(ROWS * COLS * WALL_DENSITY)

    created_walls = 0

    while created_walls < wall_count:

        # انتخاب تصادفی یک خانه
        row = random.randrange(ROWS)
        col = random.randrange(COLS)

        # بررسی خالی بودن خانه و رزرو نقاط شروع و مقصد
        if (
            grid[row][col] == FREE
            and (row, col) != START_POS
            and (row, col) != GOAL_POS
        ):
            grid[row][col] = WALL
            created_walls += 1

    return grid



def get_neighbors(grid, cell):
    """همسایه‌های آزاد یک خانه را در چهار جهت پیدا می‌کند."""

    row, col = cell
    neighbors = []

    for dr, dc in DIRECTIONS:
        nr, nc = row + dr, col + dc

        # بررسی می‌کنیم خانه داخل محدوده ماز باشد.
        inside = 0 <= nr < len(grid) and 0 <= nc < len(grid[0])

        # فقط خانه‌های آزاد می‌توانند همسایه باشند.
        if inside and grid[nr][nc] != WALL:
            neighbors.append((nr, nc))

    return neighbors


def reconstruct_path(parent, start, goal):
    """مسیر نهایی را از مقصد به شروع بازسازی می‌کند."""

    path = [goal]
    current = goal

    while current != start:
        current = parent[current]
        path.append(current)

    # مسیر را از شروع به مقصد مرتب می‌کنیم.
    path.reverse()

    return path


def build_graph(grid):
    """گراف ماز را از خانه‌های آزاد و همسایه‌های آن‌ها می‌سازد."""

    graph = {}

    for row in range(len(grid)):
        for col in range(len(grid[0])):

            if grid[row][col] != WALL:
                cell = (row, col)

                # هر همسایه همراه با هزینه حرکت ذخیره می‌شود.
                graph[cell] = [
                    (neighbor, STEP_COST)
                    for neighbor in get_neighbors(grid, cell)
                ]

    return graph


def dijkstra(graph, start, goal):
    """کوتاه‌ترین مسیر را با الگوریتم Dijkstra پیدا می‌کند."""

    if start not in graph or goal not in graph:
        return [], []

    dist = {start: 0}
    parent = {}

    visited = set()
    visited_order = []

    # صف اولویت بر اساس کمترین هزینه مسیر
    heap = [(0, start)]

    while heap:
        d, current = heapq.heappop(heap)

        # نادیده گرفتن خانه‌هایی که قبلاً بررسی شده‌اند.
        if current in visited:
            continue

        visited.add(current)
        visited_order.append(current)

        # اگر به مقصد رسیدیم، جستجو تمام می‌شود.
        if current == goal:
            break

        for neighbor, cost in graph[current]:
            new_dist = d + cost

            if new_dist < dist.get(neighbor, float("inf")):
                dist[neighbor] = new_dist
                parent[neighbor] = current

                heapq.heappush(heap, (new_dist, neighbor))

    # اگر مقصد پیدا نشده باشد، مسیر خالی برمی‌گردد.
    if goal not in visited:
        return [], visited_order

    return reconstruct_path(parent, start, goal), visited_order



# تولید محیط بازی و دریافت ماتریس آن
grid = generate_grid()

# ساخت گراف از روی ماز
graph = build_graph(grid)

# اجرای الگوریتم Dijkstra
path, visited_order = dijkstra(graph, START_POS, GOAL_POS)


def draw_grid(screen):
    """
    رسم خطوط عمودی و افقی محیط بازی
    بر اساس تعداد سطرها و ستون‌ها
    """

    # رسم خطوط عمودی شبکه
    for col in range(COLS + 1):
        # محاسبه موقعیت افقی خط
        x = col * CELL_WIDTH

        # رسم خط عمودی
        pygame.draw.line(
            screen,
            GRID_COLOR,
            (x, 0),
            (x, HEIGHT),
            GRID_LINE_WIDTH
        )

    # رسم خطوط افقی شبکه
    for row in range(ROWS + 1):
        # محاسبه موقعیت عمودی خط
        y = row * CELL_HEIGHT

        # رسم خط افقی
        pygame.draw.line(
            screen,
            GRID_COLOR,
            (0, y),
            (WIDTH, y),
            GRID_LINE_WIDTH
        )


def draw_walls(screen, grid):
    """
    رسم خانه‌هایی که مقدار آن‌ها WALL است
    """

    # پیمایش تمام سطرهای ماتریس
    for row in range(ROWS):

        # پیمایش تمام ستون‌های ماتریس
        for col in range(COLS):

            # بررسی اینکه خانه فعلی دیوار است یا خیر
            if grid[row][col] == WALL:

                # محاسبه موقعیت و ابعاد خانه
                x = col * CELL_WIDTH
                y = row * CELL_HEIGHT

                # رسم دیوار به رنگ مشکی
                pygame.draw.rect(
                    screen,
                    BLACK,
                    (x, y, CELL_WIDTH, CELL_HEIGHT)
                )


def draw_positions(screen):
    """
    رسم نقطه شروع و مقصد روی محیط بازی
    """

    # رسم نقطه شروع
    start_row, start_col = START_POS

    pygame.draw.rect(
        screen,
        START_COLOR,
        (
            start_col * CELL_WIDTH,
            start_row * CELL_HEIGHT,
            CELL_WIDTH,
            CELL_HEIGHT
        )
    )

    # رسم نقطه مقصد
    goal_row, goal_col = GOAL_POS

    pygame.draw.rect(
        screen,
        GOAL_COLOR,
        (
            goal_col * CELL_WIDTH,
            goal_row * CELL_HEIGHT,
            CELL_WIDTH,
            CELL_HEIGHT
        )
    )


# متغیری برای کنترل اجرای حلقه اصلی بازی
running = True

# حلقه اصلی بازی؛ تا زمانی که running برابر True باشد ادامه دارد
while running:

    # بررسی رویدادهای اتفاق‌افتاده، مثل کلیک روی دکمه بستن پنجره
    for event in pygame.event.get():

        # اگر کاربر پنجره را ببندد، حلقه بازی متوقف می‌شود
        if event.type == pygame.QUIT:
            running = False

    # پاک کردن صفحه
    screen.fill(BACKGROUND_COLOR)

    # رسم دیوارها
    draw_walls(screen, grid)

    # رسم نقطه شروع و مقصد
    draw_positions(screen)

    # رسم خطوط شبکه
    draw_grid(screen)

    # به‌روزرسانی صفحه نمایش و نمایش تصویر جدید
    pygame.display.flip()

    # محدود کردن سرعت اجرای حلقه بازی بر اساس مقدار FPS
    clock.tick(FPS)


# خروج صحیح از Pygame پس از پایان حلقه اصلی
pygame.quit()

# پایان دادن به اجرای برنامه پایتون
sys.exit()
