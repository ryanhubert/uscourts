#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Ryan Hübert
# Department of Political Science
# University of California, Davis

"""
dockets.ClassifierTools v1.0
Tools for using docket sheet outcome classifiers
"""

import re
import os
from dockets.ParseDocketEntries import ExtractEntries
from nltk.stem.snowball import SnowballStemmer
from nltk import sent_tokenize

import datetime
from bs4 import BeautifulSoup

stemmer = SnowballStemmer("english")

abbr = {x.split('\t')[0] : x.split('\t')[1] for x in open(os.path.dirname(os.path.realpath(__file__)) + '/data/shorthand.txt','r').read().split('\n') if 'Source' not in x}
keyphrsS = open(os.path.dirname(os.path.realpath(__file__))+'/data/phrases_settlement.txt', 'r').read().split('\n')
keyphrsP = open(os.path.dirname(os.path.realpath(__file__))+'/data/phrases_prejudice.txt', 'r').read().split('\n')
clause_breaks = ',;:\n'

def FindDates(html_string):
    """
    Takes HTML of docket sheet and identifies a case
    filed and terminated date

    :param html_string: str HTML of docket sheet
    :return: list with filing and termination dates
    """

    chunk = html_string[html_string.find('</h3'):]
    chunk = chunk[chunk.find('<table'):]
    chunk = chunk[:chunk.find('<u>')]
    chunk = chunk.replace('s:', ':')
    chunk = chunk.replace('\t', '\n')
    chunk = chunk.replace("<br>", "\n")

    soup = BeautifulSoup(chunk, 'lxml')

    tables = [' '.join(x.split()).strip() for x in soup.text.split('\n') if ":" in x]
    tables = [x.split(': ') for x in tables if len(x.split(': ')) > 1]
    tables = [['_'.join(x[0].lower().split()).strip(), x[1].strip()] for x in tables]
    tables = [[x[0] if x[0][-1] != 's' else x[0][:-1], x[1].strip()] for x in tables]

    filed = [x[1] for x in tables if x[0] in ['date_filed']]
    filed = filed[0] if len(filed) > 0 else ''
    if '/' in filed:
        filed = datetime.datetime.strptime(filed, '%m/%d/%Y').date()
    else:
        filed = None
    termd = [x[1] for x in tables if x[0] in ['date_terminated']]
    termd = termd[0] if len(termd) > 0 else ''
    if '/' in termd:
        termd = datetime.datetime.strptime(termd, '%m/%d/%Y').date()
    else:
        termd = None

    return filed, termd

def BasicTextFormatter(string):
    """
    Takes a raw string (e.g., entry from docket sheet) and does some
    preprocessing to standardize the text.
    """

    i = string.lower()

    # Remove parenthetical and bracketed statements
    i = re.sub('\([^\)]*\)', ' ', i)
    i = re.sub('\[[^\]]*\]', ' ', i)

    # Remove any token NOT containint
    i = ' '.join(i.replace('\n\n', '. ').split())

    # Standardize possessives and apostrophes
    i = i.replace("'s ", " _s ")
    i = i.replace("s' ", "s _s ")

    # Standardize party names
    ## Respondent -> Defendant
    ## Petitioner -> Plaintiff
    i = i.replace(' respondent', ' defendant')
    i = i.replace(' petitioner', ' plaintiff')

    # Replace shorthand phrases (using list of abbreviations)
    i = i.replace('&', ' and ')
    i = i.replace(' w/ ', ' with ')
    i = i.replace(' w/o ', ' without ')
    i = i.replace(' w/out ', ' without ')
    i = i.replace(' w/ out ', ' without ')

    for s in abbr:
        i = re.sub('(^|[^A-z])' + s + '($|[^A-z])', '\\1' + abbr[s] + '\\2', i)
    i = i.replace(' is gr ', ' is granted ')

    i = i.replace(" _s ", "_s ")

    ## Clean up motions
    i = re.sub(' (petitions?|motions?) (?:for|to) ([^ ]+) ', ' \\1 \\2 ', i)
    i = re.sub(' (def|pla)(?:endant|intiff)s?(?:_s)? (petitions?|motions?)', ' by_\\1 \\2 ', i)
    i = re.sub(' (?:by|filed by) (?:the )?(def|pla)(?:endant|intiff)s? ', ' by_\\1 ', i)

    # Retain some key phrases when tokenizing
    for s in keyphrsS + keyphrsP:
        i = i.replace(s, s.replace(' ', '_'))
    i = i.replace(' r and r ', ' r_r ')
    i = i.replace(' report and recommendations ', ' r_r ')
    i = i.replace(' report and recommendation ', ' r_r ')

    # Remove "stipulation and order"
    i = i.replace(' stipulation and order ', ' order ')

    # Clean up judgment directions
    i = re.sub('judgment for (?:all )?(def|pla)', 'judgment in favor of \\1', i)
    i = re.sub('judgment (?:is )?granted +(?:for|to) +(?:all +)?(def|pla)', 'judgment in favor of \\1', i)

    # Final clean-up
    i = re.sub('(^| )[^a-z' + clause_breaks + ']{2,}($| )', '\\1 \\2', i)
    i = ' '.join(i.split())
    i = re.sub(' plaintiffs?_s ', ' plaintiff ', i)
    i = re.sub(' defendants?_s ', ' defendant ', i)

    i = re.sub(' ([,\.;:_])', '\\1', i)
    sentences = [x if x[-1] != '.' else x[:-1] for x in sent_tokenize(i)]
    clauses = [[x for x in re.split('[' + clause_breaks + ']', y) if any(z.islower() for z in x)] for y in sentences]
    clauses = [[' '.join(re.sub('[^_a-z]', ' ', y).split()) for y in x] for x in clauses]

    return clauses

def TerminationWindowEntries(html_string,windows=[0,0],return_full=False):
    """
    Returns entry dictionary for entries around termination date of case

    :param html_string:
    :param windows: list of len=2 with number of days prior and after termination date
    :param return_full: bool, return both full dict and terminated window dict
    :return:
    """

    soup = BeautifulSoup(html_string, 'lxml')
    filed, terminated = FindDates(html_string)

    if terminated is None:
        return {}

    window = [terminated]
    if terminated.weekday() not in [0, 4]:
        window.append(terminated - datetime.timedelta(windows[0])) #1
        window.append(terminated + datetime.timedelta(windows[1])) #1
    elif terminated.weekday() == 0:
        window.append(terminated - datetime.timedelta(2+windows[0])) #3
        window.append(terminated + datetime.timedelta(windows[1])) #1
    elif terminated.weekday() == 4:
        window.append(terminated - datetime.timedelta(windows[0])) #1
        window.append(terminated + datetime.timedelta(2+windows[1])) #3

    return ExtractEntries(soup, date_range = [min(window), max(window)], return_all=return_full)