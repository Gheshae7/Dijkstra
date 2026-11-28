"""
main.py  -  برنامه‌ی اصلی: پنجره را می‌سازد و حلقه‌ی بازی (رویدادها، به‌روزرسانی، کشیدن) را اجرا می‌کند.
"""

import pygame

from settings import CELL_SIZE, FPS, HEIGHT, RANDOM_PLACEMENT, WIDTH
from utils import inside
from car import update_car, is_idle
from sharing import plan_all
from world import place_cars_randomly, try_place_point, make_cars, start_round
from render import draw_search, draw_trail, draw_merged_routes, draw_cars
from hud import draw_start_prompt, draw_toast, make_fonts, draw_hud, draw_controls_bar
from limiter import FrameLimiter


def main():
    """برنامه‌ی اصلی: پنجره را می‌سازد و حلقه‌ی بازی را اجرا می‌کند."""

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Pathfinding Showcase")

    limiter = FrameLimiter(FPS)       # قفل دقیق FPS
    fonts = make_fonts()

    cars = make_cars()                # تعداد و رنگ ماشین‌ها
    random_mode = RANDOM_PLACEMENT    # True: جای ماشین‌ها هم تصادفی عوض می‌شود
    world = start_round(cars, random_mode)

    selected = 0                      # ماشین انتخاب‌شده
    toast_text, toast_until = "", 0   # پیام کوتاه و زمان پایانش
    hud_rect = controls_rect = None
    show_hud = True
    dt = 0
    running = True

    while running:

        # 1) گرفتن رویدادها (کلیک، کیبورد، بستن پنجره)
        for event in pygame.event.get():
            now = pygame.time.get_ticks()

            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):

                # کلیک روی نوارها نباید روی نقشه اثر بگذارد
                if inside(hud_rect, event.pos) or inside(controls_rect, event.pos):
                    continue

                if not is_idle(cars):
                    toast_text, toast_until = "Wait until the cars stop", now + 1800
                    continue

                cell = (
                    event.pos[1] // CELL_SIZE,
                    event.pos[0] // CELL_SIZE
                )

                kind = "start" if event.button == 1 else "goal"

                ok, toast_text = try_place_point(
                    cars, world, selected, kind, cell
                )

                toast_until = now + 1800

                if ok:
                    random_mode = False
                    world.shared = plan_all(cars, world.graph)

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_n:
                    # ماز جدید
                    world = start_round(cars, random_mode)

                elif event.key == pygame.K_r:
                    # پخش دوباره روی همین ماز
                    world.shared = plan_all(cars, world.graph)

                    for car in cars:
                        car.begin()

                elif event.key == pygame.K_SPACE:
                    # شروع ماشین‌های آماده
                    for car in cars:
                        car.begin()

                elif event.key == pygame.K_c:
                    # جای تصادفی جدید برای ماشین‌ها روی همین ماز
                    if not is_idle(cars):
                        toast_text, toast_until = "Wait until the cars stop", now + 1800

                    elif place_cars_randomly(cars, world.graph):
                        random_mode = True
                        world.shared = plan_all(cars, world.graph)

                    else:
                        toast_text, toast_until = "No room for the cars", now + 1800

                elif event.key == pygame.K_h:
                    # نمایش / پنهان کردن نوار بالا
                    show_hud = not show_hud

                elif pygame.K_1 <= event.key <= pygame.K_9:
                    # انتخاب ماشین
                    index = event.key - pygame.K_1

                    if index < len(cars):
                        selected = index
                        toast_text = f"Car {index + 1} selected"
                        toast_until = now + 1200

        # 2) به‌روزرسانی وضعیت ماشین‌ها
        for car in cars:
            update_car(car, dt)

        # 3) رسم اجزای بازی (ترتیب لایه‌ها مهم است)
        screen.blit(world.background, (0, 0))

        for car in cars:
            draw_search(screen, car)

        for car in cars:
            draw_trail(screen, car)

        draw_merged_routes(screen, cars)
        draw_cars(screen, cars, selected)

        controls_rect = draw_controls_bar(screen, fonts, cars)

        bottom = controls_rect[1] - 10 if controls_rect else HEIGHT - 22

        draw_start_prompt(screen, fonts, cars, bottom)

        if pygame.time.get_ticks() < toast_until:
            draw_toast(screen, fonts, toast_text)

        hud_rect = (
            draw_hud(screen, fonts, limiter, cars, world, random_mode, selected)
            if show_hud else None
        )

        pygame.display.flip()

        # 4) صبر تا فریم بعدی و گرفتن مدت فریم
        dt = min(limiter.wait(), 100)

    pygame.quit()


if __name__ == "__main__":
    main()
