"""
sharing.py  -  تشخیص مسیرهای مشترک بین ماشین‌ها: کدام تکه‌ی راه را چند ماشین با هم می‌روند.
"""

from settings import AHEAD_ALPHA


def compute_sharing(cars):
    """
    پیدا می‌کند کدام تکه‌های مسیر بین چند ماشین مشترک است.
    «یال» یعنی جفت خانه‌ی پشت سر هم؛ اگر دو ماشین از یک یال بروند، مسیرشان یکی شده.
    تعداد یال‌های مشترک را برمی‌گرداند.
    """
    users = {}  # یال -> شماره‌ی ماشین‌هایی که از آن می‌روند

    for index, car in enumerate(cars):
        car.edge_last_seg = {}

        for k, edge in enumerate(car.seg_edges):
            car.edge_last_seg[edge] = k

        for edge in set(car.seg_edges):
            users.setdefault(edge, []).append(index)

    for car in cars:
        car.shared = [
            users[e] if len(users[e]) > 1 else None
            for e in car.seg_edges
        ]

    return sum(1 for u in users.values() if len(u) > 1)


def plan_all(cars, graph):
    """برای همه‌ی ماشین‌ها Dijkstra اجرا می‌کند و مسیرهای مشترک را پیدا می‌کند."""
    for car in cars:
        car.plan(graph)

    return compute_sharing(cars)


def route_visible(car):
    """آیا مسیر این ماشین الان روی صفحه نمایش داده می‌شود؟"""
    return car.state in ("preview", "moving", "arrived")


def segment_shown(car, k):
    """آیا تکه‌ی k از مسیر این ماشین باید دیده شود؟"""
    if not route_visible(car):
        return False

    return (
        AHEAD_ALPHA > 0
        or car.state in ("preview", "arrived")
        or k < car.seg
    )
