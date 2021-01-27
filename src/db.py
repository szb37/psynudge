"""
Define sqlite DB structure which represents teh studies and surveys
:Author: Balazs Szigeti <microdose-studz.protonmail.com>
:Copyright: 2020, DrugNerdsLab
:License: MIT
"""

from pony.orm import *
from .mydt import *
import datetime
import os

src_folder = os.path.dirname(os.path.abspath(__file__))
base_dir   = os.path.abspath(os.path.join(src_folder, os.pardir))

db = Database()


class Study(db.Entity):
    id = PrimaryKey(int, auto=True)
    psId = Optional(str)
    name = Optional(str)
    participants = Set('Participant')
    type = Required('StudyType')
    timepoints = Set('Timepoint')
    lastPsCheck = Required(str, default='2020-01-01T00:00:00+00:00') # in UTC
    isActive    = Required(bool, default=True)

    def areTpsConsistent(self):

        if self.type=='stack':
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

    def getFurthestTp(self):
        """ Returns timepoint with largest timedelta from start """

        furthestTp = self.timepoints.select().first()
        furthestTpTd = furthestTp.td2start + furthestTp.td2end + furthestTp.td2nudge

        for tp in self.timepoints:
            Td = tp.td2start + tp.td2end + tp.td2nudge

            if Td > furthestTpTd:
                furthestTp = tp
                furthestTpTd = tp.td2start + tp.td2end + tp.td2nudge

        return furthestTp

    def getFurthestTd(self):
        """ Returns largest timedelta from start """
        tp = self.getFurthestTp()
        return tp.td2start + tp.td2end + tp.td2nudge


class StudyType(db.Entity):
    type = PrimaryKey(str)
    studys = Set(Study)


class Timepoint(db.Entity):
    id = PrimaryKey(int, auto=True)
    psId = Optional(int)
    name = Optional(str)
    study = Required(Study)
    completions = Set('Completion')
    lastSgCheck = Required(str, default='2020-01-01T00:00:00+00:00') # in UTC
    surveyId = Required(int)
    startPageId = Optional(int)
    firstQID = Optional(int)
    lastQID = Optional(int)
    td2start = Required(datetime.timedelta)  #from user['date'] to start of TP: user['date'] + td2start = start of TP
    td2end = Required(datetime.timedelta)    #from start of TP to end of TP: user['date'] + td2start + td2end = end of TP
    td2nudge = Required(datetime.timedelta)  #from end of TP to the end of nudge window: user['date'] + td2start + td2end + td2nudge = end of nudge window


class Participant(db.Entity):
    id = PrimaryKey(int, auto=True)
    psId = Required(str)
    study = Required(Study)
    completions = Set('Completion')
    whenStart = Optional(str) # in UTC
    whenFinish = Optional(str) # in UTC


class Completion(db.Entity):
    id = PrimaryKey(int, auto=True)
    participant = Required(Participant)
    timepoint = Required(Timepoint)
    isComplete = Required(bool, default=False) # is the timepoint completed
    lastNudgeSend = Optional(str, default='2020-01-01T00:00:00+00:00') # in UTC
    #isNudge = Required(bool, default=False)
    #isAfterCompletion = Required(bool, default=False) # should the timpoint be completed already
    #isNudgeTimely = Required(bool, default=False) # did at least 23h past since last nudge

    def isAfterCompletion(self): # Tested
        """ Returns True if completion is expected, False if before / after time completion window """

        now = getUtcNow()
        expStartDtUtc = iso2utcdt(self.participant.whenStart) # start of the experiment
        startDtUtc = expStartDtUtc + self.timepoint.td2start  # start of the timepoint
        finishDtUtc = startDtUtc + self.timepoint.td2end      # end of the tmepoint

        if finishDtUtc <= now:
            return True

        return False

    def isBeforeNudgeEnd(self): #Imp tested
        """ Checks if now is within nudge time window of user and tp """

        tp = self.timepoint
        dtStartUTC = iso2utcdt(self.participant.whenStart)

        start = dtStartUTC + (tp.td2start + tp.td2end)
        end   = dtStartUTC + (tp.td2start + tp.td2end + tp.td2nudge)

        return isWithinTimeWindow(start, end)

    def isNudgeTimely(self): #Tested
        """ Returns True if last nudge was sent > 23:50h ago, False otherwise """

        dtNow = getUtcNow()
        dtlastNudgeSend = iso2utcdt(self.lastNudgeSend)
        assert dtNow > dtlastNudgeSend

        if (dtNow - dtlastNudgeSend) > datetime.timedelta(days=0.985): # 0.985 instead of 1 for error tolerance ~23:38
            return True

        return False

    def isNudge(self): #Tested
        """ Returns True if
            -(tp is witin nudge time window) and
            -(tp has not been completed yet) and
            -(last nudge was sent more then 24h ago),

            False otherwise
        """

        # Check if completed already
        if self.isComplete is True:
            return False

        # Check if we are within nudge time window
        if self.isBeforeNudgeEnd() is False:
            return False

        # Check if last nudge was sent within 23.5 hours
        if self.isNudgeTimely() is False:
            return False

        return True


