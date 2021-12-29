from pathlib import Path
from urllib.request import urlopen
from numpy import nan, in1d, atleast_1d, logical_and
from datetime import timedelta
from zipfile import ZipFile
from bs4 import BeautifulSoup
from re import compile
from io import StringIO
from time import sleep
import pandas as pd
from matplotlib.pyplot import figure, show

"""
This function should be used politely and sparingly
"""


# from http.client import HTTPConnection


def plottrains(delays, actual, days, trains, dates, doplot):
    """
    http://stackoverflow.com/questions/11697709/comparing-two-lists-in-python
    can connection be made?
    """
    # set_trace()
    if (
        len(trains) == 2
        and len(actual[trains[0]]) > 0
        and len(actual[trains[1]]) > 0
        and len(dates) > int(days[trains[0]])
    ):
        stations = []
        for t in trains:
            stations.append(delays[t].index.values.tolist())
        overlapind = in1d(stations[0], stations[1])
        overlapstation = atleast_1d(stations[0][overlapind])

        if overlapstation.size == 1:
            overlapstation = overlapstation[0]
            otherind = in1d(stations[1], overlapstation)

            if otherind > overlapind:
                daydiff = int(days[trains[1]]) - 1
                arrival = actual[trains[1]].ix[overlapstation, :-daydiff]
                depart = actual[trains[0]].ix[overlapstation, daydiff:]
            else:
                daydiff = int(days[trains[0]]) - 1
                arrival = actual[trains[0]].ix[overlapstation, :-daydiff]
                depart = actual[trains[1]].ix[overlapstation, daydiff:]

            # set_trace()
            goodtimes = logical_and(depart.notnull(), arrival.notnull()).values
            timelefthours = (
                (depart[goodtimes].values - arrival[goodtimes].values).astype(float) / 1e9 / 3600
            )
            timelefthours = pd.DataFrame(
                timelefthours, index=depart[goodtimes].index, columns=["hoursleft"]
            )

            missedind = (timelefthours < 0).values
            missedhours = timelefthours[missedind]
            if missedind.sum() > 0:
                print(missedhours)
            else:
                print("no missed connections detected for " + str(trains))

            if goodtimes.size < 6 and in1d(["conn", "all"], doplot).any():
                ax = timelefthours.plot(ax=figure().gca(), marker=".", legend=False)
                ax.set_xlabel("date")
            elif in1d(["conn", "all"], doplot).any():
                ax = timelefthours.boxplot(
                    return_type="axes", rot=90, whis=[10, 90], ax=figure().gca()
                )
            ax.set_title(str(trains) + " made connection at " + overlapstation)
            ax.set_ylabel("Hours left to connect")

            show()

            # print(goodtimes)
        # print(depart[goodtimes].index)
        #            print((depart.values-arrival.values))
        #            print((depart.values-arrival.values).astype(float))
        #            print(arrival.values)
        #            print(depart.values)
        elif overlapstation.size == 0:
            print("no connecting station found")
        else:
            print("more than 1 connection found, this case isnt handled yet")
    else:
        print("skipped connection analysis due to missing train info or too few dates")


def plottrain(delay, train, dates, stop, doplot):
    if stop is None:
        stop = -1
        laststop = delay.index[-1]
    else:
        laststop = stop

    if doplot and delay.shape[1] > 0 and in1d(["delay", "all"], doplot).any():
        if delay.shape[1] < 6:
            ax = delay.plot(ax=figure().gca())
            ax.legend(loc="best", fontsize=8)
        else:
            ax = delay.T.boxplot(return_type="axes", rot=90, whis=[10, 90], ax=figure().gca())
        ax.set_xlabel("Station")
        ax.set_ylabel("hours delay")
        ax.set_title(
            "Train #"
            + train
            + " "
            + dates[0].strftime("%Y/%m/%d")
            + " to "
            + dates[-1].strftime("%Y/%m/%d")
        )
        if delay.shape[1] > 1:
            # late vs. date end of route
            ax = delay.ix[stop].plot(
                ax=figure().gca(), linestyle="", marker="*"
            )  # plots last station
            ax.set_title("Hours late to " + laststop)
            ax.set_ylabel("Hours Late")
            ax.set_xlabel("date")
            # histogram
            ax = delay.ix[stop].hist(ax=figure().gca(), normed=1, bins=12)
            ax.set_title("Histogram: Hours late to " + laststop)
            ax.set_xlabel("Hours Late")
            ax.set_ylabel("p(late)")
        show()
    else:
        print("* skipped plotting due to no data")


def tohdf5(fn, data, date):
    from pandas import HDFStore

    h5 = HDFStore(fn)
    h5[date.strftime("d%Y%m%d")] = data
    h5.close()


def tozip(zipfn, txt, date, train):
    from zipfile import ZIP_DEFLATED

    # store as text file like website
    # ziptop = 'test' + buildziptop(train,date)

    with ZipFile(zipfn, "a") as z:
        zippath = buildzippath(train, date)
        z.writestr(zippath, txt, compress_type=ZIP_DEFLATED)


# %%
def getday(datafn, date, train, zipfn, doscrape):
    try:
        txt = filehandler(datafn, train, date)
    except FileNotFoundError:
        if doscrape:
            print("* WARNING: beginning web scrape--be polite, they ban for overuse!")
            url = buildurl(train, date)
            # mass download, throttle to be polite
            sleep(2)
            html = gethtml(url)
            txt = gettxt(html)
        else:
            exit(
                "you dont seem to have the needed data file for Train # "
                + train
                + " on "
                + date.strftime("%Y-%m-%d")
            )

    if zipfn is not None:
        print("writing " + date.strftime("%Y-%m-%d") + " to " + zipfn)
        tozip(zipfn, txt, date, train)

    try:
        data = getdata(txt, date)
    except StopIteration:
        data = None
        print("failed to process " + date.strftime("%Y-%m-%d"))

    return data


