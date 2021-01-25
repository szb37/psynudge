"""
:Author: Balazs Szigeti <b.islander@protonmail.com>
:Copyright: 2021, DrugNerdsLab
:License: MIT
"""

from .tokens import ps_key, ps_secret
from .db import get_db, build_db
from .core import *
import requests


def updatePsData2Db(db, save=True):
    """ Downloads PS data and updates DB """

    assert isinstance(save, bool)

    for study in db.Study.select(lambda s: s.isActive is True).fetch():

        ps_data = getPsData(study)
        updateParticipant(db=db, study=study, ps_data=ps_data)
        if save:
            filepath = getDataFilePath(study, source='ps', base_dir=base_dir)
            saveData(ps_data, filepath)

        #with db_session:
        #    study.lastPsCheck=getUtcNow().isoformat()

    deletePastParticipant(db)

def updateSgData2Db(db, save=True, forceNew=False):
    """ Downloads SG data and updates DB """

    assert isinstance(save, bool)
    assert isinstance(forceNew, bool)

    for study in db.Study.select(lambda s: s.isActive is True).fetch():

        if study.type=='stack':
            alchemy_data = getSgData(study=study, forceNew=forceNew)
            updateStackStudyIsComplete(db=db, study=study, alchemy_data=alchemy_data)

            for tp in study.timepoints:
                tp.lastSgCheck = getUtcNow().isoformat()

            if save:
                filepath = getDataFilePath(study=study, source='ps')
                saveData(ps_data, filepath)

        if study.type=='indep':
            for tp in study.timepoints:
                alchemy_data = getSgData(study=study, tp=tp, forceNew=forceNew)
                updateIndepStudyIsComplete(db=db, study=study, timepoint=tp, alchemy_data=alchemy_data)
                tp.lastSgCheck = getUtcNow().isoformat()

                if save:
                    filepath = getDataFilePath(study=study, tp=tp, source='sg')
                    saveData(ps_data, filepath)

    updateCompletionIsNeeded(db=db)
    updateCompletionIsNudge(db=db)

def sendNudges(db):
    """ Checks the status of """

    for tp in db.Timepoint.select().fetch():

        if tp.study.isActive is False:
            continue

        nudge_ids = [nudgeCompletion.participant.psId for nudgeCompletion in db.Completion.select(lambda c: c.timepoint==tp and c.isNudge is True).fetch()]

        #/v2/studies/**study_id**/timepoints/**timepoint_id**/send
        response = requests.post('https://dashboard-api.psychedelicsurvey.com/v2/studies/{}/timepoints/{}/send'.format(
            tp.study.id,
            tp.psId),
        headers={
            'ClientSecret': ps_secret,
            'ClientID': ps_key,},)

        #{
        #    "subject":"test",
        #    "participants": [
        #        "8nOqZpfooGbbhxqJ"
        #    ],
