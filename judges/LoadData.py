#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Ryan Hübert
# Department of Political Science
# University of California, Davis

"""
judges.LoadData v2.0
This script takes the Federal Judicial Center's Biographical Directory of 
Article III Federal Judges and generates a json file formatted for easy 
import/use in other federal courts-related research applications.

New in v2.0: function to reshape (and shrink) data for use in other applications
"""

# Import Modules
import os, csv, json, re
from urllib.request import urlopen
import datetime

def UpdateData(directory=os.getcwd(), fjclink = 'https://www.fjc.gov/sites/default/files/history/judges.csv'):
    # Download most recent judicial biography
    print('Downloading updated data from: ' + fjclink)
    if not re.search('/ *$',directory):
        directory = directory.strip() + '/'
    try:
        urlopen(fjclink)
    except:
        print("FJC biographical data no longer stored at " + fjclink)
        print("PLEASE ENTER A VALID LINK TO judges.csv FROM THE FOLLOWING DOMAIN: https://www.fjc.gov/.")
    with urlopen(fjclink) as webpage:
        reader2 = csv.DictReader(webpage.read().decode('utf-8').splitlines())
        fjcdict = {}
        for row in reader2:
            fjcdict[row['nid']] = row

    # Save as JSON
    if os.path.exists(directory + "judges.json"):
        modtime = re.sub('[^\d]','',str(datetime.datetime.fromtimestamp(os.stat(directory+"judges.json").st_mtime))[:-2])
        os.rename(directory + "judges.json",directory + "judges" + modtime + ".json")
    with open(directory + 'judges.json', 'w') as fp:
        json.dump(fjcdict, fp, sort_keys=True, indent=4)

    return(fjcdict)

def LoadData(directory=os.getcwd()):
    if not re.search('/ *$',directory):
        directory = directory.strip() + '/'
    if os.path.exists(directory + "judges.json"):
        with open(directory + 'judges.json', 'r') as fp:
            fjcdict = json.load(fp)
        return(fjcdict)
    elif input("Local data does not exist. Download new version? [y/n] ") == "y":
        fjcdict = UpdateData(directory)
        return(fjcdict)
    else:
        raise Exception("No data loaded!")

