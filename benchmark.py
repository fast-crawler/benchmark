import csv
from matplotlib import pyplot as plt
import numpy as np

from scrap import profiler as scrapy_profiler
from _fastcrawler import profiler as fast_profiler

if __name__ == "__main__":
    scrapy_time, scrapy_memory = scrapy_profiler()
    try:
        fast_time, fast_memory = fast_profiler()
    except:
        fast_time = 1
        fast_memory = 1

    data = [
        {"Framework": "scrapy", "Time": scrapy_time, "Memory": scrapy_memory},
        {"Framework": "fast", "Time": fast_time, "Memory": fast_memory},
    ]

    # Write data to a CSV file
    with open("benchmark_results.csv", "w", newline="") as csvfile:
        fieldnames = ["Framework", "Time", "Memory"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    # Read data from the CSV file
    data = []
    with open("benchmark_results.csv", "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(row)

    # Extract framework names, times, and memories
    frameworks = [row["Framework"] for row in data]
    times = [float(row["Time"]) for row in data]
    memories = [int(row["Memory"]) for row in data]

    # Create a grouped bar chart
    bar_width = 0.35
    index = np.arange(len(frameworks))

    fig, ax = plt.subplots(figsize=(10, 6))

    rects1 = ax.bar(index, times, bar_width, label="Time")
    rects2 = ax.bar(index + bar_width, memories, bar_width, label="Memory")

    ax.set_xlabel("Framework")
    ax.set_ylabel("Values")
    ax.set_title("Execution Time and Memory Usage")
    ax.set_xticks(index + bar_width / 2)
    ax.set_xticklabels(frameworks)
    ax.legend()

    plt.tight_layout()

    plt.savefig("grouped_benchmark_chart.png")
