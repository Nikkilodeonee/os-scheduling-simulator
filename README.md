# CPU Scheduling Simulation: FCFS vs SJF

![Python](https://img.shields.io/badge/Python-3.10-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

Coursework project from Operating Systems: a small simulator that compares **FCFS** and **non-preemptive SJF** on randomly generated processes.

## Overview

The program generates processes with random arrival and burst times, computes waiting times, and plots a per-process comparison with Matplotlib.

## Algorithms

### FCFS (First Come First Serve)

Processes run in arrival order, without preemption. Simple, but a long job can delay shorter ones.

### SJF (Shortest Job First, non-preemptive)

Among processes that have already arrived, the shortest burst runs next. This usually lowers average waiting time, but it needs known burst lengths and can starve long jobs.

## Run

```bash
pip install -r requirements.txt
python main.py
```

This prints average waiting times and opens a bar chart of FCFS vs SJF waiting time for each process.

Default experiment: 25 processes, arrival in `[0, 50]`, burst in `[1, 10]`, seed `42`. Change those values in `main()`.

```python
processes = generate_processes(n=50, arrival_range=(0, 100), burst_range=(1, 20), seed=123)
```

## Example result

| Algorithm | Average waiting time |
|-----------|----------------------|
| FCFS      | 41.52                |
| SJF       | 24.28                |

<img width="1495" height="739" alt="FCFS vs SJF waiting times" src="https://github.com/user-attachments/assets/42db1d37-4692-4263-90f6-5bafc3ee7c84" />

SJF wins on average waiting time here. FCFS is simpler. Real OS schedulers rarely use pure SJF because burst time is not known in advance.

## License

MIT. Author: [Roman Sushkin](https://github.com/Nikkilodeonee)
