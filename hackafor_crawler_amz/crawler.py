import random
from typing import Union
from playwright.async_api import async_playwright, Page
from pathlib import Path
import asyncio


async def automation_amz_product(page: Page, url: str):
    """ Plawyright automation to get product data """
    PRODUCT_TITLE = "//span[@id='productTitle']"
    PRODUCT_PRICE = "//*[@id='corePrice_desktop']//span[contains(@class,'a-price')]/span[1]"
    PRODUCT_PRICE_WHOLE = "//span[@class='a-price-whole']"
    PRODUCT_PRICE_FRACTION = "//span[@class='a-price-fraction']"
    PRODUCT_IMAGE_URL = "//div[@id='imgTagWrapperId']/img"
    PRODUCT_CATEGORIES = "//div[@id='wayfinding-breadcrumbs_container']//a"
    # if not url.endswith("&language=es_MX"):
    #     url += "&language=es_MX"
    await page.goto(url)
    await page.wait_for_selector(PRODUCT_TITLE, timeout=5000)
    title = str(await page.inner_text(PRODUCT_TITLE, timeout=1000))
    price_ele = page.locator(PRODUCT_PRICE)
    if await price_ele.is_visible(timeout=1000):
        price_str = await page.text_content(PRODUCT_PRICE, timeout=1000)
    else:
        price_whole = str(await page.text_content(PRODUCT_PRICE_WHOLE, timeout=1000))
        price_fraction = str(await page.inner_text(PRODUCT_PRICE_FRACTION, timeout=1000))
        price_str = price_whole + price_fraction
    price = float(price_str.replace("$", "").replace(",", ""))
    img_url = await page.get_attribute(PRODUCT_IMAGE_URL, 'src', timeout=1000)
    categories = await page.locator(PRODUCT_CATEGORIES).all_inner_texts()
    return {
        "full_name": title.replace('\n', ''),
        "price": price,
        "image": img_url,
        "categories": categories
    }


def get_random_agent():
    user_agents_file = Path(__file__).parent / 'user-agents.txt'
    with open(user_agents_file, 'r') as f:
        agents_list = f.read().split('\n')
        return random.choice(agents_list)


async def scrap_urls(urls: Union[str, list],
                     locales: Union[str, list] = ["en-US", "es-MX"]):

    urls: list = urls.split(",") \
        if isinstance(urls, str) \
        else urls
    locales: list = locales.split(",") \
        if isinstance(locales, str) \
        else locales

    async with async_playwright() as playwright:
        try:
            chromium = playwright.chromium
            browser = await chromium.launch()

            async def execute_crawler(url: str, locales: str):
                data = {}
                try:
                    for locale in locales:
                        page = await browser.new_page(user_agent=get_random_agent(),
                                                      locale=locale)
                        data[locale] = await automation_amz_product(page, url)
                    return data
                finally:
                    await page.close()

            tasks = set()
            for url in urls:
                task = asyncio.create_task(
                    execute_crawler(url, locales))
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
