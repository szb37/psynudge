"""
Functions to manipulate datetime objects
:Author: Balazs Szigeti <szbazsu@gmail.com>
:Copyright: 2019, DrugNerdsLab
:License: MIT
"""

from mcrds.src.globals import *
import datetime
import pytz
import copy

def dt2str(dt):
    """ Convert datetime to string in format YYYY_MM_DD_HH_MM_SS """

    assert isinstance(dt, datetime.datetime)
    return dt.strftime('%Y_%m_%d_%H_%M_%S')

def str2utcdt(isodtstr, source='PS', returnTz=False):
    """ Converts various date/time strs to UTC localized datetime obj """

    assert isinstance(isodtstr, str)

    if source =='PS':

        # Case w time zone offset
        if len(isodtstr)==25 and isodtstr[-3] == ':':
            start_str_formatted = isodtstr[:-3] + isodtstr[-2:]
            dt = datetime.datetime.strptime(start_str_formatted, "%Y-%m-%dT%H:%M:%S%z")
            dt_localized = dt.astimezone(pytz.timezone('UTC'))

            if returnTz is False:
                return dt_localized

            return (dt_localized, dt.tzinfo)

        # Case wo time zone offset
        if len(isodtstr)==20 and isodtstr[-1] == 'Z':
            start_str_formatted = isodtstr[:-1]
            dt = datetime.datetime.strptime(start_str_formatted, "%Y-%m-%dT%H:%M:%S")
            dt_localized = pytz.timezone('UTC').localize(dt)

            if returnTz is False:
                return dt_localized

            return (dt_localized, dt_localized.tzinfo)

        raise Exception('Unexcepcted datetime string from PS data source.')

    if source =='SG':

        assert(len(isodtstr)== 23)
        assert(isodtstr[4] == '-' and isodtstr[7] == '-')
        assert(isodtstr[13] == ':' and isodtstr[16] == ':')
        assert(isodtstr[10] == ' ' and isodtstr[19] == ' ')

        year  = int(isodtstr[0:4])
        month = int(isodtstr[5:7])
        day   = int(isodtstr[8:10])
        hour  = int(isodtstr[11:13])
        min   = int(isodtstr[14:16])
        sec   = int(isodtstr[17:19])
        tz    = isodtstr[-3:]

        assert tz in ['EDT', 'EST']
        if tz=='EDT':
            tz ='EST5EDT' # pytz recognizes EDT as EST5EDT

        # Convert time to UTC
        dt = datetime.datetime(year, month, day, hour, min, sec)
        dt = pytz.timezone(tz).localize(dt)
        return dt.astimezone(pytz.timezone('UTC'))

    if source == 'CBS':

        if isodtstr[-5:] == '00:00':  # This is isoformat
            dt = datetime.datetime.strptime(isodtstr[:-6], "%Y-%m-%dT%H:%M:%S")
        elif isodtstr[-5:] == '.000Z': # This is from CBS
            dt = datetime.datetime.strptime(isodtstr[:-5], "%Y-%m-%dT%H:%M:%S")
        else:
            raise Exception('Unrecognized datetime string: {}.'.format(isodtstr))

        dt_localized = pytz.timezone('UTC').localize(dt)

        if returnTz is True:
            return (dt_localized, dt_localized.tzinfo)
        elif returnTz is False:
            return dt_localized

def get_timepoints(start_date_str):

    start_dt = str2utcdt(isodtstr=start_date_str, returnTz=False)
    timepoints = copy.deepcopy(TIMEPOINTS)
    timepoints['kickoff'] = start_dt

    timepoints['pre']['start']  = timepoints['kickoff'] - datetime.timedelta(days=14)
    timepoints['pre']['end']    = timepoints['kickoff']

    timepoints['w1s1']['start'] = timepoints['kickoff'] + datetime.timedelta(days=3)
    timepoints['w1s1']['end']   = timepoints['w1s1']['start'] + datetime.timedelta(days=1)
    timepoints['w1s2']['start'] = timepoints['kickoff'] + datetime.timedelta(days=6)
    timepoints['w1s2']['end']   = timepoints['w1s2']['start'] + datetime.timedelta(days=1)

    timepoints['w2s1']['start'] = timepoints['kickoff'] + datetime.timedelta(days=10)
    timepoints['w2s1']['end']   = timepoints['w2s1']['start'] + datetime.timedelta(days=1)
    timepoints['w2s2']['start'] = timepoints['kickoff'] + datetime.timedelta(days=13)
    timepoints['w2s2']['end']   = timepoints['w2s2']['start'] + datetime.timedelta(days=1)

    timepoints['w3s1']['start'] = timepoints['kickoff'] + datetime.timedelta(days=17)
    timepoints['w3s1']['end']   = timepoints['w3s1']['start'] + datetime.timedelta(days=1)
    timepoints['w3s2']['start'] = timepoints['kickoff'] + datetime.timedelta(days=20)
    timepoints['w3s2']['end']   = timepoints['w3s2']['start'] + datetime.timedelta(days=1)

    timepoints['w4s1']['start'] = timepoints['kickoff'] + datetime.timedelta(days=24)
    timepoints['w4s1']['end']   = timepoints['w4s1']['start'] + datetime.timedelta(days=1)
    timepoints['w4s2']['start'] = timepoints['kickoff'] + datetime.timedelta(days=27)
    timepoints['w4s2']['end']   = timepoints['w4s2']['start'] + datetime.timedelta(days=1)

    timepoints['post']['start'] = timepoints['kickoff'] + datetime.timedelta(days=28)
    timepoints['post']['end']   = timepoints['post']['start'] + datetime.timedelta(days=7)

    timepoints['ltfu']['start'] = timepoints['kickoff'] + datetime.timedelta(days=56)
    timepoints['ltfu']['end']   = timepoints['ltfu']['start'] + datetime.timedelta(days=7)

    return timepoints
