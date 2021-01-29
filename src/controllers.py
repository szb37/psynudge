"""
:Author: Balazs Szigeti <b.islander@protonmail.com>
:Copyright: 2021, DrugNerdsLab
:License: MIT
"""

from .tokens import ps_key, ps_secret
from .db import build_empty_db, get_db
from .core import *
from .mydt import getUtcNow
import requests
import os

src_folder = os.path.dirname(os.path.abspath(__file__))
base_dir   = os.path.abspath(os.path.join(src_folder, os.pardir))


def build_db(filepath=os.path.join(base_dir, 'psynudge_db.sqlite'), delete_past=False):

    db = build_empty_db(filepath=filepath, create_db=True, mock_db=False)
    updatePsData2Db(db, save=False, delete_past=delete_past)
    updateSgData2Db(db, save=False, getAll=True)
    return db

@db_session
def updatePsData2Db(db, save=True, delete_past=True):
    """ Downloads PS data and updates DB """

    assert isinstance(save, bool)

    for study in db.Study.select(lambda s: s.isActive is True).fetch():

        ps_data = getPsData(study)
        updateParticipant(db=db, study=study, ps_data=ps_data)

        if save:
            filepath = getDataFilePath(study, source='ps', base_dir=base_dir)
            saveData(ps_data, filepath)

        study.lastPsCheck=getUtcNow().isoformat()

        if delete_past is True:
            deletePastParticipant(db)

@db_session
def updateSgData2Db(db, save=True, getAll=False):
    """ Downloads SG data and updates DB """

    assert isinstance(save, bool)
    assert isinstance(getAll, bool)

    for study in db.Study.select(lambda s: s.isActive is True).fetch():

        if study.type.type=='stack':
            alchemy_data = getSgData(study=study, getAll=getAll)
            updateIsCompleteStack(db=db, study=study, alchemy_data=alchemy_data)

            if save:
                filepath = getDataFilePath(study=study, source='sg')
                saveData(ps_data, filepath)

        if study.type.type=='indep':
            for tp in study.timepoints:
                alchemy_data = getSgData(study=study, tp=tp, getAll=getAll)
                updateIsCompleteIndep(db=db, tp=tp, alchemy_data=alchemy_data)

                if save:
                    filepath = getDataFilePath(study=study, tp=tp, source='sg')
                    saveData(ps_data, filepath)

@db_session
def sendNudges(db, isTest=False):
    """ For all tps, collects Completion with .isNudge=True and then calls PS to send reminder email """

    nudges=[]
    for tp in db.Timepoint.select().fetch():

        if tp.study.isActive is False:
            continue

        comps    = db.Completion.select(lambda c: c.timepoint==tp).fetch()
        user_ids = [comp.participant.psId for comp in comps if comp.isNudge() is True]

        if isTest:
            nudges.append((tp.study, tp.psId, user_ids))
            continue

        ps_call = requests.post(
            'https://dashboard-api.psychedelicsurvey.com/v2/studies/{}/timepoints/{}/send'.format(
                tp.study.psId,
                tp.psId,
                ),
            json={
                "subject" : "Reminder to complete missed survey",
                "participants" : user_ids,
                },
            headers={
                'ClientSecret' : ps_secret,
                'ClientID' : ps_key,
                },
            )

        assert ps_call.response_code==200

    if isTest:
        return nudges
