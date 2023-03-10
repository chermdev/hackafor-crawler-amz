import httpx
import random
import asyncio
from lxml import html
from typing import Union
from pathlib import Path
from playwright.async_api import Page
from playwright.async_api import Browser
from playwright.async_api import async_playwright
from playwright._impl._api_types import Error
from playwright._impl._api_types import TimeoutError


PRODUCT_TITLE = "//span[@id='productTitle']"
PRODUCT_PRICE = "//*[@id='corePrice_desktop']//span[contains(@class,'a-price')]/span[1]"
PRODUCT_PRICE_WHOLE = "//span[@class='a-price-whole']"
PRODUCT_PRICE_FRACTION = "//span[@class='a-price-fraction']"
PRODUCT_IMAGE_URL = "//div[@id='imgTagWrapperId']/img"
PRODUCT_CATEGORIES = "//div[@id='wayfinding-breadcrumbs_container']//a"


def timeit(func):

    async def wrapper(*args, **kwargs):
        import time
        try:
            start_time = time.time()
            return await func(*args, **kwargs)
        finally:
            end_time = time.time()
            print(f"{func.__name__}: ", end_time-start_time)

    return wrapper


class ElementNotFound(Exception):
    ...


def find_lxml_element(doc, locator):
    results = doc.xpath(locator)
    if not results:
        raise ElementNotFound(f"Lxml error: Element not found {locator}")
    return results[0]


async def automation_amz_product_lxml(client, url: str, lang: str, user_agent: str):
    """ Lxml automation to get product data """
    try:
        headers = {"User-Agent": user_agent,
                   "Accept-Language": lang}
        res = await client.get(url, headers=headers, follow_redirects=True)
        content_html = res.text
        doc = html.fromstring(content_html)
        title = find_lxml_element(doc, PRODUCT_TITLE).text.strip()
        try:
            product_price = find_lxml_element(doc, PRODUCT_PRICE)
            price_str = product_price.text.strip()
        except ElementNotFound:
            product_price_whole = find_lxml_element(
                doc, PRODUCT_PRICE_WHOLE).text.strip()
            product_price_fraction = find_lxml_element(
                doc,
                PRODUCT_PRICE_FRACTION).text.strip()
            price_str = product_price_whole + "." + product_price_fraction
        price = float(price_str.replace("$", "").replace(",", ""))
        img_url = find_lxml_element(doc, PRODUCT_IMAGE_URL).attrib["src"]
        categories = [ele.text.strip()
                      for ele in doc.xpath(PRODUCT_CATEGORIES)]
        return {
            "full_name": title,
            "price": price,
            "image": img_url,
            "categories": categories
        }
    except Exception as err:
        return {
            "error": err
        }


async def automation_amz_product(page: Page, url: str):
    """ Plawyright automation to get product data """
    try:
        await page.goto(url)
        await page.wait_for_selector(PRODUCT_TITLE, timeout=5000)
        title = str(await page.inner_text(PRODUCT_TITLE, timeout=2000))
        price_ele = page.locator(PRODUCT_PRICE)
        if await price_ele.is_visible(timeout=1000):
            price_str = await page.text_content(PRODUCT_PRICE, timeout=2000)
        else:
            price_whole = str(await page.text_content(PRODUCT_PRICE_WHOLE, timeout=2000))
            price_fraction = str(await page.inner_text(PRODUCT_PRICE_FRACTION, timeout=2000))
            price_str = price_whole + price_fraction
        price = float(price_str.replace("$", "").replace(",", ""))
        img_url = await page.get_attribute(PRODUCT_IMAGE_URL, 'src', timeout=2000)
        categories = await page.locator(PRODUCT_CATEGORIES).all_inner_texts()
        return {
            "full_name": title.replace('\n', ''),
            "price": price,
            "image": img_url,
            "categories": categories
        }
    except (TimeoutError, Error) as err:
        return {
            "error": err
        }


def get_agents_list() -> list:
    user_agents_file = Path(__file__).parent / 'user-agents.txt'
    with open(user_agents_file, 'r') as f:
        return f.read().split('\n')


def get_random_agent(agents_list: list) -> str:
    return random.choice(agents_list)


async def gather_dict(tasks: dict):
    async def mark(key, coro):
        return key, await coro
    return {
        key: result
        for key, result in await asyncio.gather(
            *(mark(key, coro) for key, coro in tasks.items())
        )
    }


