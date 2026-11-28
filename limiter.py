"""
limiter.py  -  قفل دقیق FPS روی عدد ثابت (60).
"""

import time
import pygame


class FrameLimiter:
    """
    سرعت بازی را دقیقاً روی FPS ثابت نگه می‌دارد.

    چرا clock.tick(60) کافی نبود؟ چون Pygame زمان هر فریم را به میلی‌ثانیه‌ی
    صحیح گرد می‌کند: 1000 / 60 = 16.67 ولی 16 می‌شود، یعنی 62.5 فریم در ثانیه.
    اینجا زمان را اعشاری و با ساعت دقیق (perf_counter) حساب می‌کنیم.
    """

    def __init__(self, fps):
        self.frame_time = 1.0 / fps        # مدت هر فریم به ثانیه (اعشاری)
        now = time.perf_counter()
        self.next_frame = now              # زمانی که فریم بعدی باید شروع شود
        self.last = now                    # زمان شروع فریم قبل
        self.history = []                  # مدت چند فریم آخر، برای نمایش FPS

    def wait(self):
        """تا رسیدن زمان فریم بعدی صبر می‌کند و مدت فریم را (میلی‌ثانیه) برمی‌گرداند."""
        self.next_frame += self.frame_time

        # بیشتر زمان را با خواب سبک (بدون مصرف CPU) می‌گذرانیم،
        # دو میلی‌ثانیه‌ی آخر را با انتظار دقیق تا زمان فریم بعدی برسد
        remaining = self.next_frame - time.perf_counter()
        if remaining > 0.003:
            pygame.time.delay(int((remaining - 0.002) * 1000))

        while time.perf_counter() < self.next_frame:
            pass

        now = time.perf_counter()

        if now - self.next_frame > 5 * self.frame_time:
            # اگر خیلی عقب افتادیم، دوباره هماهنگ شو
            self.next_frame = now

        frame_seconds = now - self.last
        self.last = now

        self.history.append(frame_seconds)

        if len(self.history) > 60:
            # فقط ۶۰ فریم آخر را نگه دار
            self.history.pop(0)

        return frame_seconds * 1000

    def get_fps(self):
        """میانگین FPS در ۶۰ فریم آخر."""
        if not self.history:
            return 0.0

        return len(self.history) / sum(self.history)
