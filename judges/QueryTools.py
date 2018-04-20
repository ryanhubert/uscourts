#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Ryan Hübert
# Department of Political Science
# University of California, Davis

"""
judges.QueryTools v1.0
A set of functions used to query entries in the FJC's database of federal
judges.
WARNING: These tools will be deprecated in future versions.
"""

# Import Modules
import os
import re
import csv
import datetime

current_path = os.path.dirname(os.path.abspath( __file__ ))

# Courts abbreviations
with open(current_path + "/data/courts.csv","r") as csvfile:
    reader = csv.DictReader(csvfile.read().splitlines())
    abbr = {"":""}
    for row in reader:
        abbr[row['full_name']] = row['abbr']

def MakeDate(string):
    """
    Converts ##/##/#### string into a datetime.date object
    """
    if string == "":
        return(datetime.date(9999,12,31))
    elif re.search('^\d\d?/\d\d?/\d\d\d\d$',string):
        return(datetime.datetime.strptime(string, '%m/%d/%Y').date())
    else:
        return('')

def SittingJudges(data,begdate,enddate=None,court_abbr=None):
    """
    Takes a court name and date (or range of dates) and returns IDs for
    all judges sitting in that court for that date (or range of dates)
    [including ones sitting only partially in date range, if relevant].
    """
    court_abbr = court_abbr.upper() if court_abbr != None else None
    if enddate == None:
        enddate = begdate
    alljudges = {'active': [], 'senior': []}
    for k in data:
        for n in range(1,7):
            # if court_abbr in ['',None]:
            #     continue
            if court_abbr != None and abbr[data[k]['Court Name ('+str(n)+')']] != court_abbr:
                continue
            #ndate = MakeDate(data[k]['Nomination Date ('+str(n)+')']) # nomination
            #hdate = MakeDate(data[k]['Hearing Date ('+str(n)+')']) # hearing
            rdate = MakeDate(data[k]['Recess Appointment Date ('+str(n)+')']) # recess appt
            cdate = MakeDate(data[k]['Commission Date ('+str(n)+')']) # commission
            sdate = MakeDate(data[k]['Senior Status Date ('+str(n)+')']) # senior status
            tdate = MakeDate(data[k]['Termination Date ('+str(n)+')']) # termination

            if min(cdate,rdate) > enddate:
                continue
            elif tdate < begdate:
                continue

            if min(sdate,tdate) > enddate:
                days = min((enddate - begdate).days,(enddate - min(cdate,rdate)).days)
                alljudges['active'].append((k,str(n),days))
            elif sdate > begdate and sdate < enddate:
                days1 = min((sdate - begdate).days,(sdate - min(cdate,rdate)).days)
                alljudges['active'].append((k,str(n),days1))
                days2 = min((enddate - sdate).days,(tdate - sdate).days)
                alljudges['senior'].append((k,str(n),days2))
            elif sdate < begdate:
                days = min((enddate - begdate).days,(tdate - begdate).days)
                alljudges['senior'].append((k,str(n),days))
    return(alljudges)

def WhichEntry(data,judgeid,date):
    """
    Takes a judge ID and date and returns a number for the court
    """
    k = judgeid
    toreturn = ["",""]
    for n in range(1,7):
        # Skip entries not matching function arguments
        if MakeDate(data[k]['Commission Date ('+str(n)+')']) < date and MakeDate(data[k]['Termination Date ('+str(n)+')']) > date - datetime.timedelta(days=360):
            toreturn[0] = str(n)
            toreturn[1] = abbr[data[k]['Court Name ('+str(n)+')']]
            break
    return(toreturn)


def IsSenior(data,judgeid,date):
    n = str(WhichEntry(data,judgeid,date)[0])
    sdate = MakeDate(data[judgeid]["Senior Status Date ("+n+")"])
    if sdate < date:
        return(True)
    else:
        return(False)

def FindID(data,lastname):
    for k in data:
        if data[k]["Last Name"].upper() == lastname.upper():
            print((data[k]["First Name"],data[k]["Middle Name"],data[k]["Last Name"]))
            print(k)
            allcourts = list(filter(None,[(abbr[data[k]['Court Name ('+str(n)+')']],data[k]['Commission Date ('+str(n)+')'],data[k]['Termination Date ('+str(n)+')']) if data[k]['Court Name ('+str(n)+')'] != "" else "" for n in range(1,7)]))
            print(allcourts)
            #return(k)
