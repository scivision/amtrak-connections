#!/usr/bin/env python3
import pandas as pd
from dateutil import parser

#
from amtrakconn import getday, plottrain, plottrains

"""
capabilities:
1) polite scraping of Amtrak Status Reports
2) storing scrapes in same format as site archives (nested zip)
3) statistical analysis using pandas dataframes

TODO:
1) make scraping more polite with keep alive
2) make "hours left to make connection" work more reliably with missing data

EXAMPLE USE (assuming you've already downloading ZIP archives from dixielandsoftware.net)
./amtrak.py 29 7 -d 2013-05-15 2013-05-31
that examines connections between the Capitol Limited to the Empire Builderfor the later half of May 2013
"""


def main(dates, datafn, trains, stop, makeplot, zipfn, doscrape):
    delays = {}
    actual = {}
    days = {}

    if datafn is None:
        autodate = True
    else:
        autodate = False

    for train in trains:
        delays[train] = pd.DataFrame()
        actual[train] = pd.DataFrame()

        for date in dates:
            if autodate:
                datafn = date.strftime("%Y")  # defaults to nested zip file
            pn = date.strftime("%Y/%m/%d")
            daydata = getday(datafn, date, train, zipfn, doscrape)
            if daydata is not None:
                delays[train][pn] = daydata["delayhours"]
                actual[train][pn] = daydata["act"]
                days[train] = daydata["day"].max()
            if daydata is None or daydata["delayhours"].isnull().all():
                print("* Note: no data for train " + train + " on " + date.strftime("%Y/%m/%d"))

        #        if h5fn is not None:
        #            print('** warning this has not been tested at all')
        #            tohdf5(h5fn,daydata,date)
        plottrain(delays[train], train, dates, stop, makeplot)

    plottrains(delays, actual, days, trains, dates, makeplot)

    return delays


if __name__ == "__main__":
    from argparse import ArgumentParser

    p = ArgumentParser(description="Loads Google Forms responses XLS and analyses")
    p.add_argument("train", help="train number", type=str, nargs="+")
    p.add_argument(
        "-d",
        "--date",
        help="START [STOP] date range of train, format YYYY-MM-DD",
        type=str,
        nargs="+",
        required=True,
    )
    p.add_argument(
        "-f",
        "--file",
        help="load disk html, txt, zip file (no auto download)",
        type=str,
        default=None,
    )
    p.add_argument("-m", "--makeplot", help="plots to make (default all)", type=str, default="all")
    p.add_argument("--h5", help="write hdf5 of data to this file", type=str, default=None)
    p.add_argument("--zip", help="write zip like the website does", type=str, default=None)
    p.add_argument("--scrape", help="scrape from web--use with caution!", action="store_true")
    p.add_argument("-s", "--stop", help="three-letter station to debark", type=str, default=None)
    ar = p.parse_args()
    makeplot = ar.makeplot

    if ar.scrape and ar.zip:
        doscrape = True
    elif ar.scrape and not ar.zip:
        doscrape = False
        print("disabled scraping since you didnt choose to save as zip (dont be wasteful)")
    else:
        doscrape = False

    if len(ar.date) != 2:
        dates = [parser.parse(d) for d in ar.date]
    else:  # len(ar.date) == 2:
        dates = pd.date_range(start=ar.date[0], end=ar.date[1])
    if len(dates) == 0:
        exit("Your specified date range doesnt make sense")

    delay = main(dates, ar.file, ar.train, ar.stop, makeplot, ar.zip, doscrape)
