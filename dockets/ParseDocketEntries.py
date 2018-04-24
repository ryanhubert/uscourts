#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Ryan Hübert
# Department of Political Science
# University of California, Davis

"""
dockets.ParseDocketEntries v1.0
Extracts entries from HTML formatted docket sheet from CM/ECF and returns a dictionary
with data and text from each entry.
"""

import re
from bs4 import BeautifulSoup
from datetime import datetime

def ExtractEntries(file_path_or_bs4obj, date_range = None, return_all = False):
    """
    ExtractEntries v1.0
    Take a beautiful soup object and return a dictionary of a docket's entries.

    :param file_path_or_bs4obj: str specifying an HTML formatted docket sheet from ECF
            OR a beautiful soup object (for efficiency)
    :param date_range: a tuple or list of len=2 with a start and end date
    :param return_all: bool, return all dict entries or just ones in window
    :return: dict of docket entries
    """

    # file_path_or_bs4obj = '/Users/ryanhubert/USDC-Dataset-Data/dockets-wawd/2011/201116-00025.html'
    # date_range = None
    # date_range = [date(2012,3,6),date(2012,9,6)]

    if type(file_path_or_bs4obj) is str:
        html_text = open(file_path_or_bs4obj, 'r').read()
        soup = BeautifulSoup(html_text, 'lxml')
    else:
        soup = file_path_or_bs4obj

    table = [x for x in soup.find_all('table') if "Docket Text" in x.text]
    table = table[0] if table != [] else None

    if table is not None:
        df = {}
        linksout = {}
        for r in range(1, len(table.find_all('tr'))):
            row = [x for x in table.find_all('tr')[r].find_all("td")]
            df[r] = {}
            df[r]['date'] = row[0].text
            df[r]['date'] = datetime.strptime(df[r]['date'], '%m/%d/%Y').date()
            df[r]['doc_num'] = row[1].text.strip() if re.search('[^ ]', row[1].text) else None
            df[r]['doc_link'] = re.findall('href *\= *[\"\']([^\"\']+)[\"\']', str(row[1]))
            df[r]['doc_link'] = df[r]['doc_link'][0] if df[r]['doc_link'] != [] else None
            if df[r]['doc_link'] is not None:
                linksout[df[r]['doc_link']] = r
            df[r]['entry_text'] = row[2].text.strip()
            if date_range is not None and not (date_range[0] <= df[r]['date'] <= date_range[1]):
                df[r]['in_window'] = False
            else:
                df[r]['in_window'] = True
            entry_links = str(row[2])
            entry_links = re.sub('</?td[^>]*>', '', entry_links)
            entry_links = re.sub('<a href *\= *[\"\']([^\"\']+)[\"\'][^>]*>([^<]*)</a>', '<\\1>{\\2}', entry_links)

            for l in linksout:
                entry_links = re.sub("<" + l + ">\{([^\}]*)\}", '<' + str(linksout[l]) + '>{\\1}', entry_links)
            df[r]['linked_entries'] = sorted([int(x) for x in re.findall('<(\d+)>', entry_links)])
    else:
        df = {}

    if return_all:
        return df
    else:
        return {x:df[x] for x in df if df[x]['in_window']}