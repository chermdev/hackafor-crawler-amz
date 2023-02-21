import random
from typing import Union
from playwright.async_api import async_playwright, Page
from pathlib import Path


async def automation_amz_product(page: Page, url: str):
    """ Plawyright automation to get product data """
    PRODUCT_TITLE = "//span[@id='productTitle']"
    PRODUCT_PRICE_WHOLE = "//span[@class='a-price-whole']"
    PRODUCT_PRICE_FRACTION = "//span[@class='a-price-fraction']"
    PRODUCT_IMAGE_URL = "//div[@id='imgTagWrapperId']/img"
    PRODUCT_CATEGORIES = "//div[@id='wayfinding-breadcrumbs_container']//a"
    # if not url.endswith("&language=es_MX"):
    #     url += "&language=es_MX"
    await page.goto(url)
    await page.wait_for_selector(PRODUCT_TITLE)
    title = str(await page.inner_text(PRODUCT_TITLE))
    price_whole = str(await page.text_content(PRODUCT_PRICE_WHOLE))
    price_fraction = str(await page.inner_text(PRODUCT_PRICE_FRACTION))
    price = float(price_whole + price_fraction)
    img_url = await page.get_attribute(PRODUCT_IMAGE_URL, 'src')
    categories = await page.locator(PRODUCT_CATEGORIES).all_inner_texts()
    return {
        "name": "",
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


def scrap_urls(urls: Union[str, list], locale: str = "en-US"):
    import asyncio

    if isinstance(urls, str):
        urls = urls.split(",")

    async def main(urls: list):
        async with async_playwright() as playwright:
            try:
                chromium = playwright.chromium
                browser = await chromium.launch()

                async def execute_crawler(url: str):
                    try:
                        page = await browser.new_page(user_agent=get_random_agent(),
                                                      locale=locale)
                        return await automation_amz_product(page, url)
                    finally:
                        await page.close()

                tasks = set()
                for url in urls:
                    task = asyncio.create_task(execute_crawler(url))
                    tasks.add(task)
                    task.add_done_callback(tasks.discard)

                return await asyncio.gather(*tasks)
            finally:
                await browser.close()

    return asyncio.run(main(urls))


def cli():
    import argparse

    parser = argparse.ArgumentParser("Amazon Product Scraper")
    parser.add_argument("--urls", required=True,
                        help="list of url comma-separated")
    parser.add_argument("--locale", default="en-US")
    args = parser.parse_args()
    products = scrap_urls(args.urls,
                          locale=args.locale)
    products = str(products) \
        .replace('"', '[rdq]"[rdq]') \
        .replace("'", '"') \
        .replace('[rdq]"[rdq]', '\\"')
    print(products)
