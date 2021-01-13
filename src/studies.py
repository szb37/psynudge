"""
:Author: Balazs Szigeti <b.islander@protonmail.com>
:Copyright: 2020, DrugNerdsLab
:License: MIT
"""

from datetime import timedelta as td
from .db import Study, StudyType, Timepoint




""" Define mock studies """
indep_test_study = Study(
    name='indep_test',
    type='indep',
    tps = [
        Timepoint(name='tp1', surveyId='90288073', td2start=td(days=1), td2end=td(days=1), td2nudge=td(days=1), firstQID=2, lastQID=18),
        Timepoint(name='tp2', surveyId='90289410', td2start=td(days=6), td2end=td(days=1), td2nudge=td(days=2), firstQID=7, lastQID=19),
    ]
)

stack_test_study = Study(
    name='stack_test',
    type='stack',
    tps = [
        Timepoint(name='tp1', surveyId='90286853', td2start=td(days=1), td2end=td(days=1), td2nudge=td(days=1), firstQID=2, lastQID=18, startPageId=1),
        Timepoint(name='tp2', surveyId='90286853', td2start=td(days=6), td2end=td(days=1), td2nudge=td(days=2), firstQID=7, lastQID=19, startPageId=5),
    ]
)

""" Define real studies """
