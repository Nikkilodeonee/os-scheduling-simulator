# CPU Scheduling Simulation: FCFS vs SJF

![Python](https://img.shields.io/badge/Python-3.10-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

## Overview
This project implements and compares two fundamental CPU scheduling algorithms:
- **FCFS (First Come First Serve)**
- **SJF (Shortest Job First, non-preemptive)**

The program simulates process scheduling with randomly generated processes, computes waiting times, and visualizes results using **Matplotlib**.

---

## Key Features
- Simulation of process scheduling with random arrival & burst times.
- Modular object-oriented design for clarity and extension.
- Computation and visualization of per-process and average waiting times.
- Side-by-side **bar chart** comparison of FCFS vs SJF waiting times.
- Reproducible experiments with configurable random seed.

---

## Algorithms Explained

### FCFS (First Come First Serve)
- **Description**: Processes are executed in order of arrival, without preemption.  
- **Pros**: Simple, fair order handling.  
- **Cons**: Long jobs can delay shorter ones → higher average waiting time.  

### SJF (Shortest Job First, Non-Preemptive)
- **Description**: The process with the smallest burst time among arrived processes runs next.  
- **Pros**: Minimizes average waiting time (theoretically optimal).  
- **Cons**: Requires knowing burst durations in advance, can starve long jobs.  

---

## Code Structure
- **`Process` class** – represents a single process (arrival, burst, waiting time, etc.).  
- **`generate_processes()`** – creates random processes with given parameters.  
- **`fcfs()` & `sjf()`** – core scheduling simulators.  
- **`calculate_average_waiting_time()`** – evaluates efficiency.  
- **`plot_results()`** – Matplotlib visualization routine.  

---

## Getting Started

### Install dependencies
```bash
pip install numpy matplotlib
```
Run the simulation
```bash
python main.py
```
This will:

Print the average waiting times for both algorithms in the console.

Show a bar chart comparing FCFS and SJF waiting times.

### Customization
You can modify:

Number of processes (n)

Arrival time range

Burst time range

Random seed (for reproducibility)

## Example:
```python
processes = generate_processes(n=50, arrival_range=(0, 100), burst_range=(1, 20), seed=123)
```
Results
From experiments with 25 processes (arrival ∈ [0,50], burst ∈ [1,10]):

| Algorithm | Average Waiting Time |
|-----------|-----------------------|
| FCFS      | 41.52                 |
| SJF       | 24.28                 |

Example Output
(generated with Matplotlib)
<img width="1495" height="739" alt="image" src="https://github.com/user-attachments/assets/42db1d37-4692-4263-90f6-5bafc3ee7c84" />

## Conclusion
SJF consistently outperforms FCFS in average waiting time.

FCFS remains simpler and fair, but less efficient in mixed workloads.

SJF is theoretically optimal but impractical in real OS scheduling without burst-time knowledge.

## License
This project is licensed under the MIT License.

## Author
Nikkilodeonee
