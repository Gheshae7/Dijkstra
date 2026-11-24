
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
    SEARCH_SPEED,
PREVIEW_TIME,
TURN_SPEED,
MIN_SPEED,
SMOKE_LIFE,
AHEAD_ALPHA, WHITE, BUILDING_KINDS,
GARDEN_ROOF,
ROOF_COLORS,
WALL_COLORS,
FACADE_H,
ASPHALT,
ASPHALT_LIGHT,
ASPHALT_DARK,
ASPHALT_EDGE,
SIDEWALK,
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


def create_grid(rows, cols):
    """یک شبکه‌ی خالی می‌سازد که همه‌ی خانه‌هایش آزاد است."""
    grid = []
    for row in range(rows):
        grid.append([FREE] * cols)
    return grid


def add_wall(grid, row, col):
    """یک دیوار در خانه‌ی مشخص‌شده قرار می‌دهد، اگر مختصات داخل ماز باشد."""
    if 0 <= row < len(grid) and 0 <= col < len(grid[0]):
        grid[row][col] = WALL


def add_random_walls(grid, density, protected):
    """به‌صورت تصادفی دیوار می‌گذارد، به‌جز خانه‌های موجود در protected."""
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if (row, col) in protected:
                continue
            if random.random() < density:
                add_wall(grid, row, col)


def is_wall(grid, row, col):
    """اگر مختصات داخل ماز و خانه دیوار باشد True برمی‌گرداند؛ خارج ماز False است."""
    if 0 <= row < len(grid) and 0 <= col < len(grid[0]):
        return grid[row][col] == WALL
    return False


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


