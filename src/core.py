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
import datetime
from .mydt import *
import requests
import logging
import pytz
import json
import os

#TODO: what happens when user changes start date
#TODO: db integrty: check that all TPs have the same lastSGCheck for stack studies
#TODO: db integrty: check that all TPs have the same surveyId for stack studies
#TODO: lastPsCheck update in controller


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
@db_session
def updateParticipant(db, study, ps_file_path=None, ps_data=None): #Tested
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

@db_session
def updateIsCompleteIndep(db, tp, alchemy_file_path=None, alchemy_data=None): #Tested
    """ Updates the database with the new completions from Alchemer JSON for independent studies """

    assert tp.study.type.type=='indep'

    # Get data either from file or directly as a json
    if alchemy_data is None:
        assert isinstance(alchemy_file_path, str)
        with open(alchemy_file_path, 'r') as j:
            alchemy_data = json.loads(j.read())

    if alchemy_file_path is None:
        assert isinstance(alchemy_data, dict)

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

@db_session
def updateIsCompleteStack(db, study, alchemy_file_path=None, alchemy_data=None): #Tested
    """ Updates the database with the new completions from Alchemer JSON for stacked studies """

    assert study.type.type=='stack'

    # Get data either from file or directly as a json
    if alchemy_data is None:
        assert isinstance(alchemy_file_path, str)
        with open(alchemy_file_path, 'r') as j:
            alchemy_data = json.loads(j.read())

    if alchemy_file_path is None:
        assert isinstance(alchemy_data, dict)

    # Update data file
    for response in alchemy_data['data']:

        psId = getResponseSguid(response)
        if psId is None:
            continue

        for tp in study.timepoints:

            isComplete = assessIsComplete(response=response, tp=tp)

            completion = db.Completion.select(lambda c:
                c.participant.psId==psId and
                c.timepoint==tp).fetch()

            if len(completion)!=1:
                continue

            completion[0].isComplete = isComplete

def assessIsComplete(response, tp): #Imp tested
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

def createCompletion(db, participant): #Imp tested
    """ Creates all Completion entries in db from participant """

    for tp in participant.study.timepoints:
        db.Completion(
            participant = participant,
            timepoint = tp)

@db_session
def deletePastParticipant(db): #Tested
    """ delete participants (and belonging Completion entities) where isActive=False """

    now = getUtcNow()
    for participant in db.Participant.select().fetch():
        if iso2utcdt(participant.whenFinish) < now:
            participant.delete()

    commit()


""" Data acess and archieve """
def getPsData(study, base_dir=base_dir): #Imp tested
    """ Updates participant info from PS """

    response = requests.get('https://dashboard-api.psychedelicsurvey.com/v2/studies/{}/participants'.format(study.psId),
     headers={
        'ClientSecret': ps_secret,
        'ClientID': ps_key,
         }
    )

    assert response.status_code==200
    study.lastPsCheck = getUtcNow().isoformat()
    return response.json()

def getSgData(study, tp=None, getAll=False): #Imp tested
    """ Download SG data save """

    if tp is None:
        assert study.type.type=='stack'
        tp = study.timepoints.select().first() # for stack stuides all tps have same Id

    if study.type.type=='indep':
        assert tp is not None

    lastSgCheck = tp.lastSgCheck
    assert isinstance(getAll, bool)
    assert isinstance(lastSgCheck, str)

    client = SurveyGizmo(api_version='v5',
                         response_type='json',
                         api_token = sg_key,
                         api_token_secret = sg_secret)

    client.config.base_url = 'https://restapi.surveygizmo.eu/'

    # Download data
    if getAll is True:
        temp = client.api.surveyresponse.resultsperpage(value=100000).list(tp.surveyId)

    if getAll is False:
        temp = client.api.surveyresponse.filter(
            field    = 'date_submitted',
            operator = '>',
            value    = lastSgCheck).resultsperpage(value=100000).list(tp.surveyId)

    sg_data = json.loads(temp)
    assert sg_data['total_pages'] in [0,1]
    assert sg_data['result_ok'] is True

    # update lastSgCheck
    utcNowStr=getUtcNow().isoformat()
    if study.type.type=='stack':
        for tp in study.timepoints:
            tp.lastSgCheck = utcNowStr

    if study.type.type=='indep':
        tp.lastSgCheck = utcNowStr

    #nudgelog.info('SG data downloaded, study:{}, tp{}:.'.format(study.name, tp.name))
    return sg_data

def getDataFilePath(study, tp=None, source=None, base_dir=base_dir): #Tested
    """ Return the intended filepath when data files are saved """

    #base_dir='/home/bazsi'
    assert source in ['sg', 'ps']

    if (source=='ps'):
        assert tp is None
        return os.path.join(base_dir, "data/{}_{}_to({}).json".format(
            study.name,
            'ps',
            getUtcNow().isoformat()[:-6]
            ))

    if (source=='sg') and (study.type.type=='stack'):
        return os.path.join(base_dir, "data/{}_{}_{}_from({})_to({}).json".format(
            study.name,
            'sg',
            'stack',
            study.timepoints.select().first().lastSgCheck[:-6],
            getUtcNow().isoformat()[:-6]
            ))

    if (source=='sg') and (study.type.type=='indep'):
        return os.path.join(base_dir, "data/{}_{}_{}_from({})_to({}).json".format(
            study.name,
            'sg',
            tp.name,
            tp.lastSgCheck[:-6],
            getUtcNow().isoformat()[:-6]
            ))

    assert False

def saveData(data, filepath): #Imp tested
    """ Saves data locally """
    with open(filepath, 'w+') as file:
        json.dump(data, file)

def getResponseSguid(response): #Tested
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


""" Cron run check """
def scheduleTester():
    nudgelog.info('Schedueler executed.')
