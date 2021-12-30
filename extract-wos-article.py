import asyncio
import time

from playwright.async_api import async_playwright, Page
import typer
import re

AUTHORS_SELECTOR = ".authors-div > .ng-star-inserted > span:nth-child(2) .value"  # noqa
TITLE_SELECTOR = ".title.text--large"
JOURNAL_SELECTOR = ".journal-content .journal-content-row"
CITING_SELECTORS = {
    "citations_articles": ".summary-record > .data-section h3",
    "current_page": ".wos-input-underline",
    "final_page": ".end-page",
}
ARTICLE_SELECTORS = {
    "journal": "app-jcr-overlay",
    "volume": "#FullRTa-volume",
    "issue": "#FullRTa-issue",
    "page": "#FullRTa-pageNo",
    "DOI": "#FullRTa-DOI",
    "times_cited": "#snCitationData .large-link-number:nth-of-type(1)",
    "pubdate": "#FullRTa-pubdate",
    "article_no": "span#FullRTa-articleNumberLabel",
}

JOURNAL_SELECTORS_MAPPING = {
    "ISSN": "issn",
    "eISSN": "eissn",
    "Current Publisher": "publisher",
}

REGEX = {
    "year": re.compile(".*([0-9]{4})"),
    "wos_id": re.compile("(WOS:[0-9]{15})"),
}
CITING_SUMMARY_URL_PREFIX = "https://www.webofscience.com/wos/woscc/citing-summary/"


async def extract_citing_summary(page: Page, article_id: str):
    url = f"{CITING_SUMMARY_URL_PREFIX}{article_id}"
    await page.goto(url, wait_until="networkidle")

    curr_page = await page.query_selector(CITING_SELECTORS["current_page"])
    curr_page_text = await curr_page.input_value()
    curr_page_num = int(curr_page_text.strip())

    final_page = await page.query_selector(CITING_SELECTORS["final_page"])
    final_page_text = await final_page.inner_html()
    final_page_num = int(final_page_text.strip())

    articles = []
    while curr_page_num <= final_page_num:
        curr_articles_num = -1
        curr_articles = []

        while len(curr_articles) > curr_articles_num:
            curr_articles_num = len(curr_articles)
            await page.keyboard.press("PageDown")
            curr_articles = await page.query_selector_all(CITING_SELECTORS["citations_articles"])
            time.sleep(0.1)

        if curr_page_num < final_page_num:
            await page.click('[aria-label="Bottom Next Page"]')
            time.sleep(2)

        articles.extend(curr_articles)
        curr_page_num += 1

    articles_ids = []
    for article in articles:
        article_text = await article.inner_html()
        article_id = REGEX["wos_id"].findall(article_text)[0]
        articles_ids.append(article_id)
    return articles_ids


async def extract_text_from_selector(selector: str, page: Page, default_value: str = ""):
    selector = await page.query_selector(selector)
    if not selector:
        return default_value

    return await selector.inner_text()


async def main_extract(url: str, debug: bool = False, proxy_server: str = ""):

    async with async_playwright() as p:
        if debug:
            if proxy_server:
                proxy = {"server": proxy_server}
            else:
                proxy = None

            browser = await p.chromium.launch(headless=False, slow_mo=100, proxy=proxy)
        else:
            browser = await p.chromium.launch()

        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")

        await page.click("#onetrust-accept-btn-handler")

        outputs = {}

        title = await page.query_selector(TITLE_SELECTOR)
        title_text = await title.inner_html()

        outputs["title"] = title_text

        authors = await page.query_selector_all(AUTHORS_SELECTOR)

        authors_list = []
        for author in authors:
            author_str = await author.inner_text()
            surname, *names = author_str.split(", ")
            authors_list.append({"surname": surname, "names": "".join(names)})

        outputs["authors"] = authors_list

        for selector in ARTICLE_SELECTORS.keys():
            text = await extract_text_from_selector(ARTICLE_SELECTORS[selector], page)
            outputs[selector] = text

        journal_metdata = {}
        journal_content_rows = await page.query_selector_all(JOURNAL_SELECTOR)
        for row in journal_content_rows:
            key_selector = await row.query_selector("h3")
            key = await key_selector.inner_text()

            value_selector = await row.query_selector_all("span")
            value = ", ".join([await span.inner_text() for span in value_selector])
            # Quick hack around getting comma separation of those spans right
            value = value.replace(", ,", ",")

            journal_metdata[key] = value

        for journal_key, outputs_key in JOURNAL_SELECTORS_MAPPING.items():
            if journal_key in journal_metdata:
                outputs[outputs_key] = journal_metdata[journal_key]

        if "pubdate" in outputs:
            year_match = REGEX["year"].match(outputs["pubdate"])
            if year_match:
                # Pick the capture group -- hopefully the year
                outputs["year"] = year_match.group(1)

        article_id = url.split("/")[-1]
        outputs["citing_summary"] = await extract_citing_summary(page, article_id)

        import pprint

        pprint.pprint(outputs)
        await browser.close()


def main(url: str, debug: bool = typer.Option(False), proxy_server: str = typer.Option("")):
    asyncio.run(main_extract(url, debug, proxy_server))


if __name__ == "__main__":
    typer.run(main)