def update_car(car, dt):
    """وضعیت ماشین را برای یک فریم جلو می‌برد (dt زمان فریم به میلی‌ثانیه است)."""
    seconds = dt / 1000

    if car.state == "searching":
        # جستجو را کم‌کم نمایش بده
        car.search_progress += SEARCH_SPEED * seconds
        if car.search_progress >= len(car.visited):
            car.search_progress = len(car.visited)
            if not car.path:
                car.state = "no_path"
            elif len(car.path) < 2:
                car.state = "arrived"
            else:
                car.state = "preview"
                car.preview_timer = 0.0
                car.route_alpha = 255

    elif car.state == "preview":
        # مسیر کامل از مبدا تا مقصد نمایش داده می‌شود
        car.preview_timer += seconds
        if car.preview_timer >= PREVIEW_TIME:
            car.state = "moving"

    elif car.state == "moving":
        # مسیر جلوی ماشین کم‌کم کم‌رنگ می‌شود
        car.route_alpha = max(AHEAD_ALPHA, car.route_alpha - 400 * seconds)

        # سرعت مجاز در نقطه‌ی فعلی
        _, _, k, frac, _ = locate_on_curve(
            car.curve, car.dists, car.distance
        )
        allowed = car.limits[k] + (
            car.limits[k + 1] - car.limits[k]
        ) * frac

        new_speed = max(allowed, MIN_SPEED)
        car.braking = new_speed < car.speed - 0.5
        car.speed = new_speed

        # جلو رفتن به اندازه‌ی سرعت × زمان
        car.distance += car.speed * seconds

        if car.distance >= car.total_length:
            # به مقصد رسیدیم
            car.distance = car.total_length
            car.state = "arrived"
            car.speed = 0.0
            car.braking = False
            car.position = car.path[-1]
            car.pixel = cell_center(*car.path[-1])
            car.seg = len(car.curve) - 2

        else:
            x, y, car.seg, _, target = locate_on_curve(
                car.curve, car.dists, car.distance
            )
            car.pixel = (x, y)

            # تبدیل پیکسل به (سطر، ستون) اعشاری
            car.position = (
                (y - CELL_SIZE // 2) / CELL_SIZE,
                (x - CELL_SIZE // 2) / CELL_SIZE
            )

            # چرخش نرم بدنه به سمت جهت منحنی
            diff = (target - car.angle + 180) % 360 - 180
            step = TURN_SPEED * seconds
            car.angle = (
                car.angle + max(-step, min(step, diff))
            ) % 360

    # دود اگزوز: هنگام حرکت، هر 0.05 ثانیه یک ذره ایجاد می‌شود
    if car.state == "moving":
        car.smoke_timer += seconds

        if car.smoke_timer >= 0.05:
            car.smoke_timer = 0.0
            cx, cy = cell_center(*car.position)
            rad = math.radians(car.angle)

            car.smoke.append([
                cx - math.cos(rad) * 18,
                cy + math.sin(rad) * 18,
                0.0
            ])

    # پیر کردن ذرات دود و حذف ذرات قدیمی
    for particle in car.smoke:
        particle[2] += seconds

    car.smoke = [
        p for p in car.smoke
        if p[2] < SMOKE_LIFE
    ]


def compute_sharing(cars):
    """
    پیدا می‌کند کدام تکه‌های مسیر بین چند ماشین مشترک است.
    «یال» یعنی جفت خانه‌ی پشت سر هم؛ اگر دو ماشین از یک یال بروند، مسیرشان یکی شده.
    تعداد یال‌های مشترک را برمی‌گرداند.
    """
    users = {}  # یال -> شماره‌ی ماشین‌هایی که از آن می‌روند

    for index, car in enumerate(cars):
        car.edge_last_seg = {}

        for k, edge in enumerate(car.seg_edges):
            car.edge_last_seg[edge] = k

        for edge in set(car.seg_edges):
            users.setdefault(edge, []).append(index)

    for car in cars:
        car.shared = [
            users[e] if len(users[e]) > 1 else None
            for e in car.seg_edges
        ]

    return sum(1 for u in users.values() if len(u) > 1)


def plan_all(cars, graph):
    """برای همه‌ی ماشین‌ها Dijkstra اجرا می‌کند و مسیرهای مشترک را پیدا می‌کند."""
    for car in cars:
        car.plan(graph)

    return compute_sharing(cars)


def route_visible(car):
    """آیا مسیر این ماشین الان روی صفحه نمایش داده می‌شود؟"""
    return car.state in ("preview", "moving", "arrived")


def segment_shown(car, k):
    """آیا تکه‌ی k از مسیر این ماشین باید دیده شود؟"""
    if not route_visible(car):
        return False

    return (
        AHEAD_ALPHA > 0
        or car.state in ("preview", "arrived")
        or k < car.seg
    )


# ======================================================================
#                 کشیدن جستجو، مسیر و مسیرهای مشترک
# ======================================================================

def draw_search(screen, car):
    """خانه‌های بررسی‌شده را نشان می‌دهد؛ ۶ خانه‌ی آخر (لبه‌ی موج) پررنگ‌ترند."""
    count = int(car.search_progress)

    for i, (row, col) in enumerate(car.visited[:count]):
        overlay = car.explore_bright if i >= count - 6 else car.explore_overlay
        screen.blit(overlay, (col * CELL_SIZE, row * CELL_SIZE))


def route_bounds(curve, pad=14):
    """مستطیلی که کل مسیر در آن جا می‌شود: (چپ، بالا، عرض، ارتفاع)."""
    left = int(min(p[0] for p in curve)) - pad
    top = int(min(p[1] for p in curve)) - pad
    width = int(max(p[0] for p in curve)) + pad - left
    height = int(max(p[1] for p in curve)) + pad - top

    return left, top, width, height


def draw_route_layers(surface, points, color):
    """یک خط مسیر را با سه لایه می‌کشد: هاله‌ی نرم، لبه‌ی تیره و خط اصلی هم‌رنگ ماشین."""
    r, g, b = color
    outline = shade(color, 0.45)

    # 1) هاله‌ی نرم دور مسیر
    for point in points:
        pygame.draw.circle(surface, (r, g, b, 70), point, 8)

    pygame.draw.lines(surface, (r, g, b, 70), False, points, 16)

    # 2) لبه‌ی تیره
    pygame.draw.lines(surface, outline, False, points, 8)

    for point in points:
        pygame.draw.circle(surface, outline, point, 4)

    # 3) خط اصلی با رنگ ماشین
    pygame.draw.lines(surface, color, False, points, 4)

    for point in points:
        pygame.draw.circle(surface, color, point, 3)


def draw_trail(screen, car):
    """
    مسیر ماشین را می‌کشد:
    1) بعد از پایان جستجو (حالت preview) کل مسیر از مبدا تا مقصد یکجا و پررنگ نمایش داده می‌شود.
    2) وقتی ماشین راه می‌افتد، مسیر جلوی ماشین کم‌رنگ می‌شود (AHEAD_ALPHA)
       و بخش طی‌شده پشت ماشین پررنگ می‌ماند.
    """
    if not route_visible(car) or len(car.curve) < 2:
        return

    # تصویرها را یک بار به اندازه‌ی کل مسیر می‌سازیم
    if car.route is None:
        left, top, width, height = route_bounds(car.curve)

        full = pygame.Surface((width, height), pygame.SRCALPHA)

        draw_route_layers(
            full,
            [(int(px) - left, int(py) - top) for px, py in car.curve],
            car.color
        )

        car.route = (full, (left, top))
        # مسیر کامل (یک بار کشیده می‌شود)

        car.trail = (
            pygame.Surface((width, height), pygame.SRCALPHA),
            (left, top)
        )
        # بخش طی‌شده

    full, (left, top) = car.route

    full.set_alpha(int(car.route_alpha))
    # پررنگ در preview، کم‌رنگ جلوی ماشین هنگام حرکت

    screen.blit(full, (left, top))

    # بخش طی‌شده: از ابتدا تا جای فعلی ماشین، پررنگ و روی مسیر کامل
    if car.state in ("moving", "arrived"):
        trail_surface = car.trail[0]

        points = car.curve[:car.seg + 1] + [car.pixel]

        if len(points) >= 2:
            trail_surface.fill((0, 0, 0, 0))
            # پاک کردن فریم قبل

            local = [
                (int(px) - left, int(py) - top)
                for px, py in points
            ]

            draw_route_layers(trail_surface, local, car.color)

            screen.blit(trail_surface, (left, top))


MERGE_DASH = 8
# طول هر تکه‌ی رنگی در خط‌چین مسیر مشترک (پیکسل)


def draw_node(screen, point):
    """یک گره‌ی گرد سفید می‌کشد (برای نشان دادن جایی که مسیرها یکی یا جدا می‌شوند)."""
    p = (int(point[0]), int(point[1]))

    pygame.draw.circle(screen, WHITE, p, 7)
    pygame.draw.circle(screen, (22, 25, 36), p, 5)
    pygame.draw.circle(screen, WHITE, p, 2)


def draw_merged_routes(screen, cars):
    """
    جایی که مسیر چند ماشین یکی شده را با خط‌چینِ چندرنگ نشان می‌دهد:
    رنگ‌ها به نوبت (قرمز، آبی، قرمز، آبی ...) عوض می‌شوند و ابتدا و انتهای بخش مشترک
    یک گره‌ی سفید دارد. این خط‌چین برای بخش‌هایی کشیده می‌شود که مسیرِ حداقل دو ماشین
    (بعد از پایان جستجو) از آن می‌گذرد.
    """
    for i, car in enumerate(cars):
        if len(car.curve) < 2 or not car.shared:
            continue

        # برای هر تکه‌ی منحنی: رنگ‌های ماشین‌هایی که از آن گذشته‌اند (یا None).
        # هر بخش مشترک فقط یک بار کشیده می‌شود: توسط ماشینی که شماره‌اش کمتر است.
        merged = []

        for k, users in enumerate(car.shared):
            colors = None

            if users is not None and users[0] == i and segment_shown(car, k):
                covered = [
                    j for j in users
                    if route_visible(cars[j])
                ]

                if len(covered) >= 2:
                    colors = [cars[j].color for j in covered]

            merged.append(colors)

        # 1) لبه‌ی تیره زیر خط‌چین
        for k, colors in enumerate(merged):
            if colors:
                a, b = car.curve[k], car.curve[k + 1]

                pygame.draw.line(screen, (22, 25, 36), a, b, 9)
                pygame.draw.circle(
                    screen,
                    (22, 25, 36),
                    (int(b[0]), int(b[1])),
                    4
                )

        # 2) خط‌چین رنگی
        # هر تکه را به قطعه‌های ۳ پیکسلی می‌شکنیم و رنگ را از روی مسافت انتخاب می‌کنیم
        for k, colors in enumerate(merged):
            if not colors:
                continue

            ax, ay = car.curve[k]
            bx, by = car.curve[k + 1]

            length = car.dists[k + 1] - car.dists[k]
            pieces = max(1, int(math.ceil(length / 3)))

            for p in range(pieces):
                t0, t1 = p / pieces, (p + 1) / pieces

                d_mid = car.dists[k] + length * (t0 + t1) / 2

                color = colors[int(d_mid // MERGE_DASH) % len(colors)]

                start = (
                    ax + (bx - ax) * t0,
                    ay + (by - ay) * t0
                )

                end = (
                    ax + (bx - ax) * t1,
                    ay + (by - ay) * t1
                )

                pygame.draw.line(screen, color, start, end, 5)

        # 3) گره‌ی سفید در ابتدا و انتهای هر بخش مشترک
        for k, colors in enumerate(merged):
            if not colors:
                continue

            if k == 0 or not merged[k - 1]:
                draw_node(screen, car.curve[k])

            if k == len(merged) - 1 or not merged[k + 1]:
                draw_node(screen, car.curve[k + 1])


# وضعیت‌هایی که نشان می‌دهند ماشین هنوز مشغول انجام کار است
BUSY_STATES = ("searching", "preview", "moving")


def is_idle(cars):
    """آیا همه‌ی ماشین‌ها ایستاده‌اند؟ (آماده یا تمام‌شده)"""
    return not any(car.state in BUSY_STATES for car in cars)


def draw_start_prompt(screen, fonts, cars, bottom):
    """تا وقتی ماشین‌ها آماده‌ی شروع‌اند، پیام شروع را بالای y=bottom نشان می‌دهد."""
    if not all(car.state == "ready" for car in cars):
        return

    pulse = (math.sin(pygame.time.get_ticks() / 300) + 1) / 2
    label = fonts["big"].render("Press SPACE to start", True, WHITE)
    w, h = label.get_width() + 40, label.get_height() + 18
    x, y = (WIDTH - w) // 2, bottom - h

    panel = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (14, 17, 26, 215), (0, 0, w, h), border_radius=h // 2)
    pygame.draw.rect(
        panel,
        (80, int(120 + 120 * pulse), 120, 255),
        (0, 0, w, h),
        2,
        border_radius=h // 2
    )

    screen.blit(panel, (x, y))
    screen.blit(label, (x + 20, y + 9))


def draw_toast(screen, fonts, text):
    """یک پیام کوتاه را وسط صفحه و بالای نوار راهنما نشان می‌دهد."""
    label = fonts["body"].render(text, True, WHITE)
    w, h = label.get_width() + 28, label.get_height() + 14
    x, y = (WIDTH - w) // 2, HEIGHT - 175

    panel = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (14, 17, 26, 230), (0, 0, w, h), border_radius=h // 2)
    pygame.draw.rect(panel, (255, 255, 255, 60), (0, 0, w, h), 1, border_radius=h // 2)

    screen.blit(panel, (x, y))
    screen.blit(label, (x + 14, y + 7))
    
    
def draw_start(screen, row, col, color, selected=False):
    """محل شروع را مثل یک جای پارک با کادر رنگی نشان می‌دهد."""
    cx, cy = cell_center(row, col)

    slot = pygame.Rect(0, 0, CELL_SIZE - 6, CELL_SIZE - 10)
    slot.center = (cx, cy)

    pygame.draw.rect(screen, color, slot, 2, border_radius=6)

    if selected:
        pygame.draw.rect(
            screen,
            WHITE,
            (slot.x - 3, slot.y - 3, slot.w + 6, slot.h + 6),
            1,
            border_radius=9
        )


def draw_goal(screen, car):
    """مقصد را با هاله، حلقه‌ی ضربان‌دار و پرچم شطرنجی نمایش می‌دهد."""
    cx, cy = cell_center(*car.goal)

    # هاله‌ی نرم زیر مقصد
    screen.blit(car.goal_glow, car.goal_glow.get_rect(center=(cx, cy)))

    # حلقه‌ای که با گذشت زمان کوچک و بزرگ می‌شود
    pulse = (math.sin(pygame.time.get_ticks() / 250) + 1) / 2
    radius = CELL_SIZE // 2 - 6 + int(pulse * 4)

    pygame.draw.circle(screen, car.color, (cx, cy), radius, 3)

    # میله‌ی پرچم
    pole_x = cx - 6
    pole_top = cy - 11

    pygame.draw.line(
        screen,
        (235, 235, 235),
        (pole_x, pole_top),
        (pole_x, cy + 11),
        2
    )

    # پرچم شطرنجی
    for i in range(3):
        for j in range(2):
            color = (250, 250, 250) if (i + j) % 2 == 0 else (30, 30, 30)

            pygame.draw.rect(
                screen,
                color,
                (pole_x + 1 + i * 5, pole_top + j * 5, 5, 5)
            )


def draw_cars(screen, cars, selected=None):
    """مقصد، محل شروع، دود، نور چراغ، سایه و خود ماشین‌ها را رسم می‌کند."""

    for index, car in enumerate(cars):

        # نمایش مقصد و محل شروع
        draw_goal(screen, car)

        draw_start(
            screen,
            car.start[0],
            car.start[1],
            car.color,
            selected == index and car.state == "ready" and len(cars) > 1
        )

        # رسم ذرات دود اگزوز
        for x, y, age in car.smoke:
            index = min(
                int(age / SMOKE_LIFE * len(car.smoke_frames)),
                len(car.smoke_frames) - 1
            )

            frame = car.smoke_frames[index]
            screen.blit(frame, frame.get_rect(center=(int(x), int(y))))

        px, py = cell_center(*car.position)
        px, py = int(px), int(py)

        # نور چراغ جلو؛ فقط هنگام حرکت
        if car.state == "moving":
            rad = math.radians(car.angle)

            dist = CAR_W // 2 + car.light.get_width() // 2 - 4

            lx = px + math.cos(rad) * dist
            ly = py - math.sin(rad) * dist

            light = pygame.transform.rotozoom(car.light, car.angle, 1.0)

            screen.blit(
                light,
                light.get_rect(center=(int(lx), int(ly)))
            )

        # چرخاندن تصویر ماشین و سایه بر اساس زاویه
        image = pygame.transform.rotozoom(car.image, car.angle, 1.0)
        shadow = pygame.transform.rotozoom(car.shadow, car.angle, 1.0)

        # ابتدا سایه و سپس خود ماشین
        screen.blit(shadow, shadow.get_rect(center=(px + 3, py + 4)))
        screen.blit(image, image.get_rect(center=(px, py)))

        # چراغ ترمز هنگام کاهش سرعت
        if car.braking and car.state == "moving":
            rad = math.radians(car.angle)

            rear_x = px - math.cos(rad) * 17
            rear_y = py + math.sin(rad) * 17

            for side in (-7, 7):
                bx = rear_x + math.sin(rad) * side
                by = rear_y + math.cos(rad) * side

                screen.blit(
                    car.brake_glow,
                    car.brake_glow.get_rect(center=(int(bx), int(by)))
                )


def make_building_style(block_id):
    """رنگ سقف، رنگ دیوار و نوع سقفِ یک ساختمان را انتخاب می‌کند."""
    rng = random.Random(block_id * 7919 + 17)
    kind = rng.choice(BUILDING_KINDS)

    roof = GARDEN_ROOF if kind == "garden" else rng.choice(ROOF_COLORS)
    wall = rng.choice(WALL_COLORS)

    return {"kind": kind, "roof": roof, "wall": wall}


def find_buildings(grid):
    """
    ساختمان‌ها را پیدا می‌کند:
    هر دسته دیوارِ چسبیده به هم یک ساختمان است.

    خروجی:
    block_of: مشخص می‌کند هر خانه متعلق به کدام ساختمان است.
    styles: ظاهر هر ساختمان را نگهداری می‌کند.
    """
    block_of = {}
    styles = []

    for row in range(len(grid)):
        for col in range(len(grid[0])):

            if grid[row][col] != WALL or (row, col) in block_of:
                continue

            block_id = len(styles)
            block_of[(row, col)] = block_id
            stack = [(row, col)]

            while stack:
                r, c = stack.pop()

                for dr, dc in DIRECTIONS:
                    nr, nc = r + dr, c + dc

                    if is_wall(grid, nr, nc) and (nr, nc) not in block_of:
                        block_of[(nr, nc)] = block_id
                        stack.append((nr, nc))

            styles.append(make_building_style(block_id))

    return block_of, styles


def draw_roof_feature(surf, kind, x, y, roof_h, row, col):
    """وسایل روی سقف را می‌کشد: کولر، پنل خورشیدی، باغچه یا مخزن آب."""
    cx, cy = x + CELL_SIZE // 2, y + roof_h // 2

    if kind == "ac":
        pick = (row * 3 + col * 5) % 3

        if pick == 0:
            # کولر با پنکه
            unit = pygame.Rect(0, 0, 14, 14)
            unit.center = (cx, cy)

            pygame.draw.rect(surf, (178, 178, 184), unit, border_radius=2)
            pygame.draw.rect(surf, (90, 90, 96), unit, 1, border_radius=2)
            pygame.draw.circle(surf, (70, 70, 76), (cx, cy), 5)
            pygame.draw.circle(surf, (125, 125, 132), (cx, cy), 2)

        elif pick == 1:
            # نورگیر
            sky = pygame.Rect(0, 0, 16, 10)
            sky.center = (cx, cy)

            pygame.draw.rect(surf, (150, 205, 235), sky, border_radius=2)
            pygame.draw.line(surf, (235, 245, 250), sky.midtop, sky.midbottom, 1)
            pygame.draw.rect(surf, (90, 130, 160), sky, 1, border_radius=2)

    elif kind == "solar":
        # دو پنل خورشیدی کنار هم
        panel_h = roof_h - 14

        for px in (x + 5, x + 22):
            panel = pygame.Rect(px, y + 7, 13, panel_h)

            pygame.draw.rect(surf, (38, 62, 112), panel)
            pygame.draw.line(surf, (110, 140, 190), panel.midtop, panel.midbottom, 1)
            pygame.draw.line(
                surf,
                (110, 140, 190),
                (panel.left, panel.centery),
                (panel.right, panel.centery),
                1
            )
            pygame.draw.rect(surf, (205, 212, 225), panel, 1)

    elif kind == "garden":
        # دو درخت روی بام سبز
        for tx, ty in ((x + 12, cy), (x + 28, cy - 1)):
            pygame.draw.circle(surf, (56, 112, 64), (tx, ty), 7)
            pygame.draw.circle(surf, (92, 156, 92), (tx - 1, ty - 1), 4)

    elif kind == "tank":
        # مخزن آب گرد
        pygame.draw.circle(surf, (120, 120, 126), (cx, cy), 9)
        pygame.draw.circle(surf, (175, 175, 182), (cx, cy), 7)
        pygame.draw.circle(surf, (205, 205, 212), (cx - 2, cy - 2), 3)


def draw_building(surf, grid, block_of, styles, row, col, x, y):
    """
    یک خانه از ساختمان را می‌کشد.
    خانه‌های چسبیده یک سقف پیوسته دارند و فقط لبه‌ی بیرونی ساختمان خط می‌خورد.
    """
    style = styles[block_of[(row, col)]]

    roof = style["roof"]
    wall = style["wall"]
    kind = style["kind"]

    rng = random.Random(row * 1000 + col)

    # اگر خانه‌ی پایینی دیوار نباشد، جلوی ساختمان دیده می‌شود
    has_front = not is_wall(grid, row + 1, col)
    roof_h = CELL_SIZE - FACADE_H if has_front else CELL_SIZE

    # سقف با لکه‌های ریز
    pygame.draw.rect(surf, roof, (x, y, CELL_SIZE, roof_h))

    for _ in range(14):
        px = x + rng.randrange(CELL_SIZE - 1)
        py = y + rng.randrange(roof_h - 1)

        pygame.draw.rect(
            surf,
            shade(roof, rng.choice([0.92, 1.08])),
            (px, py, 2, 2)
        )

    # لبه‌ی سقف
    dark = shade(roof, 0.5)
    light = shade(roof, 1.25)

    if not is_wall(grid, row - 1, col):
        pygame.draw.rect(surf, dark, (x, y, CELL_SIZE, 2))
        pygame.draw.rect(surf, light, (x, y + 2, CELL_SIZE, 2))

    if not is_wall(grid, row, col - 1):
        pygame.draw.rect(surf, dark, (x, y, 2, roof_h))
        pygame.draw.rect(surf, light, (x + 2, y, 2, roof_h))

    if not is_wall(grid, row, col + 1):
        pygame.draw.rect(
            surf,
            dark,
            (x + CELL_SIZE - 2, y, 2, roof_h)
        )
        pygame.draw.rect(
            surf,
            light,
            (x + CELL_SIZE - 4, y, 2, roof_h)
        )

    # وسایل روی سقف
    draw_roof_feature(surf, kind, x, y, roof_h, row, col)

    # دیوار جلوی ساختمان
    if has_front:
        fy = y + roof_h

        pygame.draw.rect(surf, shade(roof, 0.7), (x, fy - 3, CELL_SIZE, 3))
        pygame.draw.rect(surf, wall, (x, fy, CELL_SIZE, FACADE_H))
        pygame.draw.rect(surf, shade(wall, 0.72), (x, fy, CELL_SIZE, 3))
        pygame.draw.rect(
            surf,
            shade(wall, 0.55),
            (x, y + CELL_SIZE - 1, CELL_SIZE, 1)
        )

        if not is_wall(grid, row, col - 1):
            pygame.draw.rect(
                surf,
                shade(wall, 0.7),
                (x, fy, 2, FACADE_H)
            )

        if not is_wall(grid, row, col + 1):
            pygame.draw.rect(
                surf,
                shade(wall, 0.7),
                (x + CELL_SIZE - 2, fy, 2, FACADE_H)
            )

        # بعضی خانه‌ها در دارند و بعضی سه پنجره
        if (row * 5 + col * 3) % 3 == 0:
            xs = [x + 4, x + 29]

            pygame.draw.rect(
                surf,
                (110, 72, 45),
                (x + 16, fy + 4, 8, FACADE_H - 5),
                border_radius=2
            )

            pygame.draw.circle(
                surf,
                (235, 205, 95),
                (x + 22, fy + 9),
                1
            )

        else:
            xs = [x + 5, x + 17, x + 29]

        for wx in xs:
            lit = rng.random() < 0.4
            glass = (255, 222, 135) if lit else (70, 90, 115)

            pygame.draw.rect(
                surf,
                shade(wall, 0.55),
                (wx, fy + 4, 7, 7),
                border_radius=2
            )

            pygame.draw.rect(
                surf,
                glass,
                (wx + 1, fy + 5, 5, 5)
            )


def draw_road(surf, grid, row, col, x, y, rng):
    """یک خانه‌ی جاده‌ی آسفالتی با بافت، ترک، پیاده‌رو و سایه‌ی ساختمان می‌کشد."""
    pygame.draw.rect(surf, ASPHALT, (x, y, CELL_SIZE, CELL_SIZE))

    # لکه‌های ریز برای بافت آسفالت
    for _ in range(10):
        px = x + rng.randrange(CELL_SIZE - 1)
        py = y + rng.randrange(CELL_SIZE - 1)
        tone = rng.choice([ASPHALT_LIGHT, ASPHALT_DARK])

        pygame.draw.rect(surf, tone, (px, py, 2, 2))

    # گاهی یک ترک کوچک روی آسفالت
    if rng.random() < 0.2:
        cx = x + rng.randrange(8, CELL_SIZE - 8)
        cy = y + rng.randrange(8, CELL_SIZE - 8)

        mid = (
            cx + rng.randrange(-6, 7),
            cy + rng.randrange(-6, 7)
        )

        end = (
            mid[0] + rng.randrange(-6, 7),
            mid[1] + rng.randrange(-6, 7)
        )

        pygame.draw.lines(
            surf,
            ASPHALT_DARK,
            False,
            [(cx, cy), mid, end],
            1
        )

    # خط دور خانه
    pygame.draw.rect(
        surf,
        ASPHALT_EDGE,
        (x, y, CELL_SIZE, CELL_SIZE),
        1
    )

    # پیاده‌رو کنار ساختمان‌ها
    s = 5

    if is_wall(grid, row - 1, col):
        pygame.draw.rect(surf, SIDEWALK, (x, y, CELL_SIZE, s))

    if is_wall(grid, row + 1, col):
        pygame.draw.rect(
            surf,
            SIDEWALK,
            (x, y + CELL_SIZE - s, CELL_SIZE, s)
        )

    if is_wall(grid, row, col - 1):
        pygame.draw.rect(surf, SIDEWALK, (x, y, s, CELL_SIZE))

    if is_wall(grid, row, col + 1):
        pygame.draw.rect(
            surf,
            SIDEWALK,
            (x + CELL_SIZE - s, y, s, CELL_SIZE)
        )

    # سایه‌ی ساختمان روی جاده
    top_wall = is_wall(grid, row - 1, col)
    left_wall = is_wall(grid, row, col - 1)

    if top_wall or left_wall:
        shadow = pygame.Surface(
            (CELL_SIZE, CELL_SIZE),
            pygame.SRCALPHA
        )

        if top_wall:
            pygame.draw.rect(
                shadow,
                (0, 0, 0, 80),
                (0, 0, CELL_SIZE, 12)
            )

        if left_wall:
            pygame.draw.rect(
                shadow,
                (0, 0, 0, 70),
                (0, 0, 10, CELL_SIZE)
            )

        surf.blit(shadow, (x, y))


def apply_vignette(surf):
    """لبه‌های تصویر را کمی تیره می‌کند تا عمق و حال‌وهوای سینمایی بدهد."""
    vignette = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    steps = 40

    for i in range(steps):
        alpha = int(80 * (1 - i / steps) ** 2)

        pygame.draw.rect(
            vignette,
            (0, 0, 0, alpha),
            (i, i, WIDTH - 2 * i, HEIGHT - 2 * i),
            1
        )

    surf.blit(vignette, (0, 0))


def build_background(grid):
    """کل ماز را یک بار روی یک تصویر می‌کشد و برمی‌گرداند."""
    surf = pygame.Surface((WIDTH, HEIGHT))
    rng = random.Random(7)

    # ساختمان‌ها را پیدا کن
    block_of, styles = find_buildings(grid)

    for row in range(len(grid)):
        for col in range(len(grid[0])):
            x = col * CELL_SIZE
            y = row * CELL_SIZE

            if grid[row][col] == WALL:
                draw_building(
                    surf,
                    grid,
                    block_of,
                    styles,
                    row,
                    col,
                    x,
                    y
                )
            else:
                draw_road(surf, grid, row, col, x, y, rng)

    apply_vignette(surf)

    return surf.convert()


class World:
    """همه‌ی اطلاعات یک ماز: خانه‌ها، تصویر پس‌زمینه، گراف و آمار."""

    def __init__(self, grid, background, graph, graph_ms):
        self.grid = grid
        self.background = background
        self.graph = graph
        self.graph_ms = graph_ms
        self.shared = 0


def new_map(protected):
    """یک ماز تصادفی جدید می‌سازد و یک World برمی‌گرداند."""
    grid = create_grid(ROWS, COLS)
    add_random_walls(grid, WALL_DENSITY, protected)

    t0 = time.perf_counter()

    # گراف فقط یک بار برای این ماز ساخته می‌شود
    graph = build_graph(grid)

    graph_ms = (time.perf_counter() - t0) * 1000

    return World(
        grid,
        build_background(grid),
        graph,
        graph_ms
    )


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
