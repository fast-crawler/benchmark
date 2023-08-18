import csv
import resource
import time

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings


class MySpider(scrapy.Spider):
    name = "local"
    start_urls = [f"http://localhost:8000/{id}" for id in range(200)]
    crawled_count = 0

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


def profiler():
    start_time = time.time()

    my_settings = Settings()
    my_settings.set("CONCURRENT_REQUESTS", 20)

    process = CrawlerProcess(settings=my_settings)
    process.crawl(MySpider)
    process.start()

    end_time = time.time()
    mem_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(f"Time taken: {end_time - start_time} seconds")
    print(f"Memory used: {mem_usage} kilobytes")
    return end_time - start_time, mem_usage
