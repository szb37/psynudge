"""
:Author: Balazs Szigeti <b.islander@protonmail.com>
:Copyright: 2020, DrugNerdsLab
:License: MIT

conda env export > environment.yml
conda env create -f environment.yml
"""

from surveygizmo import SurveyGizmo
from .tokens import sg_key, sg_secret, ps_key, ps_secret
from .db import get_db
from pony.orm import db_session, commit
import dateutil.parser
import datetime
import requests
import logging
import pytz
import json
import os

#TODO: what happens when user changes start date

src_folder = os.path.dirname(os.path.abspath(__file__))
base_dir   = os.path.abspath(os.path.join(src_folder, os.pardir))

log_path = os.path.join(base_dir, "psynudge.log")
logging.basicConfig(
    level=logging.INFO,
    filename=log_path,
    datefmt='%Y-%m-%d - %H:%M:%S',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s')
nudgelog = logging.getLogger("nudgelog")
nudgelog.info('Core imported.')


""" Database functions """
@db_session # tested
def updateParticipant(db, study, ps_file_path=None, ps_data=None):
    """ Updates the database with new entries from PS JSON """

    # Get data either from file or directly as a json
    if ps_data is None:
        assert isinstance(ps_file_path, str)
        with open(ps_file_path, 'r') as j:
            ps_data = json.loads(j.read())

    if ps_file_path is None:
        assert isinstance(ps_data, list)

    # Add new entries to DB
    for entry in ps_data:

        # Check if participant exists
        psId_matches = db.Participant.select(lambda part: part.psId==entry['id']).fetch()
        assert len(psId_matches) in [0,1]
        if len(psId_matches)==1:
            continue

        # Get trial boundary dates
        maxTd = study.getFurthestTd() #maximum timedelta

        if ':' in str(entry['date']): # If : in string, then str is isoformat, if not, then unix seconds
            start_utc = iso2utcdt(entry['date'])
        else:
            start_utc = iso2utcdt(datetime.datetime.fromtimestamp(entry['date']).isoformat())

        participant = db.Participant(
            psId = entry['id'],
            study = study,
            whenStart  = start_utc.isoformat(),
            whenFinish = (start_utc + maxTd).isoformat(),)

        # Create completion entries for participant
        createCompletion(participant=participant, db=db)

@db_session # tested
def updateIndepStudyIsComplete(db, tp, alchemy_file_path=None, alchemy_data=None):
    """ Updates the database with the new completions from Alchemer JSON for independent studies """

    assert tp.study.type.type=='indep'

    # Get data either from file or directly as a json
    if alchemy_data is None:
        assert isinstance(alchemy_file_path, str)
        with open(alchemy_file_path, 'r') as j:
            alchemy_data = json.loads(j.read())

    if alchemy_file_path is None:
        assert isinstance(alchemy_data, list)

    for response in alchemy_data['data']:

        psId = getResponseSguid(response)
        if psId is None:
            continue

        isComplete = assessIsComplete(response=response, tp=tp)

        completion = db.Completion.select(lambda c:
            c.participant.psId==psId and
            c.timepoint==tp).fetch()

        if len(completion)!=1: # TODO: why not assert?!?!?!?!
            continue

        completion[0].isComplete = isComplete

@db_session # tested
def updateStackStudyIsComplete(db, study, alchemy_file_path=None, alchemy_data=None):
    """ Updates the database with the new completions from Alchemer JSON for stacked studies """

    assert study.type.type=='stack'

    # Get data either from file or directly as a json
    if alchemy_data is None:
        assert isinstance(alchemy_file_path, str)
        with open(alchemy_file_path, 'r') as j:
            alchemy_data = json.loads(j.read())

    if alchemy_file_path is None:
        assert isinstance(alchemy_data, list)

    # Update data file
    for response in alchemy_data['data']:

        psId = getResponseSguid(response)
        if psId is None:
            continue

        for tp in study.timepoints:

            isComplete = assessIsComplete(response=response, timepoint=tp)

            completion = db.Completion.select(lambda c:
                c.participant.psId==psId and
                c.timepoint==tp).fetch()

            if len(completion)!=1:
                continue

            completion[0].isComplete = isComplete

@db_session # tested
def updateCompletionIsNeeded(db):
    """ updates the isNeeded attribute of Completion entries """

    now = getUtcNow()
    for completion in db.Completion.select().fetch():

        expStartDtUtc = iso2utcdt(completion.participant.whenStart) # start of the experiment
        startDtUtc = expStartDtUtc + completion.timepoint.td2start # start of the timepoint
        finishDtUtc = startDtUtc + completion.timepoint.td2end # end of the tmepoint

        if (finishDtUtc > now):
            completion.isNeeded = False

        if (startDtUtc < now):
            completion.isNeeded = False

        if (finishDtUtc > now) and (startDtUtc < now):
            completion.isNeeded = True

@db_session
def updateCompletionIsNudge(db):
    """ Updates isNudge field of Completion entries """

    for completion in db.Completion.select().fetch():

        if completion.participant.study.isActive is False:
            continue

        isnudge = isNudge(db=db, completion=completion)
        assert isinstance(isnudge, bool)
        completion.isNudge = isnudge

def assessIsComplete(response, tp):
    """ Decides whether timepoint is completed """

    isStarted  = 'answer' in response['survey_data'][str(tp.firstQID)].keys() # answer key exists iff answer was given
    isFinished = 'answer' in response['survey_data'][str(tp.lastQID)].keys()
    isComplete = None

    if (isStarted is False) and (isFinished is False):
        isComplete = False
    if (isStarted is True) and (isFinished is False):
        isComplete = False
    if (isStarted is False) and (isFinished is True):
        isComplete = False
    if (isStarted is True) and (isFinished is True):
        isComplete = True

    assert isinstance(isComplete, bool)
    return isComplete

def createCompletion(db, participant):
    """ Creates all Completion entries in db from participant """

    for tp in participant.study.timepoints:
        db.Completion(
            participant = participant,
            timepoint = tp) # tested

@db_session
def deletePastParticipant(db):
    """ delete participants (and belonging Completion entities) where isActive=False """

    now = getUtcNow()
    for participant in db.Participant.select().fetch():
        if iso2utcdt(participant.whenFinish) < now:
            participant.delete()


""" Nudge detection """
def isNudge(db, completion):
    """ Returns True if (tp is witin nudge time window) and (tp has not been completed yet) and (last nudge was sent more then 24h ago), False otherwise """
    assert isinstance(completion, Completion)

    # Check if we are within Nudge time window
    dtStartUTC = iso2utcdt(completion.participant.whenStart)
    isWithinNW = isWithinNudgeWindow(dtStartUTC, tp)
    if isWithinNW is False:
        return False

    # Check if completed already
    if completion.isComplete is True:
        return False

    isnudgetimely = isNudgeTimely(completion=completion)
    if isnudgetimely is False:
        return False

    return True

def isWithinNudgeWindow(dtStartUTC, tp): # Tested
    """ Checks if now is within nudge time window of user and tp """
    assert isinstance(tp, Timepoint)
    assert isinstance(dtStartUTC, datetime.datetime)

    start = dtStartUTC + (tp.td2start + tp.td2end)
    end   = dtStartUTC + (tp.td2start + tp.td2end + tp.td2nudge)
    return isWithinWindow(start, end)

def isNudgeTimely(completion):
    """ Returns True if last nudge was sent > 23:50h ago, False otherwise """

    dtNow = getUtcNow()
    dtlastNudgeSend = iso2utcdt(completion.lastNudgeSend)

    if (dtNow - dtlastNudgeSend) > datetime.timedelta(days=0.95): # 0.95 instead of 1 for error tolerance
        return True

    return False


""" Data acess and archieve """
def getPsData(study, base_dir=base_dir):
    """ Updates participant info from PS """

    response = requests.get('https://dashboard-api.psychedelicsurvey.com/v2/studies/{}/participants'.format(study.psId),
     headers={
        'ClientSecret': ps_secret,
        'ClientID': ps_key,
         }
    )

    assert response.status_code==200
    return response.json()

def getSgData(study, tp=None, forceNew=False, lastSgCheck=None):
    """ Download SG data save """

    if tp is None:
        assert study.type=='stack'
    else:
        assert study.type=='indep'

    assert isinstance(forceNew, bool)
    assert isinstance(lastSgCheck, str)

    client = SurveyGizmo(api_version='v5',
                         response_type='json',
                         api_token = sg_key,
                         api_token_secret = sg_secret)
    client.config.base_url = 'https://restapi.surveygizmo.eu/'
    tps = list(set(study.tps))

    if (lastSgCheck is None) or (forceNew is True):
        temp = client.api.surveyresponse.resultsperpage(value=100000).list(tp.surveyId)
    else:
        temp = client.api.surveyresponse.filter(
            field    = 'date_submitted',
            operator = '<',
            value    = lastSgCheck).resultsperpage(value=100000).list(tp.surveyId)

    sg_data = json.loads(temp)
    assert sg_data['total_pages']==1
    assert sg_data['result_ok'] is True

    nudgelog.info('SG data downloaded, study:{}, tp{}:.'.format(study.name, tp.name))

    return sg_data

def getDataFilePath(study, tp=None, source=None, base_dir=base_dir):
    """ Return the intended filepath when data files are saved """

    base_dir='/home/bazsi'
    assert source in ['sg', 'ps']

    if (source=='ps'):
        assert tp is None
        return os.path.join(base_dir, "data/{}_{}_to({}).json".format(
            study.name,
            'ps',
            getUtcNow().isoformat()[:-6]
            ))

    if (source=='sg') and (study.type=='stack'):
        return os.path.join(base_dir, "data/{}_{}_{}_from({})_to({}).json".format(
            study.name,
            'sg',
            'stack',
            study.timepoints.select().first().  lastSgCheck[:-6],
            getUtcNow().isoformat()[:-6]
            ))

    if (source=='sg') and (study.type=='indep'):
        return os.path.join(base_dir, "data/{}_{}_{}_from({})_to({}).json".format(
            study.name,
            'sg',
            tp.name,
            tp.lastSgCheck[:-6],
            getUtcNow().isoformat()[:-6]
            ))

    assert False

def saveData(data, filepath):
    """ Saves data locally """
    #import pdb; pdb.set_trace()
    with open(filepath, 'w+') as file:
        json.dump(data, file)


""" Datetime manipulations """
def iso2dt(dstr): # Tested
    """ Converts ISO date string to datetime.datetime obj """

    assert isinstance(dstr, str)
    dt_loc = dateutil.parser.parse(dstr)
    return dt_loc

def iso2utcdt(dstr): # Tested
    """ Converts ISO date string to datetime.datetime obj in UTC tz """

    assert isinstance(dstr, str)
    dt_loc = dateutil.parser.parse(dstr)
    dt_utc = dt_loc.astimezone(pytz.timezone('UTC'))

    return dt_utc

def dt2utcdt(dt): # Wrapper
    """ Wrapper to convert datetime.datetime obj to utc timezone"""
    assert isinstance(dt, datetime.datetime)
    return dt.astimezone(pytz.timezone('UTC'))

def getUtcNow(): # Wrapper
    """ Wrapper to get current datetime """
    return datetime.datetime.utcnow().replace(microsecond=0).astimezone(pytz.timezone('UTC'))

def isWithinWindow(start, end): # Tested
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


""" Cron run check """
def scheduleTester():
    nudgelog.info('Schedueler executed.')
