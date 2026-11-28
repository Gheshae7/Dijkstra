"""
hud.py  -  رابط کاربری: نوار اطلاعات بالا، نوار راهنمای پایین، پیام شروع و پیام کوتاه (toast).
"""

import math
import pygame

from settings import FPS, HEIGHT, MAX_SPEED, WHITE, WIDTH
from utils import shade
from car import is_idle


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


HUD_ROW_H = 22      # ارتفاع هر ردیف پنل


HUD_GAP = 8         # فاصله‌ی بین آیتم‌ها


HUD_PAD = 7         # حاشیه‌ی داخل پنل


HUD_MARGIN = 8      # فاصله‌ی پنل از لبه‌ی پنجره


# متن، رنگ متن و رنگ پس‌زمینه‌ی برچسب وضعیت هر ماشین
STATUS_STYLE = {
    "ready": ("READY", (195, 203, 225), (44, 50, 70)),
    "preview": ("ROUTE", (160, 255, 205), (24, 72, 52)),
    "searching": ("SEARCHING", (255, 205, 90), (70, 56, 24)),
    "moving": ("DRIVING", (120, 210, 255), (22, 56, 78)),
    "arrived": ("ARRIVED", (125, 235, 150), (24, 70, 40)),
    "no_path": ("NO PATH", (255, 120, 120), (80, 30, 30)),
}


def make_fonts():
    """فونت‌ها را می‌سازد (بزرگ برای پیام شروع، متن و متن کوچک برای پنل)."""
    return {
        "big": pygame.font.SysFont("arial", 20, bold=True),
        "body": pygame.font.SysFont("arial", 14, bold=True),
        "small": pygame.font.SysFont("arial", 12, bold=True),
    }


def text_width(font, text):
    """عرض یک متن را (به پیکسل) برمی‌گرداند."""
    return font.size(text)[0]


