"""
render.py  -  کشیدن جستجو، مسیر، مسیرهای مشترک، مقصد و ماشین‌ها روی صفحه.
"""

import math
import pygame

from settings import CAR_W, CELL_SIZE, SMOKE_LIFE, WHITE
from utils import cell_center, shade
from sharing import route_visible, segment_shown


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
