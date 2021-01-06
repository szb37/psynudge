"""
Define sqlite DB structure which represents survezs
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

class Nudge(db.Entity):
    userId   = Required(str)
    studyId  = Required(str)
    surveyId = Required(str) # same as timepoint id
    #expires  = Optional(datetime.datetime)
    isSent   = Required(bool, default=False)

def getDb(db=db, filepath=os.path.join(base_dir, 'nudges.sqlite'), create_db=False):
    """ Returns sqlite database"""

    db.bind(provider='sqlite', filename=filepath, create_db=create_db)
    db.generate_mapping(create_tables=True)
    return db
