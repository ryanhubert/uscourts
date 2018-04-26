#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Ryan Hübert
# Department of Political Science
# University of California, Davis

"""
dockets.CivilOutcomeClassifier v1.1
A dictionary-based classifier that uses text of docket entries on or near a case
termination date to code the outcome of the case.
"""

import re
import os
from nltk.stem.snowball import SnowballStemmer
stemmer = SnowballStemmer("english")

# This sets current path depending on whether in IDE
try:
    current_path =  os.path.dirname(os.path.realpath(__file__))
except:
    current_path = os.getcwd()

# Text Tools
stemmer = SnowballStemmer("english")

# We do not use this. Preserving for future consideration.
# from nltk.corpus import stopwords
# stop_words = stopwords.words('english')
# stop_words = [stemmer.stem(x) for x in stop_words]
# stop_words.remove('against')
# stop_words.remove('with')

# Important search terms
# NB: these words are not used: 'voluntary'
abbr = {x.split('\t')[0] : x.split('\t')[1] for x in open(current_path + '/data/shorthand.txt','r').read().split('\n') if 'Source' not in x}
keyphrsS = open(current_path +'/data/phrases_settlement.txt', 'r').read().split('\n')
keyphrsP = open(current_path +'/data/phrases_prejudice.txt', 'r').read().split('\n')
keywords = ['transfer', 'remand', 'vacate', 'reverse', 'affirm', 'default', 'habeas',
            'dismissal', 'dismiss', 'settled', 'settlement', 'joint', 'stipulation', 'stipulated',
            'motion', 'summary', 'judgment','grant', 'denial', 'deny',
            'defendant', 'plaintiff', 'commissioner', 'petitioner', 'respondent',
            'favor', 'against', 'award', 'entitled', 'damages', 'petition',
            'lack', 'jurisdiction', 'standing', 'stay']
keywords = [stemmer.stem(re.sub(' ','_',x)) for x in keywords + keyphrsS + keyphrsP]
keywords = sorted(list(set(keywords)))
clause_breaks = ',;:\n'


settsearch1 = '(' + '|'.join([stemmer.stem(re.sub(' ','_',x)) for x in keyphrsS]) + ')'
settsearch2 = '(case_settl|settlement|settl|joint|consent|stipul)'

outvars = ['forma_pauperis',
            'forum_non_conveniens',
            'r&r',
            'lack_jurisdiction',
            'lack_standing',
            'transfer',
            'default',
            'remand',
            'review',
            'dismiss',
            'settlement',
            'w_prej-voluntary',
            'w_prej-involuntary',
            'wo_prej',
            'wo_prej_d',
            'sumjud',
            'jud',
            'defendant',
            'plaintiff',
            'motions_petitions']

