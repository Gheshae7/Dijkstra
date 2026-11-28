"""
car_graphics.py  -  ساخت تصویر ماشین و جلوه‌هایش: بدنه، سایه، نور چراغ، دود، چراغ ترمز و مربع‌های جستجو.
"""

import pygame

from settings import CAR_H, CAR_SCALE, CAR_W, CELL_SIZE
from utils import shade


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
