"""
:Author: Balazs Szigeti <b.islander@protonmail.com>
:Copyright: 2020, DrugNerdsLab
:License: MIT
"""

from psynudge.src.studies import *
from surveygizmo import SurveyGizmo
import dateutil.parser
import datetime
import pytz
import json
import collections
from .. import tokens
import logging
import os

src_folder     = os.path.dirname(os.path.abspath(__file__))
project_folder = os.path.abspath(os.path.join(src_folder, os.pardir))

log_path = os.path.join(project_folder, "psynudge.log")
logging.basicConfig(
    level=logging.DEBUG, filename=log_path, datefmt='%Y-%m-%d - %H:%M:%S', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s')
logging.info('Core imported.')

for study in studies:
    assert study.areTpsConsistent()

Nudge = collections.namedtuple('Nudge', 'userID, surveyId')

def run(studies):

    for study in studies:
        if study.isActive is False:
            continue

        ps_data = get_ps_data(study)

        for timepoint in study.timepoints:
            nudges = collect_nudges(ps_data, timepoint)
            send_nudges(nudges)

def write_last_check_time(project_folder=project_folder):
    """ Updates last_time_checked.txt, which contains the isostring datetime for the last time the nuddger was run (in UTC) """

    file_path = os.path.join(project_folder, 'last_time_checked.txt')
    f = open(file_path, 'w')
    now = datetime.datetime.now().replace(microsecond=0).astimezone(pytz.timezone('UTC'))
    f.write(now.isoformat())
    f.close()
    logging.info('last_time_checked.txt updated.')

def read_last_check_time(project_folder=project_folder):
    """ Reads and returns last_time_checked.txt, which contains the isostring datetime for the last time the nuddger was run (in UTC) """

    file_path = os.path.join(project_folder, 'last_time_checked.txt')
    f = open(file_path, 'r')
    now_str = f.readline()
    assert len(now_str==25)
    f.close()
    logging.info('last_time_checked.txt read.')
    return now_str

def collect_nudges(ps_data, timepoints):

    assert isinstance(study, list)
    assert all([isinstance(element, Timepoint) for element in study])
    assert isinstance(ps_data, list)
    assert all([isinstance(element, dict) for element in ps_data]) #Check keys?

    nudges=[]

    for user in ps_data:
        userID = user['key']
        ustart_loc, ustart_utc = convert_iso2dt(user['date'])

        for timepoint in timepoints:
            surveyId = timepoint.surveyId

            needCompleted = needCompleted(userId, surveyId)
            isCompleted = isCompleted(userId, surveyId)

            if isCompleted is True:
                continue

            # Check whether it is still possible to complete timepoint
            start = ustart_utc + td2tp
            end   = ustart_utc + td2nudge
            isNudge = isWithinWindow(start, end)

            if isNudge is True:
                nudges.append(Nudge(userID, surveyId))

    return nudges

def downloadSurveyData(study, project_folder=project_folder):
    """ Download SG data from SG server and concatenate to single JSON """

    client = SurveyGizmo(api_version='v5',
                         response_type='json',
                         api_token = tokens.api_key,
                         api_token_secret = tokens.secret_key)
    client.config.base_url = 'https://restapi.surveygizmo.eu/'
    tps = list(set(study.tps))

    for tp in tps:

        temp = client.api.surveyresponse.resultsperpage(value=100000).list(tp.surveyId)
        assert isinstance(temp, str)

        sg_data = json.loads(temp)
        assert sg_data['total_pages']==1
        assert sg_data['result_ok'] is True

        if study.type=='stacked':
            outfile=os.path.join(project_folder, "data/{}_{}.json".format(study.name, 'all'))

        if study.type=='indep':
            outfile=os.path.join(project_folder, "data/{}_{}.json".format(study.name, tp.name))

        with open(outfile, 'w+') as outfile:
            json.dump(sg_data['data'], outfile)


""" PLACEHOLDERS """

def isCompleted(userID, surveyId, sgData):
    """ Checks whether given user has completed given survey """
    pass

def getResponseSguid(response):
    """ Returns SGUID of a response. The SGUID can be recorded either as hidden or URL variable, code checks both

        Input:
            response: element of SG_DATA[survey_name]['data']
        Returns:
            SGUID: sguid of response (same as userID)
    """

    sguid_url    = None
    sguid_hidden = None

    try:
        query = SgMiner.get_question(response['survey_data'], 'sguid')
        sguid_hidden = query['answer']
    except (QuestionNotFound, QuestionFoundButNotShown, KeyError):
        pass

    try:
        sguid_url = response['url_variables']['sguid']['value']
    except:
        pass

    if isinstance(sguid_url, str) and isinstance(sguid_hidden, str):
        assert(sguid_url==sguid_hidden) # Both SGUID sources found, but they disagree
        return sguid_url
    elif isinstance(sguid_url, str) and sguid_hidden is None:
        return sguid_url
    elif sguid_url is None and isinstance(sguid_hidden, str):
        return sguid_hidden
    elif sguid_url is None and sguid_hidden is None:
        raise MissingSGUID()

def updateSurveyData(surveyId):
    pass


""" TESTED """
def convert_iso2dt(dstr):
    """ Converts date trings from PS data to datetime.datetime objects.
        Input:
            dstr: isofromatted date string

        Returns:
            dt_loc: datetime obj in participant's local timezone
            dt_utc: datetime obj in UTC timezone
    """

    assert (len(dstr)==25 or (len(dstr)==20) and dstr[-1]=='Z')
    assert dstr[4]=='-'
    assert dstr[7]=='-'
    assert dstr[10:19]=='T00:00:00'

    dt_loc = dateutil.parser.parse(dstr)
    dt_utc = dt_loc.astimezone(pytz.timezone('UTC'))

    return dt_loc, dt_utc

def isWithinWindow(start, end):
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

    now = getNowUtc()

    if (start <= now) and (now <= end):
        return True
    else:
        return False

def getNowUtc():
    """ Wrapper to get current datetime """
    return datetime.datetime.utcnow().astimezone(pytz.timezone('UTC'))
