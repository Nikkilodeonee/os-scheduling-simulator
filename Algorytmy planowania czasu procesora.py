import random
import numpy as np
import matplotlib.pyplot as plt


# Klasa reprezentująca proces
class Process:
    def __init__(self, pid, arrival_time, burst_time):
        self.pid = pid
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.start_time = 0
        self.completion_time = 0
        self.waiting_time = 0


# Generator procesów
def generate_processes(n=25, arrival_range=(0, 50), burst_range=(1, 10), seed=None):
    if seed is not None:
        random.seed(seed)
    processes = []
    for i in range(n):
        arrival = random.randint(*arrival_range)
        burst = random.randint(*burst_range)
        processes.append(Process(i, arrival, burst))
    return processes


# FCFS - First Come First Serve
def fcfs(processes):
    processes = sorted(processes, key=lambda p: p.arrival_time)
    current_time = 0
    for p in processes:
        if current_time < p.arrival_time:
            current_time = p.arrival_time
        p.start_time = current_time
        p.completion_time = current_time + p.burst_time
        p.waiting_time = p.start_time - p.arrival_time
        current_time = p.completion_time
    return sorted(processes, key=lambda p: p.pid)  # Sortowanie po PID


# SJF - Shortest Job First (niewywłaszczalny)
def sjf(processes):
    processes = sorted(processes, key=lambda p: (p.arrival_time, p.burst_time))
    completed = []
    current_time = 0
    ready_queue = []
    idx = 0
    while len(completed) < len(processes):
        while idx < len(processes) and processes[idx].arrival_time <= current_time:
            ready_queue.append(processes[idx])
            idx += 1
        if ready_queue:
            ready_queue.sort(key=lambda p: p.burst_time)
            p = ready_queue.pop(0)
            p.start_time = current_time
            p.completion_time = current_time + p.burst_time
            p.waiting_time = p.start_time - p.arrival_time
            current_time = p.completion_time
            completed.append(p)
        else:
            current_time += 1
    return sorted(completed, key=lambda p: p.pid)  # Sortowanie po PID


# Funkcja do obliczania średnich statystyk
def calculate_average_waiting_time(processes):
    return sum(p.waiting_time for p in processes) / len(processes)


# Wizualizacja wyników
def plot_results(fcfs_processes, sjf_processes):
    # Sortowanie procesów według PID przed tworzeniem wykresu
    fcfs_sorted = sorted(fcfs_processes, key=lambda p: p.pid)
    sjf_sorted = sorted(sjf_processes, key=lambda p: p.pid)

    labels = [f"P{p.pid}" for p in fcfs_sorted]
    fcfs_waiting = [p.waiting_time for p in fcfs_sorted]
    sjf_waiting = [p.waiting_time for p in sjf_sorted]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(x - width / 2, fcfs_waiting, width, label='FCFS', color='skyblue')
    ax.bar(x + width / 2, sjf_waiting, width, label='SJF', color='salmon')

    ax.set_ylabel('Czas oczekiwania')
    ax.set_title('Porównanie czasu oczekiwania: FCFS vs SJF (posortowane wg PID)')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45)
    ax.legend()

    # Dodanie wartości na słupkach
    for i in range(len(x)):
        ax.text(x[i] - width / 2, fcfs_waiting[i] + 0.2, f'{fcfs_waiting[i]:.1f}',
                ha='center', va='bottom', fontsize=8)
        ax.text(x[i] + width / 2, sjf_waiting[i] + 0.2, f'{sjf_waiting[i]:.1f}',
                ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()


# Główna funkcja symulacyjna
def main():
    processes = generate_processes(n=25, seed=42)
    fcfs_result = fcfs([Process(p.pid, p.arrival_time, p.burst_time) for p in processes])
    sjf_result = sjf([Process(p.pid, p.arrival_time, p.burst_time) for p in processes])

    print("Średni czas oczekiwania FCFS:", calculate_average_waiting_time(fcfs_result))
    print("Średni czas oczekiwania SJF:", calculate_average_waiting_time(sjf_result))

    plot_results(fcfs_result, sjf_result)


if __name__ == "__main__":
    main()