def draw_pill(screen, font, text, text_color, bg_color, x, y, width, h=18):
    """یک برچسب قرصی‌شکل با عرض مشخص می‌کشد و متن را وسطش می‌گذارد."""
    label = font.render(text, True, text_color)
    pygame.draw.rect(screen, bg_color, (x, y, width, h), border_radius=h // 2)
    screen.blit(
        label,
        (x + (width - label.get_width()) // 2,
         y + (h - label.get_height()) // 2)
    )


def draw_bar(screen, x, y, w, h, ratio, color):
    """یک نوار پیشرفت گرد می‌کشد (ratio عددی بین 0 و 1 است)."""
    ratio = max(0.0, min(1.0, ratio))
    pygame.draw.rect(screen, (52, 57, 74), (x, y, w, h), border_radius=h // 2)
    fill_w = int(w * ratio)

    if fill_w >= h:
        pygame.draw.rect(screen, color, (x, y, fill_w, h), border_radius=h // 2)
    elif fill_w > 0:
        pygame.draw.rect(screen, color, (x, y, fill_w, h))


def car_progress(car):
    """پیشرفت ماشین (بین 0 و 1): در حالت جستجو، پیشرفت جستجو؛ در حالت رانندگی، مسافت طی‌شده."""
    if car.state == "searching":
        return car.search_progress / len(car.visited) if car.visited else 0.0

    if car.state == "moving":
        return car.distance / car.total_length if car.total_length else 0.0

    if car.state == "arrived":
        return 1.0

    return 0.0


def keycap_width(fonts, key, label):
    """عرض یک دکمه‌ی کیبورد همراه با توضیحش را حساب می‌کند."""
    return text_width(fonts["small"], key) + 14 + 6 + text_width(fonts["small"], label)


def draw_keycap(screen, fonts, key, label, x, y, active=False):
    """یک دکمه‌ی کیبورد (مثل R) با توضیح کنارش می‌کشد. اگر active باشد سبز می‌شود."""
    cap = fonts["small"].render(key, True, WHITE)
    w, h = cap.get_width() + 14, 17

    under, top = (
        ((40, 110, 70), (70, 175, 110))
        if active else
        ((62, 68, 90), (98, 106, 134))
    )

    pygame.draw.rect(screen, under, (x, y + 2, w, h), border_radius=5)
    pygame.draw.rect(screen, top, (x, y, w, h), border_radius=5)
    screen.blit(cap, (x + 7, y + (h - cap.get_height()) // 2))

    text = fonts["small"].render(label, True, (190, 196, 214))
    screen.blit(text, (x + w + 6, y + (h - text.get_height()) // 2))


def make_item(width, draw, is_separator=False):
    """یک آیتم پنل می‌سازد: عرض، تابع کشیدن draw(screen, x, y) و اینکه جداکننده است یا نه."""
    return {"w": width, "draw": draw, "sep": is_separator}


def make_separator_item():
    """یک خط عمودی نازک بین گروه‌های آیتم."""
    def draw(screen, x, y):
        pygame.draw.line(
            screen,
            (70, 76, 98),
            (x, y + 4),
            (x, y + HUD_ROW_H - 4)
        )

    return make_item(1, draw, True)


def make_key_item(fonts, key, label, is_active=None):
    """آیتم راهنمای یک کلید. is_active (اختیاری) تابعی است که تعیین می‌کند دکمه سبز باشد یا نه."""
    def draw(screen, x, y):
        active = is_active() if is_active else False
        draw_keycap(screen, fonts, key, label, x, y + 2, active)

    return make_item(keycap_width(fonts, key, label), draw)


def make_car_item(fonts, car, index, compact, selected=False):
    """
    آیتم یک ماشین: نقطه‌ی رنگی، نام، برچسب وضعیت و نوار پیشرفت.
    در حالت compact نام کوتاه می‌شود و عدد سرعت نمایش داده نمی‌شود (برای چند ماشین).
    عرض‌ها از روی متن‌های نمونه (مثل "SEARCHING" و "888 km/h") حساب می‌شوند
    تا با عوض شدن عددها، پنل نلرزد.
    """
    body, small = fonts["body"], fonts["small"]
    name = str(index + 1) if compact else f"Car {index + 1}"
    name_w = text_width(body, name)
    pill_w = text_width(small, "SEARCHING") + 14
    bar_w = 36 if compact else 44
    info_w = 0 if compact else text_width(small, "888 km/h")

    width = (
        16 + 4 + name_w + 6 + pill_w + 6 + bar_w
        + (0 if compact else 6 + info_w)
    )

    def draw(screen, x, y):
        cy = y + HUD_ROW_H // 2

        # نقطه‌ی هم‌رنگ ماشین (ماشین انتخاب‌شده یک حلقه‌ی سفید دارد)
        pygame.draw.circle(screen, car.color, (x + 8, cy), 5)
        pygame.draw.circle(screen, shade(car.color, 1.35), (x + 7, cy - 1), 2)

        if selected:
            pygame.draw.circle(screen, WHITE, (x + 8, cy), 8, 2)

        cx = x + 16 + 4

        # نام ماشین
        label = body.render(name, True, WHITE)
        screen.blit(label, (cx, cy - label.get_height() // 2))
        cx += name_w + 6

        # برچسب وضعیت
        status, fg, bg = STATUS_STYLE[car.state]
        draw_pill(screen, small, status, fg, bg, cx, y + 2, pill_w)
        cx += pill_w + 6

        # نوار پیشرفت
        draw_bar(screen, cx, cy - 2, bar_w, 5, car_progress(car), car.color)
        cx += bar_w + 6

        # عدد کنار نوار (فقط در حالت کامل)
        if not compact:
            if car.state == "searching":
                info = f"{int(car.search_progress)}/{len(car.visited)}"
            elif car.state == "no_path":
                info = "blocked"
            else:
                info = f"{car.speed / MAX_SPEED * 60:.0f} km/h"

            text = small.render(info, True, (170, 176, 198))
            screen.blit(text, (cx, cy - text.get_height() // 2))

    return make_item(width, draw)


def build_hud_items(fonts, limiter, cars, compact, world, random_mode, selected):
    """
    همه‌ی آیتم‌های نوار بالا را به ترتیب می‌سازد:
    FPS، زمان Dijkstra، زمان ساخت گراف، حالت جای ماشین‌ها، ماشین‌ها و مسیر مشترک.
    """
    small = fonts["small"]
    items = []

    # FPS (سبز اگر نزدیک عدد هدف باشد، وگرنه نارنجی)
    fps_w = text_width(small, "000 FPS") + 14

    def draw_fps(screen, x, y):
        fps = limiter.get_fps()
        ok = fps >= FPS - 3

        draw_pill(
            screen, small, f"{fps:.0f} FPS",
            (125, 235, 150) if ok else (255, 175, 70),
            (24, 70, 40) if ok else (80, 52, 20),
            x, y + 2, fps_w
        )

    items.append(make_item(fps_w, draw_fps))

    # زمان اجرای Dijkstra (مجموع همه‌ی ماشین‌ها)
    algo_w = text_width(small, "Dijkstra 00.00 ms") + 14

    def draw_algo(screen, x, y):
        total = sum(car.search_ms for car in cars)

        draw_pill(
            screen, small, f"Dijkstra {total:.2f} ms",
            (255, 215, 120), (68, 54, 22),
            x, y + 2, algo_w
        )

    items.append(make_item(algo_w, draw_algo))

    # زمان ساخت گراف (یک بار برای هر ماز)
    graph_w = text_width(small, "Graph 00.00 ms") + 14

    def draw_graph(screen, x, y):
        draw_pill(
            screen, small, f"Graph {world.graph_ms:.2f} ms",
            (140, 225, 235), (20, 60, 70),
            x, y + 2, graph_w
        )

    items.append(make_item(graph_w, draw_graph))

    # حالت جای ماشین‌ها: تصادفی یا دستی
    mode_w = text_width(small, "RANDOM") + 14

    def draw_mode(screen, x, y):
        if random_mode:
            draw_pill(
                screen, small, "RANDOM",
                (200, 235, 150), (44, 64, 22),
                x, y + 2, mode_w
            )
        else:
            draw_pill(
                screen, small, "MANUAL",
                (255, 170, 200), (84, 36, 58),
                x, y + 2, mode_w
            )

    items.append(make_item(mode_w, draw_mode))
    items.append(make_separator_item())

    # ماشین‌ها
    for index, car in enumerate(cars):
        items.append(
            make_car_item(
                fonts, car, index, compact,
                selected == index and len(cars) > 1
            )
        )

    # اگر مسیر چند ماشین یکی شده، یک برچسب «Merged n» نشان بده
    if len(cars) > 1 and world.shared > 0:
        merged_w = text_width(small, "Merged 000") + 14

        def draw_merged(screen, x, y):
            draw_pill(
                screen, small, f"Merged {world.shared}",
                (235, 225, 255), (74, 58, 110),
                x, y + 2, merged_w
            )

        items.append(make_item(merged_w, draw_merged))

    return items


def row_width(row):
    """عرض کل یک ردیف از آیتم‌ها."""
    return sum(item["w"] for item in row) + HUD_GAP * max(0, len(row) - 1)


def layout_hud(items, max_width):
    """
    آیتم‌ها را در ردیف‌ها می‌چیند: تا وقتی جا هست در یک خط،
    وقتی جا نشد به خط بعد می‌رود. جداکننده‌ی اول و آخر هر ردیف حذف می‌شود.
    """
    rows = [[]]

    for item in items:
        row = rows[-1]

        if item["sep"] and not row:
            continue

        if row and row_width(row) + HUD_GAP + item["w"] > max_width:
            while rows[-1] and rows[-1][-1]["sep"]:
                rows[-1].pop()

            rows.append([])

            if item["sep"]:
                continue

        rows[-1].append(item)

    while rows[-1] and rows[-1][-1]["sep"]:
        rows[-1].pop()

    return rows


def rows_size(rows):
    """اندازه‌ی پنلی که ردیف‌ها را در خود جا می‌دهد: (عرض، ارتفاع)."""
    width = max(row_width(row) for row in rows) + 2 * HUD_PAD
    height = len(rows) * HUD_ROW_H + (len(rows) - 1) * 4 + 2 * HUD_PAD
    return width, height


def draw_panel(screen, x, y, w, h):
    """یک پنل نیمه‌شفاف با گوشه‌ی گرد، سایه و کادر نازک می‌کشد."""
    panel = pygame.Surface((w + 3, h + 4), pygame.SRCALPHA)

    pygame.draw.rect(
        panel, (0, 0, 0, 55),
        (2, 3, w, h), border_radius=12
    )

    pygame.draw.rect(
        panel, (14, 17, 26, 175),
        (0, 0, w, h), border_radius=12
    )

    pygame.draw.rect(
        panel, (255, 255, 255, 34),
        (0, 0, w, h), 1, border_radius=12
    )

    screen.blit(panel, (x, y))


def draw_rows(screen, rows, x, y):
    """آیتم‌های هر ردیف را از چپ به راست و ردیف‌ها را از بالا به پایین می‌کشد."""
    for row in rows:
        cx = x

        for item in row:
            item["draw"](screen, cx, y)
            cx += item["w"] + HUD_GAP

        y += HUD_ROW_H + 4


def draw_hud(screen, fonts, limiter, cars, world, random_mode, selected):
    """
    نوار اطلاعات باریک و نیمه‌شفاف بالا-چپ؛ با چند ماشین، فشرده و در صورت نیاز چندخطی می‌شود.
    مستطیل نوار را برمی‌گرداند (برای نادیده گرفتن کلیک روی آن).
    """
    max_width = WIDTH - 2 * HUD_MARGIN - 2 * HUD_PAD
    compact = len(cars) > 1

    rows = layout_hud(
        build_hud_items(fonts, limiter, cars, compact, world, random_mode, selected),
        max_width
    )

    width, height = rows_size(rows)

    draw_panel(screen, HUD_MARGIN, HUD_MARGIN, width, height)
    draw_rows(screen, rows, HUD_MARGIN + HUD_PAD, HUD_MARGIN + HUD_PAD)

    return (HUD_MARGIN, HUD_MARGIN, width, height)


def draw_controls_bar(screen, fonts, cars):
    """
    نوار راهنمای کلیدها و ماوس را پایین صفحه نشان می‌دهد.
    فقط وقتی ماشین‌ها ایستاده‌اند (آماده یا تمام‌شده) دیده می‌شود تا موقع حرکت نقشه شلوغ نشود.
    مستطیل نوار را برمی‌گرداند (یا None اگر نمایش داده نشد).
    """
    if not is_idle(cars):
        return None

    items = [
        make_key_item(
            fonts, "SPACE", "Start",
            lambda: all(car.state == "ready" for car in cars)
        ),
        make_key_item(fonts, "R", "Replay"),
        make_key_item(fonts, "N", "New map"),
        make_key_item(fonts, "C", "Random cars"),
        make_key_item(fonts, "H", "HUD"),
        make_separator_item(),
        make_key_item(fonts, "Click", "Set start"),
        make_key_item(fonts, "Right-click", "Set goal"),
    ]

    if len(cars) > 1:
        items.append(make_key_item(fonts, "1-9", "Pick car"))

    rows = layout_hud(items, WIDTH - 2 * HUD_MARGIN - 2 * HUD_PAD)
    width, height = rows_size(rows)

    x, y = (WIDTH - width) // 2, HEIGHT - HUD_MARGIN - height

    draw_panel(screen, x, y, width, height)
    draw_rows(screen, rows, x + HUD_PAD, y + HUD_PAD)

    return (x, y, width, height)
