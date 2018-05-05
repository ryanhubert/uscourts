#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Ryan Hübert
# Department of Political Science
# University of California, Davis

"""
Judges.NameFinder v2.0
A function to identify names from a list of names appearing in unstructured text.
Optimized for use with federal judicial biographical data.
"""

import re

def NameFinder(namedict, string, subset=None, matches = 'all',
               namekeys=("First Name","Middle Name","Last Name","Suffix"),
               easy_output=False):
    """
    ===============
    NameFinder v2.0
    ===============
    Since v1.0:
        - Bug fixes. For example, fixes problem parsing names written in ALL CAPS.
        - Performance enhancements over v1.0 --- nearly twice as fast.
        - New option for targeting the kinds of matches desired
        - Returns a dict object with matches plus original string
          (modified to clean up formatting) with matched names tagged [BETA]
        - An option to return a list of IDs matched
    ===============
    Options
        namedict:
            [type dict] Each key is a specific ID number corresponding to
            a unique name. Each value is a dictionary containing first,
            middle, last and names.
            For example:
                namedict = {'0001' : {"f": "Jane", "m": "X.", "l": "Doe"}
                            '0002' : {"f": "John", "m": "Q.", "l": "Doe"}}
        string:
            [type str] A string that might have a name from the namedict.
        subset:
            [type list or set] A list object that is a subset of the keys
            of namedict. Only search for names in subset. (For efficiency.)
        namekeys:
            [type tuple] A 3-tuple indicating the names of the keys in each
            namedict nested dict that correspond to first, middle and last names.
        matches:
            an element from ['all','best','exact'] indicating whether
            all, best or exact matches should be returned for each name in
            the string
        easy_output:
            only return a list of IDs matched (even if duplicates); supress
            all additional information and diagnostics
        NOTE:
            an exact match indicates on of the following patterns:
              First Middle Last, F. Middle Last, First M. Last, First Last
    """

    subset = namedict.keys() if subset == None else subset

    string = string.replace('`',"'")
    string = string.replace('.'," ")
    string = string.replace('-'," ")

    # Idisyncratic formatting stuff
    ## In PACER docket sheets: "MJ" often appears inside magistrate names
    string = string.replace(" MJ "," ")
    ## Catch mistakes of form "JohnRoberts" -- NB: would incorrectly split DellaVigna into Della Vigna
    string = re.sub("([a-z]{3,})([A-Z])","\\1 \\2",string)
    ## Remove all irrelevant characters
    string = re.sub("[^ A-Za-z\']"," ",string)

    # Tokenize
    tokens = [x.upper() for x in string.split()]

    # Identify all potential names in the string
    allnames = {}
    for k in subset:
        ln = namedict[k][namekeys[2]].upper().strip().replace("."," ").replace('-',' ').replace('`',"'").split()
        if ln == [] or not all(True if t in tokens else False for t in ln):
            continue
        for n in [' '.join(tokens[max([0,i-4]):i+1]) for i,n in enumerate(tokens) if n == ln[-1]]:
            if n in allnames:
                allnames[n].append(k)
            else:
                allnames[n] = [k]

    # Match all the potential names to ID numbers from namedict
    allmatches = {x : [] for x in allnames}
    for a in allnames:
        for k in allnames[a]:
            dict_name = [namedict[k][namekeys[0]].upper().strip(),namedict[k][namekeys[1]].upper().strip(),namedict[k][namekeys[2]].upper().strip(),namedict[k][namekeys[3]].upper().strip()]
            dict_name = [x.replace("."," ").replace('-',' ').replace('`',"'") for x in dict_name]
            fn, mn, ln = dict_name[0].split(), dict_name[1].split(), dict_name[2].split()
            dict_name = ' '.join([x for x in dict_name if x != ""])
            fi = [[x[0] for x in fn][0]] if fn != [] else [] # only pulls initial from 1st First Name
            mi = [[x[0] for x in mn][0]] if mn != [] else [] # only pulls initial from 1st Middle Name

            n = ' '.join([""] + a.split() + [""])
            n = n.replace(" JUSTICE "," JUDGE ") if "JUSTICE" in n and "JUSTICE" not in ln else n

            # Applies series of rules, giving code "em" based on how good of
            # a match it is. Lower "em" is better.

            if ' '.join([""] + fn + mn + ln + [""]) in n:
                em, matched_text = 0, ' '.join([""] + fn + mn + ln + [""])
            elif ' '.join([""] + fn + mi + ln + [""]) in n:
                em, matched_text = 1, ' '.join([""] + fn + mi + ln + [""])
            elif ' '.join([""] + fi + mn + ln + [""]) in n:
                em, matched_text = 1, ' '.join([""] + fi + mn + ln + [""])
            elif fn != [] and ' '.join([""] + fn + ln + [""]) in n:
                em, matched_text = 2, ' '.join([""] + fn + ln + [""])
            elif ' '.join([""] + fi + mi + ln + [""]) in n:
                em, matched_text = 3, ' '.join([""] + fi + mi + ln + [""])
            elif fn != [] and  ' '.join([""] + fi + ln + [""]) in n:
                em, matched_text = 5, ' '.join([""] + fi + ln + [""])
            elif mn != [] and ' '.join([""] + mi + ln + [""]) in n:
                em, matched_text = 6, ' '.join([""] + mi + ln + [""])
            elif " JUDGE " in n and n[n.find(" JUDGE ")+6:].strip() == ' '.join(ln):
                em, matched_text = 7, " JUDGE " + ' '.join(ln)
            elif len(tokens) == 1 and n.strip() == ' '.join(ln):
                em, matched_text = 8, ' '.join(ln)


            else: #Stragglers
                orig = ' '+ ' '.join([x for x in n.replace(' '.join(ln),'').split()] + ln) + ' '
                mod = ' '+ ' '.join([x[0] for x in n.replace(' '.join(ln),'').split()] + ln) + ' '
                if ' '.join([""] + fi + mi + ln + [""]) == mod:
                    em, matched_text = 9, orig
                elif ' '.join([""] + fi + ln + [""]) == mod:
                    em, matched_text = 10, orig
                else:
                    em, matched_text = 99, ""

            if (em > 2 and em < 7) or em > 10:
                # Performs some regex searches to catch special cases:
                # (1) namedict's info is less robust than the string,
                # eg, finding "Barbara L. Major" in "Barbara Lynn Major"
                # (2) string uses wrong middle initial (assume it's a typo)
                # eg, finding "Barbara L. Major" in "Barbara Q. Major"
                #
                # These searches are sequenced here in order to avoid them
                # where possible. The `re` module is much less efficient
                # than string operations.
                # They are only necessary if low quality matches found above.

                if mi != [] and re.search(' '.join([""] + fn + [mi[0] + '[A-Z]+'] + ln + [""]),n):
                    em, matched_text = 2, re.search("("+' '.join([""] + fn + [mi[0] + '[A-Z]+'] + ln + [""])+")",n).group(0)
                if fn != [] and re.search(' '.join(fn + ['[A-Z]'] + ln),n):
                    em, matched_text = 4, re.search(' '.join(fn + ['[A-Z]'] + ln),n).group(0)

            if em < 11:
                allmatches[a].append((em,k,"FJC Name: " + dict_name,matched_text.strip()))

    if matches == 'exact':
        allmatches = {x : [y for y in allmatches[x] if y[0] <= 2] for x in allmatches if allmatches[x] != []}
    elif matches == 'best':
        allmatches = {x : [y for y in allmatches[x] if y[0] == min([z[0] for z in allmatches[x]])] for x in allmatches if allmatches[x] != []}

        # Consistency checks: make sure that text in string aren't being
        # "tagged" with more than one person's name from namedict
        toremove = set()
        for a in allmatches:
            for a1 in allmatches:
                if len(a) < len(a1) and a in a1:
                    if allmatches[a] == allmatches[a1]:
                        toremove.add(a1)
        for r in toremove: del allmatches[r]

        tosave = list()
        TOKSTRING = ' '.join(tokens)
        for a in sorted([(y[3],x) for x in allmatches for y in allmatches[x]],key=lambda z: len(z[0]),reverse=True):
            pass
            if a[0] in TOKSTRING:
                TOKSTRING = TOKSTRING.replace(a[0],'')
                tosave.append(a[1])
        allmatches = {x:allmatches[x] for x in allmatches if x in tosave}

        ## Reformat objects returned
        tokens = ' '.join(tokens)
        c = 0
        if allmatches != {}:
            for a in sorted([(y[3],x,y[1]) for x in allmatches for y in allmatches[x]],key=lambda z: len(z[0]),reverse=True):
                c += 1
                tokens = tokens.replace(a[0],'['+a[2]+']')
                if a[1] in allmatches:
                    allmatches[c] = allmatches[a[1]]
                    del allmatches[a[1]]

    if easy_output == False:
        return (allmatches, tokens)
    else:
        return [y[1]  for x in allmatches for y in allmatches[x]]