def BasicTextFormatter(string):
    """
    Takes a raw string (e.g., entry from docket sheet) and does some preprocessing to standardize the text.
    This is designed to work with the dictionary-based classifier of civil outcomes.
    :param string: str of docket text
    :return: list of str, each representing a clause in string with processed text
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
    i = i.replace(' w/p', ' with p')
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
    i = i.replace('plaintiffs_s ','plaintiff ')
    i = i.replace('plaintiff_s ', 'plaintiff ')
    i = i.replace('defendants_s ', 'defendant ')
    i = i.replace('defendant_s ', 'defendant ')

    i = re.sub(' ([,\.;:_])', '\\1', i)
    sentences = [x if x[-1] != '.' else x[:-1] for x in sent_tokenize(i)]
    clauses = [[x for x in re.split('[' + clause_breaks + ']', y) if any(z.islower() for z in x)] for y in sentences]
    clauses = [[' '.join(re.sub('[^_a-z]', ' ', y).split()) for y in x] for x in clauses]

    return clauses

def CivilOutcomeClassifier(entries, habeas=False):
    """
    Take a set of docket entries (for civil cases) and use dictionary methods to
    classify the case outcome(s) using categories in outvars
    :param entries: dict generated by ExtractEntries()
    :param habeas: bool
    :return: tuple of dict with classifications and cleaned text
    """

    outcome = {x: False for x in outvars}
    if entries == {}:
        return (outcome, '')

    # Break entries into clauses (useful down below)
    clauses = []
    for string in [entries[x]['entry_text'] for x in entries]:
        # We use "settle" to classify cases as settlement, and this judge's
        # name is causing problems
        string = string.replace('Benjamin H. Settle'.lower(), ' ')
        string = string.replace('Benjamin Settle'.lower(), ' ')
        clauses.extend([y for x in BasicTextFormatter(string) for y in x if y != ""])

    ## Catch some useful stuff
    if 'forma pauperis' in ' '.join(clauses):
        outcome['forma_pauperis'] = True
    if 'forum non conveniens' in ' '.join(clauses):
        outcome['forum_non_conveniens'] = True

    # clauses = [re.sub('  +',' ',x) for x in clauses]
    clauses = [[x for x in y.split(' ') if re.search("[a-z]", x) and len(x) > 1] for y in clauses]
    clauses = [[stemmer.stem(x) for x in y] for y in clauses]
    clauses = [[x for x in y if x in keywords or '_' in x] for y in clauses]
    clauses = [x for x in clauses if x != []]

    text_merge = '-'.join(['.'.join(x) for x in clauses])

    # CODE OUTCOMES ACCORDING TO RULES

    ## Find R&Rs
    if 'r_r' in text_merge and 'adopt' in text_merge:
        outcome['r&r'] = True

    ## Case transfered elsewhere, not terminated
    if 'transfer' in text_merge:
        outcome['transfer'] = True

    ## Default judgment, favors plaintiff
    if 'default.judgment' in text_merge and 'dismiss' not in text_merge:
        outcome['default'] = True

        ## Review of agencies and state courts: affirm, reverse, remand
    if 'remand' in text_merge:
        outcome['remand'] = True
        if re.search(settsearch2, text_merge):
            outcome['settlement'] = True

    if 'affirm' in text_merge:
        outcome['review'] = True
        outcome['defendant'] = True  # Affirm = pro-defendant (eg, SSA)

    if 'revers' in text_merge:
        outcome['review'] = True
        outcome['plaintiff'] = True

    ## Habeas Cases
    if habeas == True or 'habea' in text_merge:
        if 'petit.deni' in text_merge and not 'petit.grant' in text_merge:
            outcome['dismiss'] = True
            if not 'without_prejudic' in text_merge:
                outcome['w_prej-involuntary'] = True
            else:
                outcome['wo_prej'] = True
        if 'petit.grant' in text_merge and not 'petit.deni' in text_merge:
            outcome['plaintiff'] = True
        if ('deni' in text_merge or 'dismiss' in text_merge) and not 'grant' in text_merge:
            outcome['dismiss'] = True
            if not 'without_prejudic' in text_merge:
                outcome['w_prej-involuntary'] = True
            else:
                outcome['wo_prej'] = True
        if ('deni' not in text_merge and 'dismiss' not in text_merge) and 'grant' in text_merge:
            outcome['plaintiff'] = True

    ## Settlements and dismissals
    if re.search(settsearch1, text_merge):
        outcome['dismiss'] = True
        outcome['settlement'] = True
        outcome['w_prej-voluntary'] = True
    elif 'dismiss' in text_merge and (habeas == False and 'habea' not in text_merge):
        outcome['dismiss'] = True
        # Prejudice language in text (all allowed, e.g, dismissals of multiple claims)
        if 'without_prejudic' in text_merge:
            outcome['wo_prej'] = True
        if 'with_prejudic' in text_merge:
            if re.search(settsearch2, text_merge):
                outcome['settlement'] = True
                outcome['w_prej-voluntary'] = True
            else:
                outcome['w_prej-involuntary'] = True
        # No prejudice language at all
        if 'without_prejudic' not in text_merge and 'with_prejudic' not in text_merge:
            if 'stipul' in text_merge and 'proposed_ord' in text_merge:
                outcome['settlement'] = True
                outcome['w_prej-voluntary'] = True
            else:  # This is our reversion classification -- when not clear what kind of dism
                outcome['wo_prej_d'] = True

    ## Wrong venue?
    if 'lack.jurisdict' in text_merge:
        outcome['lack_jurisdiction'] = True
    if 'lack.stand' in text_merge:
        outcome['lack_standing'] = True

    ## Identify summary judgments, other judgments (e.g., after trial)

    ## Also keep all formatted strings related to motions and petitions
    ## can use later to code outcomes that are blank
    mss = []
    for clause in clauses:
        i = '.'.join(clause)
        if 'petit' in i or 'motion' in i:
            i = i.replace('petit','motion')
            if 'by_def' in i or 'defend.motion' in i:
                mss.append('defendant/mot_pet')
                for r in re.findall('(?:grant|deni)', i):
                    mss.append('defendant/mot_pet/' + r)
            if ('by_pla' in i or 'plaintiff.motion' in i) and 'grant' in i:
                mss.append('plaintiff/mot_pet')
                for r in re.findall('(?:grant|deni)', i):
                    mss.append('plaintiff/mot_pet/' + r)
        if 'summari.judgment' in i and not 'deni' in i:
            outcome['sumjud'] = True
            if 'motion.summari.judgment' in i and ('grant' in i and 'deni' not in i):
                if 'by_def' in i or 'defend' in i:
                    outcome['defendant'] = True
                if 'by_pla' in i or 'plaintiff' in i:
                    outcome['plaintiff'] = True
        elif 'judgment' in i and not 'default.judgment' in i:
            if not any(outcome[z] for z in outcome if
                       z not in ['r&r', 'lack_jurisdiction', 'lack_standing', 'forma_pauperis',
                                 'forum_non_conveniens']):
                outcome['jud'] = True
        else:  # do not code direction if language above not found
            continue

    mss = ["" if any((x in z and len(x) < len(z)) for z in mss) else x for x in mss]
    mss = [x for x in mss if x != ""]

    ## Code directions if a judgment is identified
    ## This is overly inclusive -- will code D and P decisions liberally!
    if outcome['jud'] == True or outcome['sumjud'] == True:
        if 'favor.defend' in text_merge or 'against.plaintiff' in text_merge:
            outcome['defendant'] = True
        if 'favor.plaintiff' in text_merge or 'against.defend' in text_merge:
            outcome['plaintiff'] = True
        if 'award.platiff.damag' in text_merge:
            outcome['plaintiff'] = True
        if 'plaintiff.entitl.judgment' in text_merge:
            outcome['plaintiff'] = True
        if 'defend.entitl.judgment' in text_merge:
            outcome['defendant'] = True

    outcome['motions_petitions'] = sorted(mss)

    return outcome, text_merge