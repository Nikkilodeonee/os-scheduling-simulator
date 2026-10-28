"""Command-line input, reproducible exports, and optional plotting."""

import argparse
import csv
import json
from dataclasses import asdict
from pathlib import Path

from .core import Process, Schedule, fcfs, generate_processes, round_robin, sjf


def read_workload(path: Path) -> list[Process]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["pid", "arrival_time", "burst_time"]:
            raise ValueError("CSV header must be pid,arrival_time,burst_time")
        items = []
        for line, row in enumerate(reader, 2):
            try:
                if None in row:
                    raise ValueError("too many columns")
                items.append(Process(*(int(row[k]) for k in reader.fieldnames)))
            except (ValueError, TypeError) as exc:
                raise ValueError(f"invalid process on CSV line {line}: {exc}") from exc
    if not items:
        raise ValueError("CSV workload must contain at least one process")
    return items


def export_results(
    output: Path, workload: list[Process], schedules: list[Schedule], parameters: dict
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    with (output / "workload.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["pid", "arrival_time", "burst_time"])
        writer.writeheader()
        writer.writerows(asdict(p) for p in workload)
    with (output / "processes.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["algorithm", *asdict(schedules[0].processes[0])]
        )
        writer.writeheader()
        for schedule in schedules:
            writer.writerows(
                {"algorithm": schedule.algorithm, **asdict(p)} for p in schedule.processes
            )
    with (output / "timeline.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["algorithm", "pid", "start", "end"])
        writer.writeheader()
        for schedule in schedules:
            writer.writerows(
                {"algorithm": schedule.algorithm, **asdict(s)} for s in schedule.timeline
            )
    report = {
        "schema_version": 1,
        "parameters": parameters,
        "metrics": {s.algorithm: s.metrics for s in schedules},
    }
    (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def plot_results(schedules: list[Schedule], output: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    with plt.rc_context({"font.family": "DejaVu Sans", "svg.hashsalt": "cpu-scheduling"}):
        fig, axes = plt.subplots(2, 1, figsize=(11, 7), layout="constrained")
        colors = ["#2563eb", "#0f766e", "#d97706"]
        labels = [s.algorithm for s in schedules]
        for i, (schedule, color) in enumerate(zip(schedules, colors, strict=True)):
            for slot in schedule.timeline:
                axes[0].broken_barh(
                    [(slot.start, slot.end - slot.start)],
                    (i - 0.3, 0.6),
                    facecolors=color,
                    edgecolors="white",
                    linewidth=0.5,
                )
                if len(schedule.timeline) <= 25:
                    axes[0].text(
                        (slot.start + slot.end) / 2,
                        i,
                        f"P{slot.pid}",
                        ha="center",
                        va="center",
                        color="white",
                        fontsize=8,
                    )
        axes[0].set(
            yticks=range(len(labels)),
            yticklabels=labels,
            xlabel="Simulation time",
            title="Execution timeline · gaps indicate an idle CPU",
        )
        names = ["average_waiting_time", "average_turnaround_time", "average_response_time"]
        for i, (schedule, color) in enumerate(zip(schedules, colors, strict=True)):
            positions = [x + (i - 1) * 0.25 for x in range(3)]
            bars = axes[1].bar(
                positions,
                [schedule.metrics[n] for n in names],
                0.25,
                label=schedule.algorithm,
                color=color,
            )
            axes[1].bar_label(bars, fmt="%.2f", padding=3, fontsize=9)
        axes[1].set(
            xticks=range(3),
            xticklabels=["Waiting", "Turnaround", "Response"],
            ylabel="Mean time (simulation units)",
            title="Same workload, different tradeoffs",
        )
        axes[1].margins(y=0.2)
        axes[1].legend(frameon=False)
        for ax in axes:
            ax.spines[["top", "right"]].set_visible(False)
        fig.savefig(output, metadata={"Date": None})
        plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare FCFS, SJF, and Round Robin on one workload."
    )
    parser.add_argument("--input", type=Path, help="CSV with pid,arrival_time,burst_time")
    parser.add_argument("--count", type=int, default=25)
    parser.add_argument("--arrival-max", type=int, default=50)
    parser.add_argument("--burst-max", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--quantum", type=int, default=2)
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    parser.add_argument(
        "--plot", action="store_true", help="save comparison.svg (requires plotting extra)"
    )
    args = parser.parse_args(argv)
    try:
        workload = (
            read_workload(args.input)
            if args.input
            else generate_processes(
                args.count, (0, args.arrival_max), (1, args.burst_max), args.seed
            )
        )
        schedules = [fcfs(workload), sjf(workload), round_robin(workload, args.quantum)]
        parameters = {
            "source": str(args.input) if args.input else "generated",
            "quantum": args.quantum,
            "seed": None if args.input else args.seed,
            "count": len(workload),
            "arrival_range": None if args.input else [0, args.arrival_max],
            "burst_range": None if args.input else [1, args.burst_max],
        }
        export_results(args.output_dir, workload, schedules, parameters)
        if args.plot:
            plot_results(schedules, args.output_dir / "comparison.svg")
    except ImportError:
        parser.error('plotting requires: python -m pip install ".[plot]"')
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(f"{'Algorithm':<15} {'Mean wait':>12} {'Turnaround':>12} {'Response':>12}")
    for schedule in schedules:
        m = schedule.metrics
        print(
            f"{schedule.algorithm:<15} {m['average_waiting_time']:>12.2f} "
            f"{m['average_turnaround_time']:>12.2f} {m['average_response_time']:>12.2f}"
        )
    print(f"Results saved to {args.output_dir}")
    return 0