def get_db(db=db, filepath=os.path.join(base_dir, 'psynudge_db.sqlite'), create_db=False):
    """ Returns existing sqlite database"""

    db.bind(provider='sqlite', filename=filepath, create_db=create_db)
    db.generate_mapping(create_tables=True)
    return db

def build_empty_db(db=db, filepath=os.path.join(base_dir, 'psynudge_db.sqlite'), create_db=True, mock_db=False):
    """ Deletes old database (if exists) and returns newly built sqlite database"""

    if db.provider is not None:
        return db

    if os.path.isfile(filepath):
        os.remove(filepath)

    db = get_db(filepath=filepath, create_db=create_db)

    """ Define database entries for mock studies """
    with db_session:

        """ define study types """
        indep_type = StudyType(type='indep')
        stack_type = StudyType(type='stack')

        """ indep_mock_study """
        indep_mock_study = Study(
            psId='38130fdb-5c9e-11eb-ac63-0a280c4496dd',
            name='indep_study',
            type=indep_type,
        )
        indep_tp1 = Timepoint(
            study = indep_mock_study,
            psId=1,
            name = 'indep_tp1',
            surveyId = 90288073,
            firstQID = 2,
            lastQID = 18,
            td2start = datetime.timedelta(days=1),
            td2end = datetime.timedelta(days=1),
            td2nudge = datetime.timedelta(days=1)
        )
        indep_tp2 = Timepoint(
            study = indep_mock_study,
            psId=6,
            name = 'indep_tp2',
            surveyId = 90289410,
            firstQID = 7,
            lastQID = 19,
            td2start = datetime.timedelta(days=6),
            td2end = datetime.timedelta(days=1),
            td2nudge = datetime.timedelta(days=2)
        )
        indep_mock_study.timepoints = [indep_tp1, indep_tp2]

        """ stack_mock_study """
        stack_mock_study = Study(
            psId='3f4241b2-5cbb-11eb-ac63-0a280c4496dd',
            name='stack_study',
            type='stack',
        )
        stack_tp1 = Timepoint(
            study = stack_mock_study,
            name = 'stack_tp1',
            psId=1,
            surveyId = 90286853,
            firstQID = 2,
            lastQID = 18,
            startPageId = 1,
            td2start = datetime.timedelta(days=1),
            td2end = datetime.timedelta(days=1),
            td2nudge =datetime.timedelta(days=1)
        )
        stack_tp2 = Timepoint(
            study = stack_mock_study,
            name = 'stack_tp2',
            surveyId = 90286853,
            psId=6,
            firstQID = 7,
            lastQID = 19,
            startPageId = 5,
            td2start = datetime.timedelta(days=6),
            td2end = datetime.timedelta(days=1),
            td2nudge = datetime.timedelta(days=2)
        )
        stack_mock_study.timepoints = [stack_tp1, stack_tp2]

    if mock_db is True:
        return db

    """ Define database entries for active studies """
    with db_session:
        pass

    return db
