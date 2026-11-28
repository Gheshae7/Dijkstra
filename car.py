"""
car.py  -  کلاس ماشین (Car) و حرکت دادن آن در هر فریم (update_car) با وضعیت‌های
ready / searching / preview / moving / arrived / no_path.
"""

import math
import time

from settings import (
    AHEAD_ALPHA,
    CELL_SIZE,
    MIN_SPEED,
    PREVIEW_TIME,
    SEARCH_SPEED,
    SMOKE_LIFE,
    TURN_SPEED,
)
from utils import cell_center
from dijkstra import dijkstra
from driving import build_curve, build_speed_profile, locate_on_curve
from car_graphics import (
    make_car_surface,
    make_shadow_surface,
    make_light_surface,
    make_smoke_frames,
    make_brake_surface,
    make_overlay_surface,
    make_glow_surface,
)


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


# وضعیت‌هایی که نشان می‌دهند ماشین هنوز مشغول انجام کار است
BUSY_STATES = ("searching", "preview", "moving")


def is_idle(cars):
    """آیا همه‌ی ماشین‌ها ایستاده‌اند؟ (آماده یا تمام‌شده)"""
    return not any(car.state in BUSY_STATES for car in cars)
