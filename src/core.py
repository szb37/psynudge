"""
:Author: Balazs Szigeti <b.islander@protonmail.com>
:Copyright: 2020, DrugNerdsLab
:License: MIT

conda env export > environment.yml
conda env create -f environment.yml
"""

from surveygizmo import SurveyGizmo
from .tokens import api_key, secret_key
from .db import getDb
from pony.orm import db_session, commit
import dateutil.parser
import datetime
import logging
import pytz
import json
import os


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

@db_session
def updateNudges(studies, base_dir=base_dir):

    updateData(studies=studies, forceNew=False, base_dir=base_dir)

    for study in studies:
        if study.isActive is False:
            continue

        psData, surveyData = loadStudyData(study)

        for user in psData:
            userId = user['key']
            dtStartLoc = iso2utcdt(user['date'])   # Start datetime in user's local tz
            dtStartUTC = dt2utcdt(dtStartLOC)     # Start datetime in UTC

            for tp in study.timepoints:

                isnudge = isNudge(userId, dtStartUTC, tp, surveyData)
                assert isinstance(isnudge, bool)
                if isnudge is False:
                    continue

                isnudgesent = isNudgeSent(userId, studyId, surveyId)
                assert isinstance(isnudgesent, bool)
                if isnudgesent is True:
                    continue

                Nudge(
                    userId=userId,
                    surveyId=surveyId,
                    studyId=studyId,
                    isSent = False)
                commit()


""" Nudge detection """
@db_session
def isNudgeSent(userId, studyId, surveyId, db):
    """ Returns True/False if the nudge was / wasnt sent already """

    matching_nudge = db.Nudge.select(lambda nudge:
        nudge.userId==userId and
        nudge.surveyId==surveyId and
        nudge.studyId==studyId).fetch()

    assert len(matching_nudge) in [0,1]

    if len(matching_nudge)==0:
        return False

    if len(matching_nudge)==1:
        assert matching_nudge[0].isSent is True
        return True

def isNudge(userId, dtStartUTC, tp, surveyData): # Tested
    """ Returns True if tp is witin nudge time window and tp has not been completed yet, False otherwise """
    assert isinstance(userId, str)
    assert isinstance(dtStartUTC, datetime.datetime)
    assert isinstance(tp, Timepoint)
    assert isinstance(surveyData, list)

    isWithinNW = isWithinNudgeWindow(dtStartUTC, tp)
    if isWithinNW is False:
        return False

    isComp = isCompleted(userId, surveyData)
    if isComp is True:
        return False

    return True

def isWithinNudgeWindow(dtStartUTC, tp): # Tested
    """ Checks if now is within nudge time window of user and tp """
    assert isinstance(tp, Timepoint)
    assert isinstance(dtStartUTC, datetime.datetime)

    start = dtStartUTC + (tp.td2start + tp.td2end)
    end   = dtStartUTC + (tp.td2start + tp.td2end + tp.td2nudge)
    return isWithinWindow(start, end)


""" Survey data exploration """
def isCompleted(userId, surveyData, firstQID=None, lastQID=None): # Tested
    """ Checks whether user has entry in surveyData """

    assert isinstance(userId, str)
    assert isinstance(surveyData, list)
    assert isinstance(firstQID, int)
    assert isinstance(lastQID, int)

    responseFound = False
    for response in surveyData:
        sguid=getResponseSguid(response)
        if sguid==userId:
            responseFound = True
            break

    if responseFound is False:
        return False # Response with SGUID not found

    isStarted  = 'answer' in response['survey_data'][str(firstQID)].keys() # answer key exists iff answer was given
    isFinished = 'answer' in response['survey_data'][str(lastQID)].keys()

    if (isStarted is False) and (isFinished is False):
        return False
    if (isStarted is True) and (isFinished is False):
        return False
    if (isStarted is False) and (isFinished is True):
        assert False
    if (isStarted is True) and (isFinished is True):
        return True

    assert False

def getResponseSguid(response):
    """ Returns SGUID of a response. The SGUID can be recorded either as hidden or URL variable, code checks both """

    sguid_url    = None
    sguid_hidden = None

    for key, value in response['survey_data'].items():
        if value['question']=='Capture SGUID':
            if value['shown'] is True:
                sguid_hidden = value['answer']

    try:
        sguid_url = response['url_variables']['sguid']['value']
    except:
        pass

    if isinstance(sguid_url, str) and isinstance(sguid_hidden, str):
        assert(sguid_url==sguid_hidden)
        return sguid_url
    elif isinstance(sguid_url, str) and sguid_hidden is None:
        return sguid_url
    elif sguid_url is None and isinstance(sguid_hidden, str):
        return sguid_hidden
    elif sguid_url is None and sguid_hidden is None:
        assert False


