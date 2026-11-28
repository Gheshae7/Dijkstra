"""
driving.py  -  منطق رانندگی: تبدیل مسیر خانه‌ای به منحنی نرم، نمودار سرعت (شتاب و ترمز)
و پیدا کردن جای ماشین روی منحنی.
"""

import math
import bisect

from settings import ACCEL, BRAKE, CORNER_SPEED, CURVE_STEPS, MAX_SPEED
from utils import cell_center


def build_curve(path):
    """
    مسیر خانه‌ها را به یک منحنی نرم تبدیل می‌کند.

    در خانه‌هایی که ماشین باید تغییر جهت بدهد،
    به‌جای حرکت مستقیم از یک منحنی استفاده می‌کنیم.

    خروجی:
        points: نقاط مسیر بر حسب پیکسل
        turning: مشخص می‌کند هر نقطه داخل پیچ است یا خیر
        positions: موقعیت هر نقطه در مسیر اصلی
    """

    centers = [cell_center(row, col) for row, col in path]

    points = []
    turning = []
    positions = []

    def add(point, is_turn, position):
        # نقطه‌ی تکراری را دوباره اضافه نکن
        if points and math.hypot(
            point[0] - points[-1][0],
            point[1] - points[-1][1]
        ) < 1e-6:

            turning[-1] = turning[-1] or is_turn
            return

        points.append(point)
        turning.append(is_turn)
        positions.append(position)

    add(centers[0], False, 0)

    for i in range(1, len(centers) - 1):

        prev, cur, nxt = centers[i - 1], centers[i], centers[i + 1]

        # حاصل‌ضرب خارجی صفر یعنی سه نقطه روی یک خط‌اند.
        cross = (
            (cur[0] - prev[0]) * (nxt[1] - cur[1])
            - (cur[1] - prev[1]) * (nxt[0] - cur[0])
        )

        if cross == 0:
            add(cur, False, i)

        else:
            # پیچ: از وسط ضلع قبلی تا وسط ضلع بعدی
            m1 = (
                (prev[0] + cur[0]) / 2,
                (prev[1] + cur[1]) / 2
            )

            m2 = (
                (cur[0] + nxt[0]) / 2,
                (cur[1] + nxt[1]) / 2
            )

            for s in range(CURVE_STEPS + 1):

                t = s / CURVE_STEPS

                x = (
                    (1 - t) ** 2 * m1[0]
                    + 2 * (1 - t) * t * cur[0]
                    + t ** 2 * m2[0]
                )

                y = (
                    (1 - t) ** 2 * m1[1]
                    + 2 * (1 - t) * t * cur[1]
                    + t ** 2 * m2[1]
                )

                add(
                    (x, y),
                    True,
                    i - 0.5 + t
                )

    add(centers[-1], False, len(centers) - 1)

    return points, turning, positions


def build_speed_profile(dists, turning):
    """
    برای هر نقطه‌ی منحنی، سرعت مجاز را محاسبه می‌کند.

    در مسیر مستقیم سرعت بیشتر است.
    در پیچ سرعت کمتر می‌شود.
    ابتدا و انتهای مسیر سرعت صفر است.

    ماشین قبل از رسیدن به پیچ ترمز می‌کند
    و بعد از عبور از پیچ دوباره شتاب می‌گیرد.
    """

    limits = [
        CORNER_SPEED if t else MAX_SPEED
        for t in turning
    ]

    limits[0] = 0.0
    limits[-1] = 0.0

    # حرکت از آخر به اول:
    # محاسبه سرعت مناسب برای ترمز قبل از پیچ
    for k in range(len(limits) - 2, -1, -1):

        seg = dists[k + 1] - dists[k]

        limits[k] = min(
            limits[k],
            math.sqrt(
                limits[k + 1] ** 2 + 2 * BRAKE * seg
            )
        )

    # حرکت از اول به آخر:
    # محدود کردن شتاب برای افزایش تدریجی سرعت
    for k in range(1, len(limits)):

        seg = dists[k] - dists[k - 1]

        limits[k] = min(
            limits[k],
            math.sqrt(
                limits[k - 1] ** 2 + 2 * ACCEL * seg
            )
        )

    return limits


def locate_on_curve(curve, dists, d):
    """
    موقعیت ماشین را روی منحنی پیدا می‌کند.

    d فاصله‌ی طی‌شده از ابتدای منحنی است.

    خروجی:
        x: مختصات افقی
        y: مختصات عمودی
        k: شماره قطعه فعلی منحنی
        frac: میزان پیشرفت در قطعه فعلی
        angle: زاویه حرکت ماشین
    """

    k = bisect.bisect_right(dists, d) - 1

    k = max(0, min(k, len(curve) - 2))

    seg_len = dists[k + 1] - dists[k]

    frac = (
        (d - dists[k]) / seg_len
        if seg_len > 0
        else 0.0
    )

    frac = max(0.0, min(1.0, frac))

    x0, y0 = curve[k]
    x1, y1 = curve[k + 1]

    x = x0 + (x1 - x0) * frac
    y = y0 + (y1 - y0) * frac

    angle = math.degrees(
        math.atan2(-(y1 - y0), x1 - x0)
    ) % 360

    return x, y, k, frac, angle
