import random
import asyncio
from lxml import html
from pathlib import Path
from typing import Union
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


async def automation_amz_product_lxml(page: Page, url: str):
    """ Plawyright automation to get product data """
    try:
        await page.goto(url)
        content_html = await page.content()
        doc = html.fromstring(content_html)
        title = doc.xpath(PRODUCT_TITLE)[0].text.strip()
        product_price = doc.xpath(PRODUCT_PRICE)
        if product_price:
            price_str = product_price[0].text.strip()
        else:
            product_price_whole = doc.xpath(PRODUCT_PRICE_WHOLE)[
                0].text.strip()
            product_price_fraction = doc.xpath(
                PRODUCT_PRICE_FRACTION)[0].text.strip()
            price_str = product_price_whole + "." + product_price_fraction
        price = float(price_str.replace("$", "").replace(",", ""))
        img_url = doc.xpath(PRODUCT_IMAGE_URL)[0].attrib["src"]
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
        await page.wait_for_selector(PRODUCT_TITLE, timeout=2000)
        title = str(await page.inner_text(PRODUCT_TITLE, timeout=500))
        price_ele = page.locator(PRODUCT_PRICE)
        if await price_ele.is_visible(timeout=1000):
            price_str = await page.text_content(PRODUCT_PRICE, timeout=500)
        else:
            price_whole = str(await page.text_content(PRODUCT_PRICE_WHOLE, timeout=500))
            price_fraction = str(await page.inner_text(PRODUCT_PRICE_FRACTION, timeout=500))
            price_str = price_whole + price_fraction
        price = float(price_str.replace("$", "").replace(",", ""))
        img_url = await page.get_attribute(PRODUCT_IMAGE_URL, 'src', timeout=500)
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


async def scrap_url(browser: Browser,
                    url: str,
                    locale: str,
                    agents_list: list,
                    automation_func):
    try:
        page = await browser.new_page(user_agent=get_random_agent(agents_list),
                                      locale=locale)
        return await automation_func(page, url)
    finally:
        await page.close()


async def run_crawler(browser: Browser,
                      url: str,
                      locales: str,
                      agents_list: list,
                      automation_func):
    product_data = {
        "url": url,
        "locales": locales,
        "lang": {}
    }
    tasks = set()
    for locale in locales:
        task = asyncio.create_task(
            scrap_url(browser,
                      url,
                      locale,
                      agents_list,
                      automation_func))
        tasks.add(task)
        task.add_done_callback(tasks.discard)

    locales_data = await asyncio.gather(*tasks)

    for locale, data in zip(locales, locales_data):
        product_data["lang"][locale] = data

    return product_data


async def scrap_urls(urls: Union[str, list],
                     locales: Union[str, list] = ["en-US", "es-MX"],
                     func=automation_amz_product):

    urls: list = urls.split(",") \
        if isinstance(urls, str) \
        else urls
    locales: list = locales.split(",") \
        if isinstance(locales, str) \
        else locales

    agents_list = get_agents_list()

    async with async_playwright() as playwright:
        try:
            chromium = playwright.chromium
            browser = await chromium.launch()

            tasks = set()
            for url in urls:
                task = asyncio.create_task(
                    run_crawler(browser,
                                url,
                                locales,
                                agents_list,
                                func))
                tasks.add(task)
                task.add_done_callback(tasks.discard)

            return await asyncio.gather(*tasks)
        finally:
            await browser.close()


def cli():
    import argparse

    parser = argparse.ArgumentParser("Amazon Product Scraper")
    parser.add_argument("--urls", required=True,
                        help="list of url comma-separated")
    parser.add_argument("-l", "--lang", nargs='+', default=["en-US", "es-MX"])
    args = parser.parse_args()
    products = asyncio.run(scrap_urls(args.urls, args.lang))
    products = str(products) \
        .replace('"', '[rdq]"[rdq]') \
        .replace("'", '"') \
        .replace('[rdq]"[rdq]', '\\"')
    print(products)
