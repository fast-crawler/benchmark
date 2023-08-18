# Justfile

default:
    help

# Help task to display available tasks
help:
    @echo "Available tasks:"
    @echo "  install       - Install the benchmark requirement."
    @echo "  sketch       - create sketch report for compair scrapy and fastcrawler framework"

install :
    pip install -r requirements.txt --no-cache-dir

sketch:
    python benchmark.py
