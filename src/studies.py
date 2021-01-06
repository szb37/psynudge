"""
:Author: Balazs Szigeti <b.islander@protonmail.com>
:Copyright: 2020, DrugNerdsLab
:License: MIT
"""

from datetime import timedelta as td


class Study():
    """ Representation of studies """

    def __init__(self, name, type, tps=[], isActive=True):
        assert type in ['indep', 'stacked']
        assert isinstance(isActive, bool)
        assert isinstance(name, str)
        #assert (tps==[] or (isinstance(tps, list) and all([isinstance(tp, Timepoint) for tp in tps])))
        assert isinstance(tps, list) and all([isinstance(tp, Timepoint) for tp in tps])

        self.name = name
        self.type = type # Stacked type has the study in a single SG survey, indep has multiple SG surveys
        self.tps  = tps
        self.isActive = isActive

    def areTpsConsistent(self):

        if self.type=='stacked':
            if not len(set([tp.surveyId for tp in self.tps]))==1:
                print('not all surveyIds are unique')
                return False

            if not all([isinstance(tp.lastQID, int) for tp in self.tps]):
                print('not all lastQIDs are int')
                return False

            if not len(set([tp.lastQID for tp in self.tps]))==len(self.tps):
                print('not all lastQIDs are unique')
                return False

            if not len(set([tp.startPageId for tp in self.tps]))==len(self.tps):
                print('not all startPageIds are unique')
                return False

            return True

        if self.type=='indep':

            if not len(set([tp.surveyId for tp in self.tps]))==len(self.tps):
                return False

            if not all([tp.startPageId==1 for tp in self.tps]):
                return False

            return True

class Timepoint():
    """ Representation of tempoints within a study """

    def __init__(self, name, surveyId, td2start, td2end, td2nudge, remind=True, firstQID=None, lastQID=None, startPageId=1):
        assert isinstance(name, str)
        assert isinstance(surveyId, str)
        assert isinstance(td2start, td)
        assert isinstance(td2end, td)
        assert isinstance(td2nudge, td)
        assert isinstance(remind, bool)
        assert isinstance(startPageId, int)
        assert (lastQID is None) or isinstance(lastQID, int)

        self.name = name
        self.surveyId = surveyId # this can be used as timepoint Id as well
        self.td2start = td2start # td2start: datetime.deltatime from user['date'] to start of TP, i.e. user['date'] + td2start = start of TP
        self.td2end = td2end     # td2end: datetime.deltatime from start of TP to end of TP, i.e. user['date'] + td2start + td2end = end of TP
        self.td2nudge = td2nudge # td2nudge: datetime.deltatime from end of TP to the end of nudge time window
        self.remind = remind
        self.startPageId = startPageId
        self.firstQID = firstQID
        self.lastQID = lastQID


""" Define mock studies """
indep_test_study = Study(
    name='indep_test',
    type='indep',
    tps = [
        Timepoint(name='tp1', surveyId='90288073', td2start=td(days=1), td2end=td(days=1), td2nudge=td(days=1), firstQID=2, lastQID=18),
        Timepoint(name='tp2', surveyId='90289410', td2start=td(days=6), td2end=td(days=1), td2nudge=td(days=2), firstQID=7, lastQID=19),
    ]
)

stacked_test_study = Study(
    name='stacked_test',
    type='stacked',
    tps = [
        Timepoint(name='tp1', surveyId='90286853', td2start=td(days=1), td2end=td(days=1), td2nudge=td(days=1), firstQID=2, lastQID=18, startPageId=1),
        Timepoint(name='tp2', surveyId='90286853', td2start=td(days=6), td2end=td(days=1), td2nudge=td(days=2), firstQID=7, lastQID=19, startPageId=5),
    ]
)

""" Define real studies """

studies_list=[indep_test_study, stacked_test_study]

#for study in studies_list:
#    assert study.areTpsConsistent()
