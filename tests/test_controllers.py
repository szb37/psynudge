"""
:Author: Balazs Szigeti <b.islander@protonmail.com>
:Copyright: 2020, DrugNerdsLab
:License: MIT

Integration tests """

from pony.orm import db_session
from unittest import mock
import psynudge
import unittest

db = psynudge.db.build_empty_db(filepath=':memory:', create_db=True, mock_db=True) # DB wo participant, just studys and timepoints


class IntegrationTests(unittest.TestCase):

    @unittest.skip('wip')
    @db_session
    def test_build_db(self):

        db = psynudge.controllers.build_db(filepath=':memory:', delete_past=False)

        # Test updatePsData2Db jobs
        self.assertEqual(db.Study.select(lambda s: s.name=='indep_study').first().participants.select().count(), 2)
        self.assertEqual(db.Study.select(lambda s: s.name=='stack_study').first().participants.select().count(), 3)
        self.assertEqual(db.Participant.select().count(), 5)
        self.assertEqual(db.Completion.select().count(), 10)
        self.assertEqual(db.Participant.select(lambda p: p.psId=='004').first().whenStart, '2021-01-24T23:00:00+00:00')
        self.assertEqual(db.Participant.select(lambda p: p.psId=='004').first().whenFinish, '2021-02-02T23:00:00+00:00')
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

        import pdb; pdb.set_trace()