"""
:Author: Balazs Szigeti <b.islander@protonmail.com>
:Copyright: 2020, DrugNerdsLab
:License: MIT
"""

from surveygizmo import SurveyGizmo
import dateutil.parser
import datetime
import pytz
import json
import collections
from .. import tokens
from psynudge.src.studies import studies

Nudge = collections.namedtuple('Nudge', 'userID, surveyID')

def downloadSurveyData(surveyID):
    """ Download SG data from SG server and concatenate to single JSON """

    client = SurveyGizmo(api_version='v5',
                         response_type='json',
                         api_token = tokens.api_key,
                         api_token_secret = tokens.secret_key)

    client.config.base_url = 'https://restapi.surveygizmo.eu/'

    for study, surveys in survey_keys.studies.items():
        for survey in surveys:

            if survey['remind'] is False:
                #continue
                pass

            id = survey['id']

            temp = client.api.surveyresponse.resultsperpage(value=100000).list(id)
            assert isinstance(temp, str)

            sg = json.loads(temp)

            assert sg['total_pages']==1

def updateSurveyData(surveyID):
    pass

def convert_ps2dt(dstr):
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

def collectNudges(ps_data, timepoints):

    assert isinstance(study, list)
    assert all([isinstance(element, Timepoint) for element in study])
    assert isinstance(ps_data, list)
    assert all([isinstance(element, dict) for element in ps_data]) #Check keys?

    nudges=[]

    for user in ps_data:
        userID = user['key']

        for timepoint in timepoints:
            surveyID = timepoint.surveyID
            isCompleted = isCompleted(userId, surveyId)

            if isCompleted is True:
                continue

            # Check whether it is still possible to complete timepoint
            ustart_loc, ustart_utc = convert_ps2dt(user['date'])
            start = ustart_utc + td2tp
            end   = ustart_utc + td2nudge
            isNudge = isWithinWindow(start, end)

            if isNudge is True:
                nudges.append(Nudge(userID, surveyID))

    return nudges

def isCompleted(userID, surveyID, sgData):
    """ Checks whether given user has completed given survey """
    pass

def isWithinWindow(start, end):
    """ Checks whether there is any uncompleted timepoints within the nudginf time window
        input:
            start: datetime.datetime of start in UTC
            end:  datetime.datetime of end in UTC
    """

    now = datetime.datetime.now()
    if (start <= now) and (now <= end):
        return True
    else:
        return False

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
