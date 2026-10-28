"""Pure scheduling algorithms. All times are integer simulation units."""

from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass
from heapq import heappop, heappush
from random import Random
from statistics import mean


def _integer(value: int, name: str, minimum: int = 0) -> None:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")


@dataclass(frozen=True)
class Process:
    pid: int
    arrival_time: int
    burst_time: int

    def __post_init__(self) -> None:
        _integer(self.pid, "pid")
        _integer(self.arrival_time, "arrival_time")
        _integer(self.burst_time, "burst_time", 1)


@dataclass(frozen=True)
class Slice:
    pid: int
    start: int
    end: int


@dataclass(frozen=True)
class ProcessResult:
    pid: int
    arrival_time: int
    burst_time: int
    start_time: int
    completion_time: int
    waiting_time: int
    turnaround_time: int
    response_time: int


@dataclass(frozen=True)
class Schedule:
    algorithm: str
    processes: tuple[ProcessResult, ...]
    timeline: tuple[Slice, ...]

    @property
    def metrics(self) -> dict[str, float]:
        finish = max((p.completion_time for p in self.processes), default=0)
        busy = sum(p.burst_time for p in self.processes)
        return {
            "average_waiting_time": mean(p.waiting_time for p in self.processes)
            if self.processes
            else 0.0,
            "average_turnaround_time": mean(p.turnaround_time for p in self.processes)
            if self.processes
            else 0.0,
            "average_response_time": mean(p.response_time for p in self.processes)
            if self.processes
            else 0.0,
            "cpu_utilization": busy / finish if finish else 0.0,
            "throughput": len(self.processes) / finish if finish else 0.0,
            "makespan": finish,
        }


def _workload(processes: Iterable[Process]) -> list[Process]:
    items = list(processes)
    if any(not isinstance(p, Process) for p in items):
        raise ValueError("workload must contain Process objects")
    if len({p.pid for p in items}) != len(items):
        raise ValueError("process IDs must be unique")
    return sorted(items, key=lambda p: (p.arrival_time, p.pid))


def _result(name: str, items: list[Process], timeline: list[Slice]) -> Schedule:
    starts: dict[int, int] = {}
    finishes: dict[int, int] = {}
    for slot in timeline:
        starts.setdefault(slot.pid, slot.start)
        finishes[slot.pid] = slot.end
    results = tuple(
        ProcessResult(
            p.pid,
            p.arrival_time,
            p.burst_time,
            starts[p.pid],
            finishes[p.pid],
            finishes[p.pid] - p.arrival_time - p.burst_time,
            finishes[p.pid] - p.arrival_time,
            starts[p.pid] - p.arrival_time,
        )
        for p in sorted(items, key=lambda p: p.pid)
    )
    return Schedule(name, results, tuple(timeline))


def fcfs(processes: Iterable[Process]) -> Schedule:
    """First come, first served; equal arrivals use ascending PID."""
    items = _workload(processes)
    now = 0
    timeline = []
    for p in items:
        now = max(now, p.arrival_time)
        timeline.append(Slice(p.pid, now, now + p.burst_time))
        now += p.burst_time
    return _result("FCFS", items, timeline)


def sjf(processes: Iterable[Process]) -> Schedule:
    """Non-preemptive shortest job first; ties use arrival, then PID."""
    items = _workload(processes)
    ready: list[tuple[int, int, int, Process]] = []
    timeline = []
    index = now = 0
    while index < len(items) or ready:
        if not ready:
            now = max(now, items[index].arrival_time)
        while index < len(items) and items[index].arrival_time <= now:
            p = items[index]
            heappush(ready, (p.burst_time, p.arrival_time, p.pid, p))
            index += 1
        p = heappop(ready)[3]
        timeline.append(Slice(p.pid, now, now + p.burst_time))
        now += p.burst_time
    return _result("SJF", items, timeline)


def round_robin(processes: Iterable[Process], quantum: int = 2) -> Schedule:
    """Arrivals at a slice boundary enter before the preempted process."""
    _integer(quantum, "quantum", 1)
    items = _workload(processes)
    remaining = {p.pid: p.burst_time for p in items}
    ready: deque[Process] = deque()
    timeline = []
    index = now = 0
    while index < len(items) or ready:
        if not ready:
            now = max(now, items[index].arrival_time)
        while index < len(items) and items[index].arrival_time <= now:
            ready.append(items[index])
            index += 1
        p = ready.popleft()
        duration = min(quantum, remaining[p.pid])
        timeline.append(Slice(p.pid, now, now + duration))
        now += duration
        remaining[p.pid] -= duration
        while index < len(items) and items[index].arrival_time <= now:
            ready.append(items[index])
            index += 1
        if remaining[p.pid]:
            ready.append(p)
    return _result("Round Robin", items, timeline)


def generate_processes(
    n: int = 25,
    arrival_range: tuple[int, int] = (0, 50),
    burst_range: tuple[int, int] = (1, 10),
    seed: int = 42,
) -> list[Process]:
    _integer(n, "process count", 1)
    for name, bounds, minimum in (
        ("arrival", arrival_range, 0),
        ("burst", burst_range, 1),
    ):
        if len(bounds) != 2:
            raise ValueError(f"{name} range must have two bounds")
        for bound in bounds:
            _integer(bound, f"{name} bound", minimum)
        if bounds[0] > bounds[1]:
            raise ValueError(f"{name} minimum cannot exceed maximum")
    rng = Random(seed)
    return [Process(i, rng.randint(*arrival_range), rng.randint(*burst_range)) for i in range(n)]
