"""
:Author: Balazs Szigeti <b.islander@protonmail.com>
:Copyright: 2020, DrugNerdsLab
:License: MIT
"""

from datetime import timedelta as td


class Study():

    def __init__(self, name, type, tps=[], isActive=True):
        assert type in ['indep', 'stacked']
        assert isinstance(isActive, bool)
        assert isinstance(name, str)
        assert (tps==[] or (isinstance(tps, list) and all([isinstance(tp, Timepoint) for tp in tps])))

        self.name = name
        self.type = type # Stacked type has the study in a single SG survey, indep has multiple SG surveys
        self.tps  = tps
        self.isActive = isActive

    def areTpsConsistent(self):

        if self.type=='stacked':
            if not len(set([tp.surveyId for tp in self.tps]))==1:
                print('not all surveyIds are unique')
                return False

            if not all([isinstance(tp.end_qid, int) for tp in self.tps]):
                print('not all end_qids are int')
                return False

            if not len(set([tp.end_qid for tp in self.tps]))==len(self.tps):
                print('not all end_qids are unique')
                return False

            if not len(set([tp.start_page for tp in self.tps]))==len(self.tps):
                print('not all start_pages are unique')
                return False

            return True

        if self.type=='indep':

            if not len(set([tp.surveyId for tp in self.tps]))==len(self.tps):
                return False

            if not all([tp.start_page==1 for tp in self.tps]):
                return False

            return True

class Timepoint():

    def __init__(self, name, surveyId, td2tp, td2nudge, remind=True, end_qid=None, start_page=1):
        assert isinstance(name, str)
        assert isinstance(surveyId, str)
        assert isinstance(td2tp, td)
        assert isinstance(td2nudge, td)
        assert isinstance(remind, bool)
        assert isinstance(start_page, int)
        assert (end_qid is None) or isinstance(end_qid, int)

        self.name = name
        self.surveyId = surveyId
        self.td2tp = td2tp       # td2tp: the datetime.deltatime from start (as entered to PS) to the end of tp, i.e. start + td2tp = end of TP
        self.td2nudge = td2nudge # td2nudge: the datetime.deltatime from start (as entered to PS) to the end of the nudge period, i.e. start + td2tp = end of TP
        self.remind = remind
        self.start_page = start_page
        self.end_qid = end_qid

indep_test_study = Study(
    name='indep_test',
    type='indep',
    tps = [
        Timepoint(name='tp1', surveyId='90288073', td2tp=td(days=0), td2nudge=td(days=1)),
        Timepoint(name='tp2', surveyId='90288074', td2tp=td(days=7), td2nudge=td(days=2)),
    ]
)

stacked_test_study = Study(
    name='stacked_test',
    type='stacked',
    tps = [
        Timepoint(name='tp1', surveyId='90286853', td2tp=td(days=0), td2nudge=td(days=1), end_qid=2, start_page=1),
        Timepoint(name='tp2', surveyId='90286853', td2tp=td(days=7), td2nudge=td(days=2), end_qid=5, start_page=5),
    ]
)

studies_list=[indep_test_study, stacked_test_study]
