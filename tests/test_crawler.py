from hackafor_crawler_amz import crawler
from rich.console import Console

console = Console()

URLS = ("https://a.co/d/geQhA2O",
        "https://a.co/d/d650BRG",
        "https://a.co/d/5GjLWQx",
        "https://a.co/d/cewgOFz",
        "https://a.co/d/3h52kBL")


def test_crawler():
    console.print(crawler.scrap_urls(URLS))

# urls = ["https://a.co/d/geQhA2O", "https://a.co/d/d650BRG",
#         "https://a.co/d/5GjLWQx", "https://a.co/d/cewgOFz"]
# print(crawler.scrap_urls(urls))
