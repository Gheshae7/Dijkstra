
import pygame
import sys

# دریافت تنظیمات موردنیاز از فایل settings.py
from settings import WIDTH, HEIGHT, FPS, WHITE, COLS, ROWS, GRID_COLOR, GRID_LINE_WIDTH, BACKGROUND_COLOR, FREE, WALL, BLACK, WALL_DENSITY

import random


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

# ساخت ماتریس محیط بازی
# هر خانه در ابتدا با مقدار FREE مشخص می‌شود
grid = [
    [FREE for _ in range(COLS)]
    for _ in range(ROWS)
]

# محاسبه تعداد دیوارهای موردنیاز بر اساس تراکم مشخص‌شده
wall_count = int(ROWS * COLS * WALL_DENSITY)

# انتخاب تصادفی خانه‌ها و تبدیل آن‌ها به دیوار
for _ in range(wall_count):
    row = random.randrange(ROWS)
    col = random.randrange(COLS)

    grid[row][col] = WALL

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

# متغیری برای کنترل اجرای حلقه اصلی بازی
running = True

# حلقه اصلی بازی؛ تا زمانی که running برابر True باشد ادامه دارد
while running:

    # بررسی رویدادهای اتفاق‌افتاده، مثل کلیک روی دکمه بستن پنجره
    for event in pygame.event.get():

        # اگر کاربر پنجره را ببندد، حلقه بازی متوقف می‌شود
        if event.type == pygame.QUIT:
            running = False

    # پاک کردن صفحه و رنگ‌آمیزی پس‌زمینه محیط بازی
    screen.fill(BACKGROUND_COLOR)

    # رسم دیوارهای محیط بازی
    draw_walls(screen, grid)

    # رسم خطوط شبکه روی محیط بازی
    draw_grid(screen)

    # به‌روزرسانی صفحه نمایش و نمایش تصویر جدید
    pygame.display.flip()

    # محدود کردن سرعت اجرای حلقه بازی بر اساس مقدار FPS
    clock.tick(FPS)


# خروج صحیح از Pygame پس از پایان حلقه اصلی
pygame.quit()

# پایان دادن به اجرای برنامه پایتون
sys.exit()