"""  Disk data manipulations """
def updateData(studies, forceNew=False, base_dir=base_dir):
    """ Updates data from SG """

    lastCheck = readLastCheckTime(base_dir=base_dir)

    for study in studies:
        if study.isActive is False:
            continue

    getData(study, forceNew=False, lastCheck=None, base_dir=base_dir)
    writeLastCheckTime(base_dir=base_dir)

def getData(study, forceNew=False, lastCheck=None, base_dir=base_dir):
    """ Download SG data save """

    assert isinstance(forceNew, bool)
    assert (lastCheck is None) or isinstance(last_check, str)
    if forceNew is True:
        assert lastCheck is None

    client = SurveyGizmo(api_version='v5',
                         response_type='json',
                         api_token = api_key,
                         api_token_secret = secret_key)
    client.config.base_url = 'https://restapi.surveygizmo.eu/'
    tps = list(set(study.tps))

    for tp in tps:

        if (lastCheck is None) or (forceNew is True):
            temp = client.api.surveyresponse.resultsperpage(value=100000).list(tp.surveyId)
        else:
            temp = client.api.surveyresponse.filter(
                field    = 'date_submitted',
                operator = '<',
                value    = last_check).resultsperpage(value=100000).list(tp.surveyId)

        assert isinstance(temp, str)

        sg_data = json.loads(temp)
        assert sg_data['total_pages']==1
        assert sg_data['result_ok'] is True
        nudgelog.info('Data successfully acquired form SG.')

        file_path = getDataFileName(study, tp)

        # Either save new file or append to existing file
        if os.path.isfile(file_path) is True:
            appendData(file_path, sg_data['data'])

        if os.path.isfile(file_path) is False:
            with open(file_path, 'w+') as file:
                json.dump(sg_data['data'], file)

        # no need to iterate over tps with stack studies
        if study.type=='stack':
            return

def loadStudyData(study): # WIP

    psData = get_ps_data(study)
    getData(study=study, lastCheck=None)
    surveyData = read_sg_data()

    return psData, surveyData

def appendData(file_path, data): # Tested

    assert isinstance(data, list)

    with open(file_path, 'r') as file:
        file_data = json.load(file)
        assert isinstance(file_data, list)

    for element in data:
        file_data.append(element)

    with open(file_path, 'w+') as file:
        json.dump(file_data, file)

def getDataFileName(study, tp, base_dir=base_dir): # Tested

    if study.type=='stack':
        return os.path.join(base_dir, "data/{}_{}.json".format(study.name, 'stack'))

    if study.type=='indep':
        return os.path.join(base_dir, "data/{}_{}.json".format(study.name, tp.name))

def writeLastCheckTime(base_dir=base_dir): # Tested
    """ Updates last_time_checked.txt, which contains the isostring datetime for the last time the nuddger was run (in UTC) """

    now = getUtcNow()
    file_path = os.path.join(base_dir, 'last_time_checked.txt')
    with open(file_path, 'w+') as file:
        file.write(now.isoformat())

def readLastCheckTime(base_dir=base_dir): # Tested
    """ Reads and returns last_time_checked.txt, which contains the isostring datetime for the last time the nuddger was run (in UTC) """

    file_path = os.path.join(base_dir, 'last_time_checked.txt')
    with open(file_path, 'r') as file:
        now_str = file.readline()
    assert len(now_str)==25
    return now_str


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
def scheduletester():
    nudgelog.info('Schedueler executed.')




""" Database functions """
@db_session
def updateParticipantFromPS(db, study, ps_file_path=None, ps_data=None):
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
        start_utc = iso2utcdt(entry['date'])

        participant = db.Participant(
            psId = entry['id'],
            study = study,
            whenStart  =  start_utc.isoformat(),
            whenFinish = (start_utc + maxTd).isoformat(),)

        # Create completion entries for participant
        createCompletions(participant=participant, db=db)

def createCompletions(participant, db):
    """ Creates all Completion entries in db from participant """

    for tp in participant.study.timepoints:
        db.Completion(
            participant = participant,
            timepoint = tp)

@db_session
def updateCompletionsFromAlchemy(db, study, alchemy_file_path=None, alchemy_data=None):
    """ Updates the database with the new completions from Alchemer JSON """
    pass

@db_session
def updateParticipantIsActive(db):
    """ updates the isActive field of participant entries """

    now = getUtcNow()
    for participant in db.Participant.select().fetch():
        if iso2utcdt(participant.whenFinish) < now:
            participant.isActive = False

@db_session
def deleteInactiveParticipants(db):
    """ delete participants (and belonging Completion entities) where isActive=False """

    for participant in db.Participant.select(lambda p: p.isActive is False).fetch():
        participant.delete()
