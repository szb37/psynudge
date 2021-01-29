"""
:Author: Balazs Szigeti <b.islander@protonmail.com>
:Copyright: 2020, DrugNerdsLab
:License: MIT

Integration tests """

from pony.orm import db_session
from unittest import mock
import psynudge
import unittest


db = psynudge.controllers.build_database(filepath=':memory:', delete_past=False)

class IntegrationTests(unittest.TestCase):

    @db_session
    def test_build_database(self, db=db):

        # Test updatePsData2Db jobs
        self.assertEqual(db.Study.select(lambda s: s.name=='indep_study').first().participants.select().count(), 2)
        self.assertEqual(db.Study.select(lambda s: s.name=='stack_study').first().participants.select().count(), 3)
        self.assertEqual(db.Participant.select().count(), 5)
        self.assertEqual(db.Completion.select().count(), 10)
        self.assertEqual(db.Participant.select(lambda p: p.id=='004').first().whenStart, '2021-01-24T23:00:00+00:00')
        self.assertEqual(db.Participant.select(lambda p: p.id=='004').first().whenFinish, '2021-02-02T23:00:00+00:00')
        self.assertFalse(db.Study.select(lambda s: s.name=='indep_study').first().lastPsCheck == '2020-01-01T00:00:00+00:00')
        self.assertFalse(db.Study.select(lambda s: s.name=='stack_study').first().lastPsCheck == '2020-01-01T00:00:00+00:00')

        # Test updateSgData2Db jobs
        # 002 is in indep study and completed tp2
        # 003 is in indep study and completed tp1
        # 004 is in stack study and completed tp2
        # 005 is in stack study and completed tp1

        indep_tp1 = db.Timepoint.select(lambda tp: tp.name=='indep_tp1').first()
        indep_tp2 = db.Timepoint.select(lambda tp: tp.name=='indep_tp2').first()
        stack_tp1 = db.Timepoint.select(lambda tp: tp.name=='stack_tp1').first()
        stack_tp2 = db.Timepoint.select(lambda tp: tp.name=='stack_tp2').first()

        self.assertEqual(db.Completion.select(lambda c: c.isComplete is True).count(), 4)
        self.assertEqual(db.Completion.select(lambda c: c.isComplete is True and c.timepoint==indep_tp1).count(), 1)
        self.assertEqual(db.Completion.select(lambda c: c.isComplete is True and c.timepoint==indep_tp2).count(), 1)
        self.assertEqual(db.Completion.select(lambda c: c.isComplete is True and c.timepoint==stack_tp1).count(), 1)
        self.assertEqual(db.Completion.select(lambda c: c.isComplete is True and c.timepoint==stack_tp2).count(), 1)

    @db_session
    @mock.patch.object(db.Completion, 'isNudge')
    def test_sendNudges(self, mock, db=db):

        db.Study.select(lambda s: s.name=='indep_study').first().delete()
        stack_study = db.Study.select(lambda s: s.name=='stack_study').first()

        mock.return_value = False
        nudge_ids = psynudge.controllers.sendNudges(db=db, isTest=True)
        self.assertEqual([(stack_study, 1, []) , (stack_study, 6, [])], nudge_ids)

        mock.return_value = True
        nudge_ids = psynudge.controllers.sendNudges(db=db, isTest=True)
        self.assertEqual([(stack_study, 1, ['004', '005', 'bLZBHf69wmDVSbXh']) , (stack_study, 6, ['004', '005', 'bLZBHf69wmDVSbXh'])], nudge_ids)
