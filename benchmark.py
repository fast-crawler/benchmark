from scrapy.crawler import CrawlerProcess
from scrapy.spiderloader import SpiderLoader
from scrapy.utils.project import get_project_settings
from memory_profiler import profile
import time

@profile
def benchmark(spider_list: list[str]):
    settings = get_project_settings()
    spider_loader = SpiderLoader(settings)
    process = CrawlerProcess(get_project_settings()) 
    for spider in spider_list:
        spider = spider_loader.load(spider)
        process.crawl(spider)
        process.start()


start = time.perf_counter()
# spider_list = spider_loader.list()
spider_list = ['mopon', 'offch', 'takhfifan', 'digikala-products', 'digistyle-products'
            #    'digikalajet-products', 'snappexpress-products', 'snappfood-products',
               ]
benchmark(spider_list)
end = time.perf_counter()

print(f"Execution Time: {end - start} seconds")