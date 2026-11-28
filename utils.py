"""
utils.py  -  توابع کمکی کوچک که چند فایل از آن‌ها استفاده می‌کنند: مرکز خانه به پیکسل، روشن/تیره کردن رنگ، چک کردن کلیک داخل مستطیل.
"""

from settings import CELL_SIZE


def cell_center(row, col):
    """
    مرکز یک خانه را بر اساس مختصات سطر و ستون
    به مختصات پیکسلی تبدیل می‌کند.

    row و col می‌توانند عدد اعشاری هم باشند.
    """

    x = col * CELL_SIZE + CELL_SIZE // 2
    y = row * CELL_SIZE + CELL_SIZE // 2

    return (x, y)


def shade(color, factor):
    """رنگ را روشن‌تر یا تیره‌تر می‌کند."""
    return tuple(
        max(0, min(255, int(c * factor)))
        for c in color
    )


def inside(rect, pos):
    """آیا نقطه‌ی pos داخل مستطیل rect=(x, y, عرض، ارتفاع) است؟ (rect می‌تواند None باشد)"""
    if rect is None:
        return False

    x, y, w, h = rect
    return x <= pos[0] < x + w and y <= pos[1] < y + h
