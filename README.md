# steel-wok
Exactly what it sounds like

## Installation

All the dependencies should be in `requirements.txt`. Hence, installation
should be as easy as running:

    pip install -r requirements.txt

Since many of the scripts included here use `playwright`, we suggest installing
its dependencies too:

    playwright install

## Running

Should be as easy as running

    python extract-wos-article.py https://www.webofscience.com/wos/woscc/full-record/WOS:000690353600001

Which would then produce output similar to

    {'DOI': '10.1007/s11262-021-01866-5',
     'article_no': '',
     'authors': [{'names': 'Brona', 'surname': 'Brejova'},
                 {'names': 'Kristina', 'surname': 'Borsova'},
                 {'names': 'Viktoria', 'surname': 'Hodorova'},
                 {'names': 'Viktoria', 'surname': 'Cabanova'},
                 {'names': 'Lenka', 'surname': 'Reizigova'},
                 {'names': 'Evan D.', 'surname': 'Paul'},
                 {'names': 'Pavol', 'surname': 'Cekan'},
                 {'names': 'Boris', 'surname': 'Klempa'},
                 {'names': 'Jozef', 'surname': 'Nosek'},
                 {'names': 'Tomas', 'surname': 'Vinar'}],
     'citing_summary': ['WOS:000718302600032', 'WOS:000707419500038'],
     'eissn': '1572-994X',
     'issn': '0920-8569',
     'issue': '6',
     'journal': 'VIRUS GENES',
     'page': '556-560',
     'pubdate': 'DEC 2021',
     'publisher': 'SPRINGER, VAN GODEWIJCKSTRAAT 30, 3311 GZ DORDRECHT, '
                  'NETHERLANDS',
     'times_cited': '2',
     'title': 'A SARS-CoV-2 mutant from B.1.258 lineage with increment H69/ '
              'increment V70 deletion in the Spike protein circulating in Central '
              'Europe in the fall 2020',
     'volume': '57',
     'year': '2021'}

To debug how the script works (i.e. by not making the Chromium that's being
started headless), you can specify the `--debug` option.

Should you want to make use of a proxy, e.g. SOCKS proxy running on port `11000`
on `localhost`, you can do so by specifying further options:

    python extract-wos-article.py https://www.webofscience.com/wos/woscc/full-record/WOS:000690353600001 --debug --proxy-server socks://localhost:11000

## Development

Install the `pre-commit` hook that checks the correct formatting:

    pre-commit install