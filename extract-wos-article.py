import asyncio
from playwright.async_api import async_playwright, Page
import typer
import re

AUTHORS_SELECTOR = ".authors-div > .ng-star-inserted > span:nth-child(2) .value"  # noqa
TITLE_SELECTOR = ".title.text--large"
JOURNAL_SELECTOR = ".journal-content .journal-content-row"
SELECTORS = {
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

YEAR_REGEX = re.compile(".*([0-9]{4})")


async def extract_text_from_selector(
    selector: str, page: Page, default_value: str = ""
):
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

        for selector in SELECTORS.keys():
            text = await extract_text_from_selector(SELECTORS[selector], page)
            outputs[selector] = text

        journal_metdata = {}
        journal_content_rows = await page.query_selector_all(JOURNAL_SELECTOR)
        for row in journal_content_rows:
            key_selector = await row.query_selector("h3")
            key = await key_selector.inner_text()

            value_selector = await row.query_selector_all("span")
            value = ", ".join([await span.inner_text() for span in value_selector])
            # Quick hack around getting comma spearation of those spans right
            value = value.replace(", ,", ",")

            journal_metdata[key] = value

        for journal_key, outputs_key in JOURNAL_SELECTORS_MAPPING.items():
            if journal_key in journal_metdata:
                outputs[outputs_key] = journal_metdata[journal_key]

        if "pubdate" in outputs:
            year_match = YEAR_REGEX.match(outputs["pubdate"])
            if year_match:
                # Pick the capture group -- hopefully the year
                outputs["year"] = year_match.group(1)

        import pprint

        pprint.pprint(outputs)
        await browser.close()


def main(
    url: str, debug: bool = typer.Option(False), proxy_server: str = typer.Option("")
):
    asyncio.run(main_extract(url, debug, proxy_server))


if __name__ == "__main__":
    typer.run(main)
