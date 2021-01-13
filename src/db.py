"""
Define sqlite DB structure which represents teh studies and surveys
:Author: Balazs Szigeti <microdose-studz.protonmail.com>
:Copyright: 2020, DrugNerdsLab
:License: MIT
"""

from pony.orm import *
import datetime
import os


src_folder = os.path.dirname(os.path.abspath(__file__))
base_dir   = os.path.abspath(os.path.join(src_folder, os.pardir))
db = Database()


class LastCheck(db.Entity):
    id = PrimaryKey(int, auto=True)
    dt = Required(datetime.datetime)


class Nudge(db.Entity):
    id = PrimaryKey(int, auto=True)
    study = Required(str)
    timepoint = Required('Timepoint')


class Study(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Optional(str)
    users = Set('Participant')
    type = Required('StudyType')
    timepoints = Set('Timepoint')
    isActive = Required(bool, default=True)

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
    study = Required(Study)
    name = Optional(str)
    completions = Set('Completion')
    nudges = Set(Nudge)
    isRemind = Required(bool, default=True)
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
    isActive = Required(bool, default=True)


class Completion(db.Entity):
    id = PrimaryKey(int, auto=True)
    participant = Required(Participant)
    timepoint = Required(Timepoint)
    isComplete = Required(bool, default=False)
    needComplete = Required(bool, default=False)


def getDb(db=db, filepath=os.path.join(base_dir, 'nudges.sqlite'), create_db=False):
    """ Returns sqlite database"""

    db.bind(provider='sqlite', filename=filepath, create_db=create_db)
    db.generate_mapping(create_tables=True)
    return db