# %%


def gettxt(html):
    soup = BeautifulSoup(html)
    txt = soup.get_text()
    return txt


def getdata(txt, datereq):
    # %% first the departures
    data, datestr = getdept(txt, datereq)

    data["sked"] = str2datetime(data["sked"], data["day"], datestr)
    data["act"] = str2datetime(data["act"], data["day"], datestr)

    # %% have to skip ahead a day when delay rolls past midnight!
    # train wouldn't be more than 4 hours early!
    dayflip = (data["act"] - data["sked"]).astype("timedelta64[h]") < -4  # hours
    data.ix[dayflip, "act"] += timedelta(days=1)
    data["delayhours"] = (data["act"] - data["sked"]).astype(
        "timedelta64[m]"
    ) / 60  # .values.astype(float)/1e9/3600

    data["diffdelay"] = data["delayhours"].diff()
    # we don't expect the delay to jump more than 12 hours between stations
    if (data["diffdelay"].abs() > 12).any():
        print("** WARNING: excessive time difference detected, possible parsing error!")
        print(txt)
        print(data)
        data = None

    return data


def getdept(txt, datereq):
    firstheadpat = compile(r"\d{2}/\d{2}/\d{4}")  # not for zip files!
    # trainpat = compile('(?<=\* Train )\d+')
    lastheadpat = compile(r"^\* V")
    datestr = None
    with StringIO(txt) as inpt:
        for line in inpt:
            tmp = firstheadpat.findall(line)
            if len(tmp) > 0:
                datestr = tmp[0]
            if len(lastheadpat.findall(line)) > 0:
                if datestr is None:
                    # must be a zip file where no dates are give
                    datestr = datereq.strftime("%m/%d/%Y")
                break
        # data = read_fwf(inpt,colspecs=[(2,5),(10,15),(16,17),(19,24),(25,30),(31,36)],skiprows=0)
        # data.columns = ['city','skedarv','skeddep','actarv','actdep']
        data = pd.read_fwf(
            inpt,
            colspecs=[(2, 5), (16, 17), (19, 24), (31, 36)],
            index_col=0,
            header=None,
            skiprows=0,
        )

    # %% append last arrival (destination)
    arv = getarv(txt)
    # %% drop blank rows before appending arrival
    data = data.dropna(axis=0, how="all")  # needed for trailing blank lines
    data = data.replace("*", nan)  # now that blank lines are gone, we swap for nan

    data.ix[-1] = arv.ix[0]  # we know arrival is one line, the last line of the file
    data.columns = ["day", "sked", "act"]

    return data, datestr


def getarv(txt):
    llrgx = compile("(?<=\n).+(?=\r*\n+$)")  # no \r in lookbehind
    lastline = llrgx.findall(txt)[0]

    with StringIO(lastline) as inpt:
        arv = pd.read_fwf(
            inpt,
            colspecs=[(2, 5), (7, 8), (10, 15), (25, 30)],
            index_col=0,
            header=None,
            skiprows=0,
            converters={1: str},
        )

    return arv


def str2datetime(data, day, datestr):
    dstr = data.str.extract(r"(\d+)")
    ampm = data.str.extract("([AP])") + "M"
    dint = dstr.astype(float)  # int can't use nan

    # ZERO PAD HOURS
    for i, sd in enumerate(dint):
        if sd != "NaN":
            dstr[i] = "{:04d}".format(sd.astype(int))
    dstr = datestr + "T" + dstr + ampm  # add date to front

    # finally put to datetime
    datadt = pd.to_datetime(
        dstr, format="%m/%d/%YT%I%M%p", utc=True
    )  # seems to put time-zone aware to Eastern time..
    # multi-day trips
    datadt[day == "2"] += timedelta(days=1)  # NOT relativedelta(days=1)
    datadt[day == "3"] += timedelta(days=2)

    return datadt


def buildurl(trainnum, date):
    url = "http://dixielandsoftware.net/cgi-bin/gettrain.pl?seltrain="
    url += str(trainnum)
    url += "&selyear=" + date.strftime("%Y")
    url += "&selmonth=" + date.strftime("%m")
    url += "&selday=" + date.strftime("%d")
    return url


def buildziptop(train, date):
    return Path(date.strftime("%Y")) / (str(train) + ".zip")


def buildzippath(train, date):
    return Path(train) / "".join([train, "_", date.strftime("%Y%m%d"), ".txt"])


def filehandler(fn, train, date):
    fn = Path(fn).expanduser()

    if fn.suffix in "html":  # single train
        with open(fn, "r") as f:
            html = f.read()
        txt = [gettxt(html)]
    elif fn.suffix == "txt":  # single train
        with open(fn, "r") as f:
            txt = [f.read()]
    elif fn.suffix == "":  # single or multiple trains
        try:
            ziptop = buildziptop(train, date)
            with ZipFile(ziptop, "r") as z:
                zippath = buildzippath(train, date)
                with z.open(zippath, "r") as f:
                    txt = f.read().decode("utf-8")
        except KeyError:
            print("I dont find", zippath)
            txt = None
    else:
        raise ValueError("I dont know how to parse", fn)

    return txt


def gethtml(url):
    response = urlopen(url)
    html = response.read().decode("utf-8")
    # session.request("GET", url)
    # response = session.getresponse()
    # if response.status == 200:
    #     html = response.read().decode('utf-8')
    # elif response.status == 301:
    #     print('** 301 moved to ' + str(response.getheader('Location')))
    # else:
    #     print('** error ' + str(response.status) + '  could not read ' + url)
    #     html = '** could not read ' + url
    return html
