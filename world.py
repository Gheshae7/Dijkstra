"""
world.py  -  جهان بازی: ماز + گراف + جای ماشین‌ها (تصادفی یا دستی) و ساخت دور جدید.
"""

import random
import time

from settings import (
    CAR_COLORS,
    COLS,
    MANUAL_POSITIONS,
    MIN_TRIP,
    NUM_CARS,
    RANDOM_PLACEMENT,
    ROWS,
    WALL,
    WALL_DENSITY,
)
from grid import create_grid, add_random_walls
from graph import build_graph
from dijkstra import dijkstra
from car import Car
from sharing import plan_all
from map_graphics import build_background


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


def get_protected(cars):
    """خانه‌هایی که نباید دیوار شوند: شروع و مقصد همه‌ی ماشین‌ها."""
    protected = set()

    for car in cars:
        protected.add(car.start)
        protected.add(car.goal)

    return protected


def place_cars_randomly(cars, graph):
    """
    برای هر ماشین یک شروع و مقصد تصادفی انتخاب می‌کند.

    شرط‌ها:
    - همه‌ی خانه‌ها متفاوت باشند.
    - فاصله‌ی شروع تا مقصد حداقل MIN_TRIP باشد.
    - بین شروع و مقصد مسیر وجود داشته باشد.

    اگر موفق شود True برمی‌گرداند؛ در غیر این صورت False.
    """

    free = list(graph.keys())
    need = len(cars) * 2

    if len(free) < need:
        return False

    for attempt in range(200):

        # اگر بعد از ۱۵۰ تلاش موفق نشدیم، فاصله‌ی حداقل را کاهش می‌دهیم.
        min_trip = MIN_TRIP if attempt < 150 else 1

        # انتخاب خانه‌های متفاوت
        chosen = random.sample(free, need)

        # ساخت زوج‌های شروع و مقصد برای ماشین‌ها
        pairs = [
            (chosen[2 * i], chosen[2 * i + 1])
            for i in range(len(cars))
        ]

        # بررسی حداقل فاصله‌ی شروع تا مقصد
        too_close = any(
            abs(s[0] - g[0]) + abs(s[1] - g[1]) < min_trip
            for s, g in pairs
        )

        if too_close:
            continue

        # بررسی وجود مسیر برای تمام ماشین‌ها
        if all(dijkstra(graph, s, g)[0] for s, g in pairs):

            # اگر همه‌ی شرایط برقرار بود، جای ماشین‌ها را تغییر می‌دهیم.
            for car, (s, g) in zip(cars, pairs):
                car.start, car.goal = s, g

            return True

    return False


def try_place_point(cars, world, index, kind, cell):
    """
    شروع یا مقصد ماشین مشخص‌شده را روی یک خانه قرار می‌دهد.

    kind می‌تواند start یا goal باشد.

    خروجی:
    (موفق شد؟، پیام)
    """

    row, col = cell

    # بررسی خارج نبودن خانه از محدوده‌ی ماز
    if not (0 <= row < ROWS and 0 <= col < COLS):
        return False, "Outside the map"

    # بررسی دیوار نبودن خانه
    if world.grid[row][col] == WALL:
        return False, "That cell is a building"

    # خانه‌هایی که ماشین‌ها قبلاً اشغال کرده‌اند
    # به‌جز همان نقطه‌ای که در حال جابه‌جایی آن هستیم.
    taken = set()

    for k, other in enumerate(cars):

        for name, point in (
            ("start", other.start),
            ("goal", other.goal)
        ):

            if k == index and name == kind:
                continue

            taken.add(point)

    if cell in taken:
        return False, "Cell already used"

    car = cars[index]

    # محاسبه‌ی شروع و مقصد جدید
    new_start = cell if kind == "start" else car.start
    new_goal = cell if kind == "goal" else car.goal

    # بررسی وجود مسیر بین شروع و مقصد جدید
    if not dijkstra(world.graph, new_start, new_goal)[0]:
        return False, "No route there"

    # اعمال تغییرات پس از موفقیت بررسی‌ها
    car.start, car.goal = new_start, new_goal

    return True, f"Car {index + 1} {kind} moved"


def make_cars():
    """ماشین‌ها را تصادفی یا بر اساس MANUAL_POSITIONS می‌سازد."""

    if RANDOM_PLACEMENT:

        count = max(1, min(NUM_CARS, len(CAR_COLORS)))

        # جای واقعی ماشین‌ها در start_round تعیین می‌شود.
        return [
            Car((0, 0), (0, 1), CAR_COLORS[i])
            for i in range(count)
        ]

    cars, seen = [], set()

    for i, (start, goal) in enumerate(
        MANUAL_POSITIONS[:len(CAR_COLORS)]
    ):

        for point in (start, goal):

            # بررسی قرار داشتن نقطه داخل ماز
            if not (
                0 <= point[0] < ROWS
                and 0 <= point[1] < COLS
            ):
                raise ValueError(
                    f"MANUAL_POSITIONS: {point} خارج از ماز است"
                )

            # بررسی تکراری نبودن نقطه‌ها
            if point in seen:
                raise ValueError(
                    f"MANUAL_POSITIONS: {point} دو بار استفاده شده"
                )

            seen.add(point)

        cars.append(Car(start, goal, CAR_COLORS[i]))

    return cars


def start_round(cars, random_mode):
    """
    یک ماز جدید می‌سازد که همه‌ی ماشین‌ها در آن مسیر داشته باشند.

    random_mode=True:
        جای ماشین‌ها نیز تصادفی تغییر می‌کند.

    random_mode=False:
        ماشین‌ها در جای قبلی خود باقی می‌مانند.

    ماشین‌ها در وضعیت ready باقی می‌مانند تا کاربر SPACE بزند.
    در پایان یک World برمی‌گرداند.
    """

    world, planned = None, False

    for _ in range(60):

        # در حالت تصادفی نقطه‌ای محافظت نمی‌شود؛
        # در حالت دستی، شروع و مقصد ماشین‌ها محافظت می‌شوند.
        protected = set() if random_mode else get_protected(cars)

        world = new_map(protected)

        planned = False

        # تعیین تصادفی شروع و مقصد ماشین‌ها
        if random_mode and not place_cars_randomly(cars, world.graph):
            continue

        # محاسبه‌ی مسیر تمام ماشین‌ها و مسیرهای مشترک
        world.shared = plan_all(cars, world.graph)

        planned = True

        # اگر همه‌ی ماشین‌ها مسیر داشتند، تلاش تمام می‌شود.
        if all(car.path for car in cars):
            break

    # اگر بعد از ۶۰ تلاش مسیر مناسبی پیدا نشد،
    # باز هم مسیرها را برای آخرین ماز محاسبه می‌کنیم.
    if not planned:
        world.shared = plan_all(cars, world.graph)

    return world
