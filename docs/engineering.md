# Engineering notes

## Model and metrics

The simulation clock starts at 0. A process is ready at its arrival time.
Execution is a sequence of half-open intervals [start, end). Gaps are idle CPU time.

For each process:

- Turnaround = completion − arrival.
- Waiting = turnaround − burst, including all waits between Round Robin slices.
- Response = first start − arrival.

Utilization = total executed burst / last completion, including initial idle time.
Throughput = completed process count / last completion. Makespan is the last
completion measured from time 0. An empty library workload produces zero metrics;
the CLI requires a non-empty workload.

## Policy semantics

FCFS orders equal arrivals by PID. SJF chooses only jobs that have arrived and
never interrupts a running burst. Equal ready bursts use arrival then PID.
Round Robin starts in arrival/PID order; arrivals during or exactly at the end of
a slice enter the ready queue before the interrupted job is appended.

Inputs are frozen dataclasses. Algorithms return separate frozen result objects,
sorted by PID, plus a timeline in execution order. Reusing one input list is safe.

## Complexity

Let n be the number of jobs and s the number of Round Robin execution slices.

| Algorithm | Simulation time, including input/result sorting | Space, including returned timeline |
| --- | --- | --- |
| FCFS | O(n log n) | O(n) |
| SJF | O(n log n), including heap operations | O(n) |
| Round Robin | O(n log n + s) | O(n + s) |

All policies jump over idle intervals. Very small quanta and huge burst lengths
can create large Round Robin timelines. The CLI is designed for educational
workloads; it does not impose a job or slice limit.

Plotting/export costs are separate. These bounds are implementation analysis,
not measured speedup claims.

## Verification

The suite includes exact expected schedules calculated by hand, workload
immutability, RR equivalence to FCFS for a sufficiently large quantum, and
randomized invariants across 30 seeds. Each job must receive exactly its requested
CPU time; slices cannot overlap; response and waiting must be non-negative.

CSV input is validated before the output directory is created. CLI failures use
exit status 2 with a concise message. Output names are replaced when rerunning in
the same directory; use a separate output directory to preserve prior runs.
Exports are not atomic; an I/O or plotting failure can leave partial output.

A fixed seed repeats a generated workload on the same Python implementation.
For long-term replay, retain the exported workload CSV and quantum rather than
depending solely on random-number generator implementation details.

## Portfolio and interview talking points

CV wording, after reviewing the implementation:

> Extended an Operating Systems scheduling simulator into a Python CLI comparing
> FCFS, heap-based SJF and Round Robin, with immutable data models, reproducible
> CSV/JSON experiments, execution timelines and 19 automated regression tests.

Be ready to explain why shortest ready burst differs from globally shortest
burst, why waiting and response diverge under preemption, and how Round Robin's
quantum changes responsiveness. Use the checked-in four-process example to walk
through the timeline without relying on a screenshot.

Original scope: FCFS/SJF generation and a waiting-time chart. Extensions:
Round Robin, immutable models, event jumps, heap-based selection, additional
metrics, CLI/CSV input, reports, packaging, regression tests and CI.

## Background

- [OSTEP: CPU Scheduling](https://pages.cs.wisc.edu/~remzi/OSTEP/cpu-sched.pdf)
- [Python heapq documentation](https://docs.python.org/3/library/heapq.html)