async def scrap_url_lxml(client,
                         url: str,
                         locale: str,
                         agents_list: list):

    data = await automation_amz_product_lxml(client,
                                             url,
                                             locale,
                                             get_random_agent(agents_list))
    data["url"] = url
    data["lang"] = locale
    return data


async def run_crawler_lxml(client,
                           url: str,
                           locales: list,
                           agents_list: list):

    dict_tasks = {}
    for locale in locales:
        task = asyncio.create_task(
            scrap_url_lxml(client,
                           url,
                           locale,
                           get_random_agent(agents_list)))
        dict_tasks[locale] = task

    return await gather_dict(dict_tasks)


async def scrap_with_lxml(urls: list,
                          locales: list,
                          agents_list: list):
    async with httpx.AsyncClient() as client:
        dict_tasks = {}
        for url in urls:
            task = asyncio.create_task(
                run_crawler_lxml(client,
                                 url,
                                 locales,
                                 agents_list))
            dict_tasks[url] = task

        return await gather_dict(dict_tasks)


async def scrap_url(browser: Browser,
                    url: str,
                    locale: str,
                    agents_list: list):
    try:
        page = await browser.new_page(user_agent=get_random_agent(agents_list),
                                      locale=locale)
        data = await automation_amz_product(page, url)
        data["url"] = url
        data["lang"] = locale
        return data
    finally:
        await page.close()


async def run_crawler(browser: Browser,
                      url: str,
                      locales: list,
                      agents_list: list):
    dict_tasks = {}
    for locale in locales:
        task = asyncio.create_task(
            scrap_url(browser,
                      url,
                      locale,
                      agents_list))
        dict_tasks[locale] = task

    return await gather_dict(dict_tasks)


async def scrap_with_playwright(urls: list,
                                locales: list,
                                agents_list: list):
    async with async_playwright() as playwright:
        try:
            chromium = playwright.chromium
            browser = await chromium.launch()

            async def gather_dict(tasks: dict):
                async def mark(key, coro):
                    return key, await coro
                return {
                    key: result
                    for key, result in await asyncio.gather(
                        *(mark(key, coro) for key, coro in tasks.items())
                    )
                }

            dict_tasks = {}
            for url in urls:
                task = asyncio.create_task(
                    run_crawler(browser,
                                url,
                                locales,
                                agents_list))
                dict_tasks[url] = task

            return await gather_dict(dict_tasks)
        finally:
            await browser.close()


async def scrap_urls(urls: Union[str, list],
                     locales: Union[str, list] = ["en-US", "es-MX"],
                     method: str = "playwright"):

    urls: list = urls.split(",") \
        if isinstance(urls, str) \
        else urls
    locales: list = locales.split(",") \
        if isinstance(locales, str) \
        else locales

    agents_list = get_agents_list()

    supported_methods = ["playwright", "lxml"]
    if method not in supported_methods:
        raise ValueError(
            f"method '{method}' not supported. {supported_methods}")

    if method == "playwright":
        return await scrap_with_playwright(urls, locales, agents_list)
    elif method == "lxml":
        return await scrap_with_lxml(urls, locales, agents_list)


def cli():
    import argparse

    parser = argparse.ArgumentParser("Amazon Product Scraper")
    parser.add_argument("--urls", required=True,
                        help="list of url comma-separated")
    parser.add_argument("-l", "--lang", nargs='+', default=["en-US", "es-MX"])
    parser.add_argument(
        "--method", choices=["playwright", "lxml"], default="playwright")
    args = parser.parse_args()
    products = asyncio.run(scrap_urls(args.urls, args.lang, args.method))
    products = str(products) \
        .replace('"', '[rdq]"[rdq]') \
        .replace("'", '"') \
        .replace('[rdq]"[rdq]', '\\"')
    print(products)


if __name__ == "__main__":

    urls = ("https://a.co/d/geQhA2O",
            "https://a.co/d/d650BRG",
            "https://a.co/d/5GjLWQx",
            "https://a.co/d/cewgOFz",
            "https://a.co/d/3h52kBL")

    locales = ["en-US", "es-MX"]
    data1 = asyncio.run(timeit(scrap_urls)(urls, locales, "playwright"))
    print(data1)
    data2 = asyncio.run(timeit(scrap_urls)(urls, locales, "lxml"))
    print(data2)

    print(len(data1) == len(data2))
