import csv
from matplotlib import pyplot as plt

from scrap import profiler as scrapy_profiler
from _fastcrawler import profiler as fast_profiler


def benchmark():
    request_counts = [10, 20, 100, 200, 300, 400]
    data = []

    for request_count in request_counts:
        scrapy_time, scrapy_memory = scrapy_profiler()
        fast_time, fast_memory = fast_profiler()
        data.append(
            {
                "RequestCount": request_count,
                "scrapy_time": scrapy_time,
                "scrapy_memory": scrapy_memory,
                "fast_time": fast_time,
                "fast_memory": fast_memory,
            }
        )

    # Write data to a CSV file

    # Extract performance metrics
    request_counts = [int(row["RequestCount"]) for row in data]
    scrapy_times = [float(row["scrapy_time"]) for row in data]
    fast_times = [float(row["fast_time"]) for row in data]
    scrapy_memories = [int(row["scrapy_memory"]) for row in data]
    fast_memories = [int(row["fast_memory"]) for row in data]

    # Create subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))

    bar_width = 0.35
    index = range(len(request_counts))

    ax1.bar(index, scrapy_times, bar_width, label="scrapy")
    ax1.bar([i + bar_width for i in index], fast_times, bar_width, label="fast")
    ax1.set_xticks([i + bar_width / 2 for i in index])
    ax1.set_xticklabels(request_counts)
    ax1.set_xlabel("Request Count")
    ax1.set_ylabel("Time (seconds)")
    ax1.set_title("Response Time vs. Request Count")
    ax1.legend()

    ax2.bar(index, scrapy_memories, bar_width, label="scrapy")
    ax2.bar([i + bar_width for i in index], fast_memories, bar_width, label="fast")
    ax2.set_xticks([i + bar_width / 2 for i in index])
    ax2.set_xticklabels(request_counts)
    ax2.set_xlabel("Request Count")
    ax2.set_ylabel("Memory Usage (kilobytes)")
    ax2.set_title("Memory Usage vs. Request Count")
    ax2.legend()

    plt.tight_layout()

    plt.savefig("performance_benchmark_barchart.png")


if __name__ == "__main__":
    benchmark()