def ReshapeData(dictionary, directory=os.getcwd(), other_judges=False):
    smap = [s.lower().split('\t') for s in open(directory + '/data/states.txt').read().split('\n')]
    smap = sorted(smap, key=lambda x: len(x[1]), reverse=True)

    cmap = {'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5,
            'sixth': 6, 'seventh': 7, 'eighth': 8, 'ninth': 9, 'tenth': 10,
            'eleventh': 11, 'federal': 'f', 'district of columbia': 'dc'}
    dmap = {'northern': 'nd', 'eastern': 'ed', 'central': 'cd',
            'middle': 'md', 'western': 'wd', 'southern': 'sd'}

    omap = {'Supreme Court of the United States'.lower(): 'ussc',
            'Customs Court'.lower(): 'cit',
            'Court of International Trade'.lower(): 'cit',
            'Court of Customs and Patent Appeals'.lower(): 'cpa',
            'Court of Claims'.lower(): 'cc'}

    for k in dictionary:
        courts = []

        # Add entry for magistrate service
        for x in dictionary[k]:
            if "Other Federal Judicial Service" in x and "U.S. Magistrate" in dictionary[k][x]:
                term = [x.strip() for x in re.findall('(?:[^d]|^)([\d\- ]+)(?:[^d]|$)', dictionary[k][x])
                        if x not in [' ', '-'] and '-' in x]
                term = [min(set([int(y) for x in term for y in x.split('-')])),
                        max(set([int(y) for x in term for y in x.split('-')]))]
                court = [dictionary[k][x].lower(),
                         'mag',
                         None,
                         None,
                         datetime.datetime.strptime('01/01/' + str(term[0]), '%m/%d/%Y').date(),
                         datetime.datetime.strptime('12/31/' + str(term[1]), '%m/%d/%Y').date()]
                courts.append(court)

        # Add entries for each Article 3 appointment
        for c in range(1, 7):
            if dictionary[k]['Court Name (' + str(c) + ')'] in ['', ' ']:
                continue
            court = [dictionary[k]['Court Name (' + str(c) + ')'].lower(),
                     'art3',
                     dictionary[k]['Nomination Date (' + str(c) + ')'].strip(),
                     dictionary[k]['Confirmation Date (' + str(c) + ')'].strip(),
                     dictionary[k]['Commission Date (' + str(c) + ')'].strip(),
                     dictionary[k]['Termination Date (' + str(c) + ')'].strip()
                     ]
            court = [datetime.datetime.strptime(x, '%m/%d/%Y').date() if re.search('\d+/\d+/\d+',x) else x for x in court]
            courts.append(court)

        # Abbreviate court names
        for c in courts:
            sta = [x[0] for x in smap if x[1] in c[0]]
            dis = [dmap[x] for x in dmap if x in c[0]]
            cir = [cmap[x] for x in cmap if x in c[0] and 'circuit' in c[0]]
            oth = [omap[x] for x in omap if x in c[0]]

            if oth != [] and all(x == [] for x in [sta, dis, cir]):
                c[0] = oth[0]

            elif sta == ['dc']:
                c[0] = 'cadc' if cir != [] else 'dcd'

            elif cir != [] and all(x == [] for x in [dis, oth, sta]):
                c[0] = 'ca' + str(cir[0])

            elif sta != [] and all(x == [] for x in [oth, cir, dis]):
                c[0] = sta[0] + 'd'

            elif sta != [] and dis != [] and all(x == [] for x in [oth, cir]):
                c[0] = sta[0] + dis[0]

            else:
                c[0] = 'other'

        dictionary[k]['Courts'] = courts

    dictionary = dict({x: {"First Name": dictionary[x]["First Name"],
                    "Suffix": dictionary[x]["Suffix"],
                    "Middle Name": dictionary[x]["Middle Name"],
                    "Last Name": dictionary[x]["Last Name"],
                    "Courts": dictionary[x]["Courts"]}
                for x in dictionary})

    # Some simple formatting
    dictionary = {x: {y: re.sub('[\[\]]', '', dictionary[x][y].strip()) if type(dictionary[x][y]) is str else dictionary[x][y] for y in dictionary[x]} for x in dictionary}

    if other_judges:
        with open(os.path.dirname(os.path.realpath(__file__))+'/data/magistrate-list.csv', 'r') as mf:
            for k in csv.DictReader(mf):
                if k['\ufeffusdc_id'] == "":
                    continue

                ln = k['Last Name']
                fn = k["First Name"]
                mn = k["Middle Name"]

                newrow = [k["Appointing Court"],
                          'mag',
                          None,
                          None,
                          None, #datetime.datetime.strptime('01/01/1994','%m/%d/%Y').date(),
                          None
                          ]

                dictionary[k['\ufeffusdc_id']] = {
                    "First Name": fn, "Middle Name": mn, "Last Name": ln, "Suffix": k["Suffix"],
                    "Courts": [newrow]}


    # Magistrate judge date clean up
    for k in dictionary:
        minCommissionDate = [x[4] for x in dictionary[k]["Courts"] if x[1] == 'art3']
        minCommissionDate = [x for x in minCommissionDate if type(x) is datetime.date]
        minCommissionDate =  min(minCommissionDate) if minCommissionDate != [] else []
        maxMagistrateDate = [x[5] for x in dictionary[k]["Courts"] if x[1] == 'mag']
        maxMagistrateDate = [x for x in maxMagistrateDate if type(x) is datetime.date]
        maxMagistrateDate = max(maxMagistrateDate) if maxMagistrateDate != [] else []
        if minCommissionDate != [] and maxMagistrateDate != []:
            for x in dictionary[k]["Courts"]:
                if maxMagistrateDate == x[5]:
                    x[5] = minCommissionDate
    newdict = {}
    for k in dictionary:
        newdict[k] = {x: dictionary[k][x] for x in dictionary[k] if x != "Courts"}
        newdict[k]['Courts'] = {}
        sn = 0
        for x in dictionary[k]['Courts']:
            sn = sn + 1
            newdict[k]['Courts'][sn] = {'judge_type': x[1] if x[1] != '' else None,
                                        'service_number': sn,
                                        'court': x[0],
                                        'date_nomination': x[2] if x[2] != '' else None,
                                        'date_confirmation': x[3] if x[3] != '' else None,
                                        'date_commission': x[4] if x[4] != '' else None,
                                        'date_termination': x[5] if x[5] != '' else None}

    return newdict