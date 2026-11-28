"""
grid.py  -  ساخت ماز: ماتریس خانه‌ها، گذاشتن دیوار (تصادفی) و بررسی دیوار بودن یک خانه.
"""

import random

from settings import COLS, FREE, GOAL_POS, ROWS, START_POS, WALL, WALL_DENSITY


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
