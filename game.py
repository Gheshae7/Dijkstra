
import pygame
import sys
import random
import heapq
import math
import bisect
import time

# دریافت تنظیمات موردنیاز از فایل settings.py
from settings import (
    WIDTH, HEIGHT, FPS,
    COLS, ROWS,
    GRID_COLOR, GRID_LINE_WIDTH,
    BACKGROUND_COLOR,
    FREE, WALL, BLACK, WALL_DENSITY, START_POS, GOAL_POS, START_COLOR, GOAL_COLOR, DIRECTIONS, STEP_COST, CELL_SIZE,
    CURVE_STEPS,
    CORNER_SPEED,
    MAX_SPEED,
    BRAKE,
    ACCEL,
    CAR_SCALE,
CAR_W,
CAR_H,
CELL_SIZE,
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


def cell_center(row, col):
    """
    مرکز یک خانه را بر اساس مختصات سطر و ستون
    به مختصات پیکسلی تبدیل می‌کند.

    row و col می‌توانند عدد اعشاری هم باشند.
    """

    x = col * CELL_SIZE + CELL_SIZE // 2
    y = row * CELL_SIZE + CELL_SIZE // 2

    return (x, y)


def build_curve(path):
    """
    مسیر خانه‌ها را به یک منحنی نرم تبدیل می‌کند.

    در خانه‌هایی که ماشین باید تغییر جهت بدهد،
    به‌جای حرکت مستقیم از یک منحنی استفاده می‌کنیم.

    خروجی:
        points: نقاط مسیر بر حسب پیکسل
        turning: مشخص می‌کند هر نقطه داخل پیچ است یا خیر
        positions: موقعیت هر نقطه در مسیر اصلی
    """

    centers = [cell_center(row, col) for row, col in path]

    points = []
    turning = []
    positions = []

    def add(point, is_turn, position):
        # نقطه‌ی تکراری را دوباره اضافه نکن
        if points and math.hypot(
            point[0] - points[-1][0],
            point[1] - points[-1][1]
        ) < 1e-6:

            turning[-1] = turning[-1] or is_turn
            return

        points.append(point)
        turning.append(is_turn)
        positions.append(position)

    add(centers[0], False, 0)

    for i in range(1, len(centers) - 1):

        prev, cur, nxt = centers[i - 1], centers[i], centers[i + 1]

        # حاصل‌ضرب خارجی صفر یعنی سه نقطه روی یک خط‌اند.
        cross = (
            (cur[0] - prev[0]) * (nxt[1] - cur[1])
            - (cur[1] - prev[1]) * (nxt[0] - cur[0])
        )

        if cross == 0:
            add(cur, False, i)

        else:
            # پیچ: از وسط ضلع قبلی تا وسط ضلع بعدی
            m1 = (
                (prev[0] + cur[0]) / 2,
                (prev[1] + cur[1]) / 2
            )

            m2 = (
                (cur[0] + nxt[0]) / 2,
                (cur[1] + nxt[1]) / 2
            )

            for s in range(CURVE_STEPS + 1):

                t = s / CURVE_STEPS

                x = (
                    (1 - t) ** 2 * m1[0]
                    + 2 * (1 - t) * t * cur[0]
                    + t ** 2 * m2[0]
                )

                y = (
                    (1 - t) ** 2 * m1[1]
                    + 2 * (1 - t) * t * cur[1]
                    + t ** 2 * m2[1]
                )

                add(
                    (x, y),
                    True,
                    i - 0.5 + t
                )

    add(centers[-1], False, len(centers) - 1)

    return points, turning, positions


def build_speed_profile(dists, turning):
    """
    برای هر نقطه‌ی منحنی، سرعت مجاز را محاسبه می‌کند.

    در مسیر مستقیم سرعت بیشتر است.
    در پیچ سرعت کمتر می‌شود.
    ابتدا و انتهای مسیر سرعت صفر است.

    ماشین قبل از رسیدن به پیچ ترمز می‌کند
    و بعد از عبور از پیچ دوباره شتاب می‌گیرد.
    """

    limits = [
        CORNER_SPEED if t else MAX_SPEED
        for t in turning
    ]

    limits[0] = 0.0
    limits[-1] = 0.0

    # حرکت از آخر به اول:
    # محاسبه سرعت مناسب برای ترمز قبل از پیچ
    for k in range(len(limits) - 2, -1, -1):

        seg = dists[k + 1] - dists[k]

        limits[k] = min(
            limits[k],
            math.sqrt(
                limits[k + 1] ** 2 + 2 * BRAKE * seg
            )
        )

    # حرکت از اول به آخر:
    # محدود کردن شتاب برای افزایش تدریجی سرعت
    for k in range(1, len(limits)):

        seg = dists[k] - dists[k - 1]

        limits[k] = min(
            limits[k],
            math.sqrt(
                limits[k - 1] ** 2 + 2 * ACCEL * seg
            )
        )

    return limits


def locate_on_curve(curve, dists, d):
    """
    موقعیت ماشین را روی منحنی پیدا می‌کند.

    d فاصله‌ی طی‌شده از ابتدای منحنی است.

    خروجی:
        x: مختصات افقی
        y: مختصات عمودی
        k: شماره قطعه فعلی منحنی
        frac: میزان پیشرفت در قطعه فعلی
        angle: زاویه حرکت ماشین
    """

    k = bisect.bisect_right(dists, d) - 1

    k = max(0, min(k, len(curve) - 2))

    seg_len = dists[k + 1] - dists[k]

    frac = (
        (d - dists[k]) / seg_len
        if seg_len > 0
        else 0.0
    )

    frac = max(0.0, min(1.0, frac))

    x0, y0 = curve[k]
    x1, y1 = curve[k + 1]

    x = x0 + (x1 - x0) * frac
    y = y0 + (y1 - y0) * frac

    angle = math.degrees(
        math.atan2(-(y1 - y0), x1 - x0)
    ) % 360

    return x, y, k, frac, angle


def shade(color, factor):
    """رنگ را روشن‌تر یا تیره‌تر می‌کند."""
    return tuple(
        max(0, min(255, int(c * factor)))
        for c in color
    )


def make_car_surface(color):
    """تصویر ماشین را از نمای بالا و رو به راست می‌سازد."""

    S = CAR_SCALE
    big = pygame.Surface((CAR_W * S, CAR_H * S), pygame.SRCALPHA)

    def box(col, x, y, w, h, radius):
        """یک مستطیل گرد با مختصات مقیاس اصلی ماشین می‌کشد."""
        pygame.draw.rect(
            big,
            col,
            (int(x * S), int(y * S), int(w * S), int(h * S)),
            border_radius=int(radius * S)
        )

    dark = shade(color, 0.5)

    # چرخ‌ها
    tire = (18, 18, 20)
    for wx in (5, 23):
        box(tire, wx, 0, 9, 5, 2)
        box(tire, wx, 17, 9, 5, 2)
        box((85, 85, 92), wx + 3, 0.7, 3, 1.2, 0.5)
        box((85, 85, 92), wx + 3, 20.1, 3, 1.2, 0.5)

    # آینه‌های بغل
    box(dark, 21.5, 1.4, 3.6, 2.4, 1)
    box(dark, 21.5, 18.2, 3.6, 2.4, 1)

    # بدنه
    box(dark, 0.5, 2.8, 35, 16.4, 7.5)
    box(color, 1.3, 3.6, 33.4, 14.8, 6.8)

    # سایه‌روشن بدنه
    box(shade(color, 1.28), 4, 4.4, 27, 2.6, 1.3)
    box(shade(color, 0.78), 4, 15, 27, 2.2, 1.1)

    # صندوق عقب و کاپوت
    box(shade(color, 1.06), 2.2, 5, 4.5, 12, 2.2)
    box(shade(color, 1.12), 28, 5, 6, 12, 2.5)

    pygame.draw.line(
        big,
        shade(color, 0.7),
        (int(29 * S), int(11 * S)),
        (int(33.5 * S), int(11 * S)),
        max(1, int(0.5 * S))
    )

    # کابین و شیشه‌ها
    box((28, 38, 52), 9.5, 5.2, 19, 11.6, 4)
    box((150, 200, 232), 21, 5.9, 6.2, 10.2, 2.4)
    box((210, 236, 250), 22.2, 6.6, 1.2, 8.8, 0.6)
    box((85, 120, 155), 10.2, 6.1, 4.2, 9.8, 2)
    box(shade(color, 1.08), 14.8, 6, 6.8, 10, 2.2)
    box(shade(color, 1.35), 15.6, 6.8, 5.2, 2.4, 1.2)

    # جلوپنجره و چراغ‌ها
    box((25, 25, 28), 34, 9.6, 1.6, 2.8, 0.6)
    box((255, 248, 180), 33.6, 4.8, 2.2, 3.8, 1)
    box((255, 248, 180), 33.6, 13.4, 2.2, 3.8, 1)
    box((235, 45, 45), 0.3, 4.8, 2, 3.8, 1)
    box((235, 45, 45), 0.3, 13.4, 2, 3.8, 1)

    return pygame.transform.smoothscale(big, (CAR_W, CAR_H))


def make_shadow_surface():
    """سایه‌ی نرم زیر ماشین را می‌سازد."""

    S = CAR_SCALE
    big = pygame.Surface((CAR_W * S, CAR_H * S), pygame.SRCALPHA)

    for inset, alpha in ((0, 26), (1.2, 42), (2.4, 62)):
        rect = (
            int(inset * S),
            int((2 + inset * 0.6) * S),
            int((CAR_W - 2 * inset) * S),
            int((CAR_H - 4 - inset * 1.2) * S)
        )

        pygame.draw.rect(
            big,
            (0, 0, 0, alpha),
            rect,
            border_radius=int(8 * S)
        )

    return pygame.transform.smoothscale(big, (CAR_W, CAR_H))


def make_light_surface():
    """نور چراغ جلوی ماشین را می‌سازد."""

    w, h = 40, 34
    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    for x in range(w):
        half = 3 + (h / 2 - 3) * x / w
        alpha = int(55 * (1 - x / w))

        pygame.draw.line(
            surf,
            (255, 245, 190, alpha),
            (x, int(h / 2 - half)),
            (x, int(h / 2 + half))
        )

    return surf


def make_smoke_frames(count=8):
    """تصاویر مختلف دود اگزوز را می‌سازد."""

    frames = []
    size = 14

    for i in range(count):
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        radius = int(2 + i * 0.6)
        alpha = int(120 * (1 - i / count))

        pygame.draw.circle(
            surf,
            (210, 210, 215, alpha),
            (size // 2, size // 2),
            radius
        )

        frames.append(surf)

    return frames


def make_brake_surface():
    """درخشش قرمز چراغ ترمز را می‌سازد."""

    surf = pygame.Surface((14, 14), pygame.SRCALPHA)

    pygame.draw.circle(surf, (255, 40, 40, 150), (7, 7), 6)
    pygame.draw.circle(surf, (255, 130, 130, 210), (7, 7), 3)

    return surf


def make_overlay_surface(color, alpha):
    """مربع نیمه‌شفاف برای نمایش خانه‌های بررسی‌شده می‌سازد."""

    overlay = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)

    pygame.draw.rect(
        overlay,
        (color[0], color[1], color[2], alpha),
        (2, 2, CELL_SIZE - 4, CELL_SIZE - 4),
        border_radius=8
    )

    return overlay


def make_glow_surface(color):
    """هاله‌ی نیمه‌شفاف زیر مقصد را می‌سازد."""

    glow = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
    c = CELL_SIZE // 2

    pygame.draw.circle(
        glow,
        (color[0], color[1], color[2], 55),
        (c, c),
        c - 2
    )

    return glow


class Car:
    """یک ماشین با شروع، مقصد، رنگ، مسیر و وضعیت حرکت خودش."""

    def __init__(self, start, goal, color):
        self.start = start
        self.goal = goal
        self.color = color

        # تصاویر ماشین و جلوه‌های گرافیکی
        self.image = make_car_surface(color)
        self.shadow = make_shadow_surface()
        self.light = make_light_surface()
        self.smoke_frames = make_smoke_frames()
        self.explore_overlay = make_overlay_surface(color, 80)
        self.explore_bright = make_overlay_surface(color, 190)
        self.goal_glow = make_glow_surface(color)
        self.brake_glow = make_brake_surface()

        # وضعیت عمومی ماشین
        self.position = start
        self.angle = 0
        self.path = []
        self.visited = []
        self.search_progress = 0.0
        self.path_index = 0
        self.t = 0.0
        self.state = "ready"
        self.smoke = []
        self.smoke_timer = 0.0

        # اطلاعات مربوط به حرکت نرم ماشین
        self.pixel = cell_center(*start)
        self.curve = []
        self.dists = []
        self.limits = []
        self.total_length = 0.0
        self.distance = 0.0
        self.seg = 0
        self.speed = 0.0
        self.braking = False
        self.trail = None
        self.route = None
        self.route_alpha = 255
        self.preview_timer = 0.0
        self.search_ms = 0.0

        # اطلاعات مسیرهای مشترک با ماشین‌های دیگر
        self.seg_edges = []
        self.edge_last_seg = {}
        self.shared = []

    def plan(self, graph):
        """مسیر ماشین را پیدا می‌کند و وضعیت آن را برای شروع دوباره آماده می‌کند."""

        t0 = time.perf_counter()

        self.path, self.visited = dijkstra(
            graph,
            self.start,
            self.goal
        )

        self.search_ms = (time.perf_counter() - t0) * 1000

        self.position = self.start
        self.angle = 0
        self.search_progress = 0.0
        self.path_index = 0
        self.t = 0.0
        self.state = "ready"
        self.smoke = []
        self.smoke_timer = 0.0
        self.seg_edges, self.edge_last_seg, self.shared = [], {}, []

        # آماده‌سازی سیستم رانندگی
        self.pixel = cell_center(*self.start)
        self.distance = 0.0
        self.seg = 0
        self.speed = 0.0
        self.braking = False
        self.trail = None
        self.route = None
        self.route_alpha = 255
        self.preview_timer = 0.0

        self.curve, self.dists, self.limits, self.total_length = [], [], [], 0.0

        if len(self.path) >= 2:
            self.curve, turning, positions = build_curve(self.path)

            self.dists = [0.0]

            for k in range(1, len(self.curve)):
                step = math.hypot(
                    self.curve[k][0] - self.curve[k - 1][0],
                    self.curve[k][1] - self.curve[k - 1][1]
                )

                self.dists.append(self.dists[-1] + step)

            self.total_length = self.dists[-1]

            self.limits = build_speed_profile(
                self.dists,
                turning
            )

            # ماشین در ابتدا رو به جهت مسیر قرار می‌گیرد
            self.angle = locate_on_curve(
                self.curve,
                self.dists,
                0.0
            )[4]

            # مشخص می‌کنیم هر تکه از منحنی متعلق به کدام یال مسیر است
            for k in range(len(self.curve) - 1):
                u = (positions[k] + positions[k + 1]) / 2
                e = min(int(u), len(self.path) - 2)

                self.seg_edges.append(
                    tuple(sorted((self.path[e], self.path[e + 1])))
                )

    def begin(self):
        """اگر ماشین آماده باشد، جستجو و حرکت آن را شروع می‌کند."""

        if self.state == "ready":
            self.state = "searching"


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
