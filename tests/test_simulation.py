"""Hand-worked schedules, invariants, and the real CLI."""

import contextlib
import csv
import io
import json
import random
import subprocess
import sys
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from scheduling_simulator import Process, fcfs, generate_processes, round_robin, sjf
from scheduling_simulator.cli import main, read_workload


class SchedulingTests(unittest.TestCase):
    def setUp(self):
        self.jobs = [Process(0, 0, 8), Process(1, 0, 4), Process(2, 1, 2), Process(3, 2, 1)]

    def test_fcfs_hand_worked(self):
        result = fcfs(self.jobs)
        self.assertEqual([p.waiting_time for p in result.processes], [0, 8, 11, 12])
        self.assertEqual(result.metrics["average_waiting_time"], 7.75)

    def test_sjf_hand_worked(self):
        result = sjf(self.jobs)
        self.assertEqual([s.pid for s in result.timeline], [1, 3, 2, 0])
        self.assertEqual([p.waiting_time for p in result.processes], [7, 0, 4, 2])
        self.assertEqual(result.metrics["average_waiting_time"], 3.25)

    def test_round_robin_hand_worked(self):
        result = round_robin(self.jobs, quantum=2)
        self.assertEqual([s.pid for s in result.timeline], [0, 1, 2, 3, 0, 1, 0, 0])
        self.assertEqual([p.completion_time for p in result.processes], [15, 11, 6, 7])
        self.assertEqual([p.response_time for p in result.processes], [0, 2, 3, 4])

    def test_boundary_arrivals_precede_requeued_process(self):
        result = round_robin([Process(0, 0, 4), Process(1, 2, 1)], 2)
        self.assertEqual([s.pid for s in result.timeline], [0, 1, 0])

    def test_sjf_does_not_run_a_future_job(self):
        result = sjf([Process(0, 0, 10), Process(1, 1, 1)])
        self.assertEqual([s.pid for s in result.timeline], [0, 1])
        self.assertEqual(result.processes[1].waiting_time, 9)

    def test_sjf_is_nonpreemptive(self):
        result = sjf([Process(0, 0, 9), Process(1, 3, 1)])
        self.assertEqual([(s.start, s.end) for s in result.timeline], [(0, 9), (9, 10)])

    def test_idle_gaps_and_initial_idle_count_toward_utilization(self):
        for policy in (fcfs, sjf, round_robin):
            result = policy([Process(0, 100_000_000, 1), Process(1, 200_000_000, 1)])
            self.assertEqual(result.processes[1].start_time, 200_000_000)
            self.assertAlmostEqual(result.metrics["cpu_utilization"], 2 / 200_000_001)
            self.assertEqual(result.metrics["average_waiting_time"], 0)

    def test_ties_are_independent_of_input_order(self):
        jobs = [Process(9, 0, 1), Process(2, 0, 1), Process(5, 0, 1)]
        for policy in (fcfs, sjf, round_robin):
            self.assertEqual([s.pid for s in policy(jobs).timeline], [2, 5, 9])

    def test_inputs_are_immutable_and_reusable(self):
        before = list(self.jobs)
        first = fcfs(self.jobs)
        sjf(self.jobs)
        round_robin(self.jobs)
        self.assertEqual(first, fcfs(self.jobs))
        self.assertEqual(before, self.jobs)
        with self.assertRaises(FrozenInstanceError):
            self.jobs[0].burst_time = 100

    def test_large_quantum_matches_fcfs(self):
        self.assertEqual(fcfs(self.jobs).processes, round_robin(self.jobs, 100).processes)

    def test_empty_workload(self):
        for policy in (fcfs, sjf, round_robin):
            result = policy([])
            self.assertEqual(result.timeline, ())
            self.assertTrue(all(value == 0 for value in result.metrics.values()))

    def test_invalid_processes(self):
        for args in [(-1, 0, 1), (0, -1, 1), (0, 0, 0), (0, 0, 1.5), (True, 0, 1)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                Process(*args)

    def test_duplicate_ids_and_invalid_quantum(self):
        for policy in (fcfs, sjf, round_robin):
            with self.assertRaises(ValueError):
                policy([Process(0, 0, 1), Process(0, 1, 1)])
        for quantum in [0, -1, 1.5, True]:
            with self.assertRaises(ValueError):
                round_robin(self.jobs, quantum)

    def test_seed_is_local_and_reproducible(self):
        state = random.getstate()
        self.assertEqual(generate_processes(seed=42), generate_processes(seed=42))
        self.assertNotEqual(generate_processes(seed=42), generate_processes(seed=43))
        self.assertEqual(state, random.getstate())

    def test_generator_validation(self):
        for kwargs in [{"n": 0}, {"arrival_range": (5, 2)}, {"burst_range": (0, 5)}]:
            with self.assertRaises(ValueError):
                generate_processes(**kwargs)

    def test_schedule_invariants_across_random_workloads(self):
        for seed in range(30):
            jobs = generate_processes(20, seed=seed)
            for policy in (fcfs, sjf, round_robin):
                result = policy(jobs)
                self.assertEqual(
                    sum(s.end - s.start for s in result.timeline), sum(p.burst_time for p in jobs)
                )
                for left, right in zip(result.timeline, result.timeline[1:], strict=False):
                    self.assertLessEqual(left.end, right.start)
                for p in result.processes:
                    self.assertGreaterEqual(p.start_time, p.arrival_time)
                    self.assertEqual(p.waiting_time + p.burst_time, p.turnaround_time)
                    self.assertGreaterEqual(p.waiting_time, p.response_time)
                    self.assertEqual(
                        sum(s.end - s.start for s in result.timeline if s.pid == p.pid),
                        p.burst_time,
                    )


class CliTests(unittest.TestCase):
    def test_exports_are_reproducible_and_replayable(self):
        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stdout(io.StringIO()):
            root = Path(temporary)
            main(["--seed", "42", "--output-dir", str(root / "one")])
            main(["--seed", "42", "--output-dir", str(root / "two")])
            for name in ["summary.json", "processes.csv", "timeline.csv", "workload.csv"]:
                self.assertEqual(
                    (root / "one" / name).read_bytes(), (root / "two" / name).read_bytes()
                )
            main(["--input", str(root / "one/workload.csv"), "--output-dir", str(root / "replay")])
            original = json.loads((root / "one/summary.json").read_text())
            replay = json.loads((root / "replay/summary.json").read_text())
            self.assertEqual(original["metrics"], replay["metrics"])
            with (root / "one/processes.csv").open(newline="") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), 75)

    def test_malformed_csv(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "input.csv"
            for content in [
                "",
                "id,arrival,burst\n0,0,1\n",
                "pid,arrival_time,burst_time\n0,x,1\n",
                "pid,arrival_time,burst_time\n0,0\n",
                "pid,arrival_time,burst_time\n0,0,1,extra\n",
            ]:
                path.write_text(content)
                with self.subTest(content=content), self.assertRaises(ValueError):
                    read_workload(path)

    def test_cli_rejects_bad_input_without_traceback(self):
        result = subprocess.run(
            [sys.executable, "main.py", "--quantum", "0"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("quantum", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
