import asyncio
import resource
import sys
import time

sys.path.append("../fastcrawler")

from fastcrawler import (
    BaseModel,
    Process,
    Depends,
    Spider,
    XPATHField,
)  # noqa: E402


class PersonData(BaseModel):
    name: str = XPATHField(query="//td[1]", extract="text")
    age: int = XPATHField(query="//td[2]", extract="text")


class PersonPage(BaseModel):
    person: list[PersonData] = XPATHField(query="//table//tr", many=True)


def get_urls(count=200):
    return {f"http://localhost:8000/{id}" for id in range(count)}


class GetUrl:
    def __init__(self, count):
        self.urls = get_urls(count)

    def __call__(self, *args, **kwargs):
        return self.urls


class MySpider(Spider):
    engine_request_limit = 20
    data_model = PersonPage
    start_url = Depends(get_urls)
    batch_size = 50

    async def save(self, all_data: PersonPage):
        ...


async def start_fast(request_count, concurrent_request):
    spider = MySpider()
    spider.start_url = Depends(GetUrl(request_count))
    spider.engine_request_limit = concurrent_request
    crawler = Process(spider)
    await crawler.start(silent=False)


def profiler(request_count=200, concurrent_request=20):
    start_time = time.time()
    asyncio.run(start_fast(request_count, concurrent_request))
    end_time = time.time()
    mem_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    return end_time - start_time, mem_usage
