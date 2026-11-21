import asyncio
import os
from time import monotonic

import psutil


class CPUHealth:
    def __init__(self, settings):
        self.settings = settings
        self.cpu_percent = 0.0
        self.high_since = None
        self.unhealthy = False
        self.process = psutil.Process()
        self.process.cpu_percent()

    def observe(self, percent, now=None):
        now = monotonic() if now is None else now
        self.cpu_percent = percent
        if percent > self.settings.cpu_threshold:
            if self.high_since is None:
                self.high_since = now
            if now - self.high_since >= self.settings.cpu_high_seconds:
                # Render가 연속 60초 실패를 관측하도록 프로세스 재시작 전까지 유지한다.
                self.unhealthy = True
        else:
            self.high_since = None

    async def monitor(self):
        from pathlib import Path
        cpus = 1.0
        try:
            quota, period = Path("/sys/fs/cgroup/cpu.max").read_text().split()
            cpus = float(quota) / float(period) if quota != "max" else float(len(os.sched_getaffinity(0)))
        except (OSError, ValueError, AttributeError):
            cpus = float(os.cpu_count() or 1)
        while True:
            self.observe(self.process.cpu_percent() / max(cpus, 0.01))
            await asyncio.sleep(self.settings.cpu_sample_seconds)
