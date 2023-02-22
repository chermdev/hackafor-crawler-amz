from hackafor_crawler_amz import crawler
from rich.console import Console
import asyncio


console = Console()

URLS = ("https://a.co/d/geQhA2O",
        "https://a.co/d/d650BRG",
        "https://a.co/d/5GjLWQx",
        "https://a.co/d/cewgOFz",
        "https://a.co/d/3h52kBL")


def test_crawler_lxml():
    data = asyncio.run(crawler.scrap_urls(URLS, method="lxml"))
    console.print(data)


def test_crawler_playwright():
    data = asyncio.run(crawler.scrap_urls(URLS, method="playwright"))
    console.print(data)
