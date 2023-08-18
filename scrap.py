import csv
import resource
import time

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings


def get_url(count=200):
    return {f"http://localhost:8000/{id}" for id in range(200)}


class MySpider(scrapy.Spider):
    name = "local"
    start_urls = get_url()
    crawled_count = 0
    max_request = 200

    def parse(self, response):
        for person in response.css("table tr"):
            yield {
                "name": str(person.css("td:nth-child(1)::text").get()),
                "age": int(person.css("td:nth-child(2)::text").get()),
            }
            self.crawled_count += 1
            if self.crawled_count >= 200:
                self.logger.info("Reached 200 IDs, stopping the spider.")
                return


def profiler(request_count=200, concurrent_request=20):
    start_time = time.time()

    my_settings = Settings()
    my_settings.set("CONCURRENT_REQUESTS", concurrent_request)
    my_settings.set("LOG_LEVEL", "ERROR")
    my_settings.set("LOG_ENABLED", True)

    process = CrawlerProcess(settings=my_settings)
    process.crawl(MySpider)
    process.start()
    end_time = time.time()
    mem_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return end_time - start_time, mem_usage
