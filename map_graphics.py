"""
map_graphics.py  -  کشیدن ماز: ساختمان‌ها، جاده و تصویر پس‌زمینه‌ی کامل (یک بار کشیده می‌شود).
"""

import random
import pygame

from settings import (
    ASPHALT,
    ASPHALT_DARK,
    ASPHALT_EDGE,
    ASPHALT_LIGHT,
    BUILDING_KINDS,
    CELL_SIZE,
    DIRECTIONS,
    FACADE_H,
    GARDEN_ROOF,
    HEIGHT,
    ROOF_COLORS,
    SIDEWALK,
    WALL,
    WALL_COLORS,
    WIDTH,
)
from utils import shade
from grid import is_wall


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
