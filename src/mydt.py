"""
:Author: Balazs Szigeti <b.islander@protonmail.com>
:Copyright: 2021, DrugNerdsLab
:License: MIT
"""

import dateutil.parser
import datetime
import pytz

""" Datetime manipulations """
def iso2dt(dstr): #Tested
    """ Converts ISO date string to datetime.datetime obj """

    assert isinstance(dstr, str)
    dt_loc = dateutil.parser.parse(dstr)
    return dt_loc

def iso2utcdt(dstr): #Tested
    """ Converts ISO date string to datetime.datetime obj in UTC tz """

    assert isinstance(dstr, str)
    dt_loc = dateutil.parser.parse(dstr)
    dt_utc = dt_loc.astimezone(pytz.timezone('UTC'))

    return dt_utc

def dt2utcdt(dt): #Wrapper
    """ Wrapper to convert datetime.datetime obj to utc timezone"""
    assert isinstance(dt, datetime.datetime)
    return dt.astimezone(pytz.timezone('UTC'))

def getUtcNow(): #Wrapper
    """ Wrapper to get current datetime """
    return datetime.datetime.utcnow().replace(microsecond=0).astimezone(pytz.timezone('UTC'))

def isWithinTimeWindow(start, end): #Tested
    """ Checks whether now is between start and end
        input:
            start: datetime.datetime of start in UTC
            end:   datetime.datetime of end in UTC
    """

    # Timezones need to be represented by pytz module
    assert start.tzname()=='UTC'
    assert isinstance(start.tzinfo, type(pytz.UTC))
    assert end.tzname()=='UTC'
    assert isinstance(end.tzinfo, type(pytz.UTC))

    now = getUtcNow()

    if (start <= now) and (now <= end):
        return True
    else:
        return False
