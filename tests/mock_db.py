"""
:Author: Balazs Szigeti <b.islander@protonmail.com>
:Copyright: 2020, DrugNerdsLab
:License: MIT
"""

from datetime import timedelta as td
from pony.orm import *
import psynudge


def getMockDb():
    db = psynudge.db.getDb(filepath=':memory:', create_db=True)

    with db_session:
        """ define study types """
        indep_type = psynudge.db.StudyType(type='indep')
        stack_type = psynudge.db.StudyType(type='stack')

        """ indep_mock_study """
        indep_mock_study = psynudge.db.Study(
            name='indep_test',
            type=indep_type,
        )
        indep_tp1 = psynudge.db.Timepoint(
            study = indep_mock_study,
            name = 'indep_tp1',
            surveyId = 90288073,
            firstQID = 2,
            lastQID = 18,
            td2start = td(days=1),
            td2end = td(days=1),
            td2nudge = td(days=1)
        )
        indep_tp2 = psynudge.db.Timepoint(
            study = indep_mock_study,
            name = 'indep_tp2',
            surveyId = 90289410,
            firstQID = 7,
            lastQID = 19,
            td2start = td(days=6),
            td2end = td(days=1),
            td2nudge = td(days=2)
        )
        indep_mock_study.timepoints = [indep_tp1, indep_tp2]

        """ stack_mock_study """
        stack_mock_study = psynudge.db.Study(
            name='stack_test',
            type='stack',
        )
        stack_tp1 = psynudge.db.Timepoint(
            study = stack_mock_study,
            name = 'stack_tp1',
            surveyId = 90286853,
            firstQID = 2,
            lastQID = 18,
            startPageId = 1,
            td2start = td(days=1),
            td2end = td(days=1),
            td2nudge =td(days=1)
        )
        stack_tp2 = psynudge.db.Timepoint(
            study = stack_mock_study,
            name = 'stack_tp2',            
            surveyId = 90286853,
            firstQID = 7,
            lastQID = 19,
            startPageId = 5,
            td2start = td(days=6),
            td2end = td(days=1),
            td2nudge = td(days=2)
        )
        stack_mock_study.timepoints = [stack_tp1, stack_tp2]

    return db

def getMockDbwParts():

    db = getMockDb()

    with db_session:
        mock_ps = [
            {"key":"test1", "email":"test1@test.net", "date":"2020-01-10T00:00:00-04:00", "id":"test1"},
            {"key":"test2", "email":"test2@test.net", "date":"2020-01-10T00:00:00-03:00", "id":"test2"},
            {"key":"test3", "email":"test3@test.net", "date":"2020-01-10T00:00:00-04:00", "id":"test3"},
            {"key":"test4", "email":"test4@test.net", "date":"2020-01-10T00:00:00-01:00", "id":"test4"},
            {"key":"test5", "email":"test5@test.net", "date":"2020-01-10T00:00:00Z"     , "id":"test5"},
            {"key":"test6", "email":"test6@test.net", "date":"2020-01-10T00:00:00+01:00", "id":"test6"},
            {"key":"test7", "email":"test7@test.net", "date":"2020-01-10T00:00:00+02:00", "id":"test7"},
            {"key":"test8", "email":"test8@test.net", "date":"2020-01-10T00:00:00+03:00", "id":"test8"},
            {"key":"test9", "email":"test9@test.net", "date":"2020-01-10T00:00:00+04:00", "id":"test9"}]

        psynudge.core.updateParticipantFromPS(
            db = db,
            ps_data = mock_ps,
            study = db.Study.select(lambda study: study.name=='indep_test').first())

    return db

#db = getMockDbwParts()
