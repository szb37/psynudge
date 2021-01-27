"""
:Author: Balazs Szigeti <b.islander@protonmail.com>
:Copyright: 2020, DrugNerdsLab
:License: MIT

python -m pytest psynudge/tests/
"""

from pony.orm import db_session
from unittest import mock
import dateutil.parser
import datetime
import psynudge
import unittest
import pytz
import json
import os

test_dir = os.path.dirname(os.path.abspath(__file__))
db = psynudge.db.build_db(filepath=':memory:', create_db=True) # DB wo participant, just studys and timepoints


class DatabaseTests(unittest.TestCase):

    @db_session
    def test_updateParticipant_fromFile(self, db=db):

        psynudge.core.updateParticipant(
            db = db,
            ps_file_path = os.path.join(test_dir, 'fixtures', 'ps_data.json'),
            study = db.Study.select(lambda study: study.name=='indep_test').first())

        self.assertEqual(db.Participant.select().count(), 10)
        self.assertEqual(db.Participant.select().count()*2, db.Completion.select().count())

        # Check that Ids are correct
        ps_ids = [part.psId for part in db.Participant.select().fetch()]
        expected_ps_ids = ['001', '002', '003', '004', '005', '006', '007', '008', '009', '010']
        for expected_ps_id in expected_ps_ids:
            self.assertTrue(expected_ps_id in ps_ids)

        #{"key":"test7", "email":"test7@test.net", "date":"2020-01-10T00:00:00+02:00", "id":"008"},
        test7p = db.Participant.select(lambda p: p.psId=='008').first()
        self.assertEqual(test7p.whenStart, '2020-01-09T22:00:00+00:00')
        self.assertEqual(test7p.whenFinish, '2020-01-18T22:00:00+00:00')

        #{"key":"test5", "email":"test5@test.net", "date":"2020-01-10T00:00:00Z"     , "id":"005"},
        test7p = db.Participant.select(lambda p: p.psId=='005').first()
        self.assertEqual(test7p.whenStart, '2020-01-10T00:00:00+00:00')
        self.assertEqual(test7p.whenFinish, '2020-01-19T00:00:00+00:00')

        #{"key":"test6", "email":"test6@test.net", "date":"2020-01-10T00:00:00+00:00", "id":"006"},
        test7p = db.Participant.select(lambda p: p.psId=='006').first()
        self.assertEqual(test7p.whenStart, '2020-01-10T00:00:00+00:00')
        self.assertEqual(test7p.whenFinish, '2020-01-19T00:00:00+00:00')

        #{"key":"test1", "email":"test1@test.net", "date":"2020-01-10T00:00:00-04:00", "id":"001"},
        test7p = db.Participant.select(lambda p: p.psId=='001').first()
        self.assertEqual(test7p.whenStart, '2020-01-10T04:00:00+00:00')
        self.assertEqual(test7p.whenFinish, '2020-01-19T04:00:00+00:00')

        db.rollback()

    @db_session
    def test_updateParticipant_fromJson(self, db=db):
        """ besides the update test, this test also contains tests for duplicate participants """

        self.assertEqual(db.Participant.select().count(), 0)

        mock_ps = [
            {"key":"test1", "email":"test1@test.net", "date":"2020-01-10T00:00:00-04:00", "id":"001"},
            {"key":"test2", "email":"test2@test.net", "date":"2020-01-10T00:00:00-03:00", "id":"002"},
            {"key":"test3", "email":"test3@test.net", "date":"2020-01-10T00:00:00-02:00", "id":"003"},
            {"key":"test4", "email":"test4@test.net", "date":"2020-01-10T00:00:00-01:00", "id":"004"},
            {"key":"test5", "email":"test5@test.net", "date":"2020-01-10T00:00:00Z"     , "id":"005"},
            {"key":"test6", "email":"test6@test.net", "date":"2020-01-10T00:00:00+00:00", "id":"006"},
            {"key":"test7", "email":"test7@test.net", "date":"2020-01-10T00:00:00+01:00", "id":"007"},
            {"key":"test8", "email":"test8@test.net", "date":"2020-01-10T00:00:00+02:00", "id":"008"},
            {"key":"test9", "email":"test9@test.net", "date":"2020-01-10T00:00:00+03:00", "id":"009"},
            {"key":"test10", "email":"test10@test.net", "date":"2020-01-10T00:00:00+04:00", "id":"010"}]

        psynudge.core.updateParticipant(
            db = db,
            ps_data = mock_ps,
            study = db.Study.select(lambda study: study.name=='indep_test').first())

        self.assertEqual(db.Participant.select().count(), 10)
        self.assertEqual(db.Participant.select().count()*2, db.Completion.select().count())

        # Check that Ids are correct
        ps_ids = [part.psId for part in db.Participant.select().fetch()]
        expected_ps_ids = ['001', '002', '003', '004', '005', '006', '007', '008', '009', '010']
        for expected_ps_id in expected_ps_ids:
            self.assertTrue(expected_ps_id in ps_ids)

        #{"key":"test7", "email":"test7@test.net", "date":"2020-01-10T00:00:00+02:00", "id":"008"},
        test7p = db.Participant.select(lambda p: p.psId=='008').first()
        self.assertEqual(test7p.whenStart, '2020-01-09T22:00:00+00:00')
        self.assertEqual(test7p.whenFinish, '2020-01-18T22:00:00+00:00')

        #{"key":"test5", "email":"test5@test.net", "date":"2020-01-10T00:00:00Z"     , "id":"005"},
        test7p = db.Participant.select(lambda p: p.psId=='005').first()
        self.assertEqual(test7p.whenStart, '2020-01-10T00:00:00+00:00')
        self.assertEqual(test7p.whenFinish, '2020-01-19T00:00:00+00:00')

        #{"key":"test6", "email":"test6@test.net", "date":"2020-01-10T00:00:00+00:00", "id":"006"},
        test7p = db.Participant.select(lambda p: p.psId=='006').first()
        self.assertEqual(test7p.whenStart, '2020-01-10T00:00:00+00:00')
        self.assertEqual(test7p.whenFinish, '2020-01-19T00:00:00+00:00')

        #{"key":"test1", "email":"test1@test.net", "date":"2020-01-10T00:00:00-04:00", "id":"001"},
        test7p = db.Participant.select(lambda p: p.psId=='001').first()
        self.assertEqual(test7p.whenStart, '2020-01-10T04:00:00+00:00')
        self.assertEqual(test7p.whenFinish, '2020-01-19T04:00:00+00:00')

        # Add duplcate participants and a legit new one
        mock_ps2 = [
            {"key":"test11", "email":"test11@test.net", "date":"2020-01-10T00:00:00-05:00", "id":"011"},
            {"key":"test1", "email":"test1@test.net", "date":"2020-01-10T00:00:00-04:00", "id":"001"},
            {"key":"test2", "email":"test2@test.net", "date":"2020-01-10T00:00:00-03:00", "id":"002"},]

        psynudge.core.updateParticipant(
            db = db,
            ps_data = mock_ps2,
            study = db.Study.select(lambda study: study.name=='indep_test').first())

        self.assertEqual(db.Participant.select().count(), 11)
        self.assertEqual(db.Participant.select().count()*2, db.Completion.select().count())

        # Check that Ids are correct
        ps_ids = [part.psId for part in db.Participant.select().fetch()]
        expected_ps_ids = ['001', '002', '003', '004', '005', '006', '007', '008', '009', '010', '011']
        for expected_ps_id in expected_ps_ids:
            self.assertTrue(expected_ps_id in ps_ids)

        #{"key":"test1", "email":"test1@test.net", "date":"2020-01-10T00:00:00-04:00", "id":"001"},
        test7p = db.Participant.select(lambda p: p.psId=='001').first()
        self.assertEqual(test7p.whenStart, '2020-01-10T04:00:00+00:00')
        self.assertEqual(test7p.whenFinish, '2020-01-19T04:00:00+00:00')

        #{"key":"test11", "email":"test11@test.net", "date":"2020-01-10T00:00:00-05:00", "id":"011"}
        test7p = db.Participant.select(lambda p: p.psId=='011').first()
        self.assertEqual(test7p.whenStart, '2020-01-10T05:00:00+00:00')
        self.assertEqual(test7p.whenFinish, '2020-01-19T05:00:00+00:00')

        db.rollback()

    @db_session
    @mock.patch('psynudge.src.core.getUtcNow')
    def test_deletePastParticipant(self, mock, db=db):

        psynudge.core.updateParticipant(
            db = db,
            ps_file_path = os.path.join(test_dir, 'fixtures', 'ps_data.json'),
            study = db.Study.select(lambda study: study.name=='indep_test').first())

        self.assertEqual(db.Participant.select().count(), 10)
        self.assertEqual(db.Completion.select().count(), db.Participant.select().count()*2)

        # Some participants are past case 1
        mock.return_value = dateutil.parser.parse("2020-01-18T22:00:02+00:00").astimezone(pytz.timezone('UTC'))
        psynudge.core.deletePastParticipant(db=db)
        self.assertEqual(db.Participant.select().count(), 7)
        self.assertEqual(db.Completion.select().count(), db.Participant.select().count()*2)

        # Some participants are past case 2
        mock.return_value = dateutil.parser.parse("2020-01-19T02:00:02+00:00").astimezone(pytz.timezone('UTC'))
        psynudge.core.deletePastParticipant(db=db)
        self.assertEqual(db.Participant.select().count(), 2)
        self.assertEqual(db.Completion.select().count(), db.Participant.select().count()*2)

        # All participants are past case
        mock.return_value = dateutil.parser.parse("2020-01-31T22:22:22+00:00").astimezone(pytz.timezone('UTC'))
        psynudge.core.deletePastParticipant(db=db)
        self.assertEqual(db.Participant.select().count(), 0)
        self.assertEqual(db.Completion.select().count(), db.Participant.select().count()*2)

        db.rollback()

    @db_session
    def test_updateIsCompleteIndep(self, db=db):

        """
        https://survey.alchemer.eu/s3/90288073/indep-tp1?sguid=001 # Did not start
        https://survey.alchemer.eu/s3/90288073/indep-tp1?sguid=002 # Done - started, not finished
        https://survey.alchemer.eu/s3/90288073/indep-tp1?sguid=003 # Done - finished

        https://survey.alchemer.eu/s3/90289410/indep-tp2-copy?sguid=001 # Did not start
        https://survey.alchemer.eu/s3/90289410/indep-tp2-copy?sguid=002 # Done - started, not finished
        https://survey.alchemer.eu/s3/90289410/indep-tp2-copy?sguid=003 # Done, finished
        """

        psynudge.core.updateParticipant(
            db = db,
            ps_file_path = os.path.join(test_dir, 'fixtures', 'ps_data.json'),
            study = db.Study.select(lambda study: study.name=='indep_test').first())

        self.assertEqual(db.Completion.select().count(), 20)
        self.assertEqual(db.Completion.select(lambda c: c.isComplete is True).count(), 0)

        # Add completions for tp1
        tp1 = db.Timepoint.select(lambda tp: tp.name=='indep_tp1').first()
        fp = os.path.join(test_dir, 'fixtures', 'indep_tp1.json')
        psynudge.core.updateIsCompleteIndep(db=db, tp=tp1, alchemy_file_path=fp)

        self.assertEqual(db.Completion.select().count(), 20)
        self.assertEqual(db.Completion.select(lambda c: c.isComplete is True).count(), 1)

        self.assertFalse(
            db.Completion.select(lambda c: c.participant.psId=='001' and c.timepoint==tp1).first().isComplete)
        self.assertFalse(
            db.Completion.select(lambda c: c.participant.psId=='002' and c.timepoint==tp1).first().isComplete)
        self.assertTrue(
            db.Completion.select(lambda c: c.participant.psId=='003' and c.timepoint==tp1).first().isComplete)

        # Add completions for tp2
        tp2 = db.Timepoint.select(lambda tp: tp.name=='indep_tp2').first()
        fp = os.path.join(test_dir, 'fixtures', 'indep_tp2.json')
        psynudge.core.updateIsCompleteIndep(db=db, tp=tp2, alchemy_file_path=fp)

        self.assertEqual(db.Completion.select().count(), 20)
        self.assertEqual(db.Completion.select(lambda c: c.isComplete is True).count(), 2)

        self.assertFalse(
            db.Completion.select(lambda c: c.participant.psId=='001' and c.timepoint==tp2).first().isComplete)
        self.assertFalse(
            db.Completion.select(lambda c: c.participant.psId=='002' and c.timepoint==tp2).first().isComplete)
        self.assertTrue(
            db.Completion.select(lambda c: c.participant.psId=='003' and c.timepoint==tp2).first().isComplete)

        db.rollback()

    @db_session
    def test_updateIsCompleteStack(self, db=db):

        """
        https://survey.alchemer.eu/s3/90286853/stack?sguid=001                # Did not do
        https://survey.alchemer.eu/s3/90286853/stack?sguid=002                # Done - started, not finished
        https://survey.alchemer.eu/s3/90286853/stack?sguid=002&__sgtarget=5   # Done - started, not finished
        https://survey.alchemer.eu/s3/90286853/stack?sguid=003                # Done - finished both
        https://survey.alchemer.eu/s3/90286853/stack?sguid=003&__sgtarget=5   # Done - finished both
        https://survey.alchemer.eu/s3/90286853/stack?sguid=004                # Done - started TP1, finished TP2
        https://survey.alchemer.eu/s3/90286853/stack?sguid=004&__sgtarget=5   # Done - started TP1, finished TP2
        https://survey.alchemer.eu/s3/90286853/stack?sguid=005                # Done - finished TP1, started TP2
        https://survey.alchemer.eu/s3/90286853/stack?sguid=005&__sgtarget=5   # Done - finished TP1, started TP2
        """

        # Update DB with test participants and sanity checks
        psynudge.core.updateParticipant(
            db = db,
            ps_file_path = os.path.join(test_dir, 'fixtures', 'ps_data.json'),
            study = db.Study.select(lambda study: study.name=='stack_test').first())

        self.assertEqual(db.Completion.select().count(), 20)
        self.assertEqual(db.Completion.select(lambda c: c.isComplete is True).count(), 0)

        # Add completions from stacked study JSON
        fp = os.path.join(test_dir, 'fixtures', 'stack.json')
        study = db.Study.select(lambda s: s.name=='stack_test').first()
        stack_tp1 = db.Timepoint.select(lambda tp: tp.name=='stack_tp1').first()
        stack_tp2 = db.Timepoint.select(lambda tp: tp.name=='stack_tp2').first()
        psynudge.core.updateIsCompleteStack(db=db, study=study, alchemy_file_path=fp)

        # Check if completions are correct
        self.assertFalse(
            db.Completion.select(lambda c: c.participant.psId=='001' and c.timepoint==stack_tp1).first().isComplete)
        self.assertFalse(
            db.Completion.select(lambda c: c.participant.psId=='002' and c.timepoint==stack_tp1).first().isComplete)
        self.assertTrue(
            db.Completion.select(lambda c: c.participant.psId=='003' and c.timepoint==stack_tp1).first().isComplete)
        self.assertFalse(
            db.Completion.select(lambda c: c.participant.psId=='004' and c.timepoint==stack_tp1).first().isComplete)
        self.assertTrue(
            db.Completion.select(lambda c: c.participant.psId=='005' and c.timepoint==stack_tp1).first().isComplete)

        self.assertFalse(
            db.Completion.select(lambda c: c.participant.psId=='001' and c.timepoint==stack_tp2).first().isComplete)
        self.assertFalse(
            db.Completion.select(lambda c: c.participant.psId=='002' and c.timepoint==stack_tp2).first().isComplete)
        self.assertTrue(
            db.Completion.select(lambda c: c.participant.psId=='003' and c.timepoint==stack_tp2).first().isComplete)
        self.assertTrue(
            db.Completion.select(lambda c: c.participant.psId=='004' and c.timepoint==stack_tp2).first().isComplete)
        self.assertFalse(
            db.Completion.select(lambda c: c.participant.psId=='005' and c.timepoint==stack_tp2).first().isComplete)

        db.rollback()

    @db_session
    @mock.patch.object(psynudge.src.db.Completion, 'isNudgeTimely')
    @mock.patch.object(psynudge.src.db.Completion, 'isBeforeNudgeEnd')
    def test_IsNudge(self, mockisNudgeTimely, mockisBeforeNudgeEnd):

        psynudge.core.updateParticipant(
            db = db,
            ps_file_path = os.path.join(test_dir, 'fixtures', 'ps_data.json'),
            study = db.Study.select(lambda study: study.name=='indep_test').first())
        completion = db.Completion.select().first()

        mockisNudgeTimely.return_value = False
        completion.isComplete=False
        mockisBeforeNudgeEnd.return_value = False
        self.assertFalse(completion.isNudge())

        mockisNudgeTimely.return_value = False
        completion.isComplete=True
        mockisBeforeNudgeEnd.return_value = False
        self.assertFalse(completion.isNudge())

        mockisNudgeTimely.return_value = False
        completion.isComplete=False
        mockisBeforeNudgeEnd.return_value = True
        self.assertFalse(completion.isNudge())

        mockisNudgeTimely.return_value = False
        completion.isComplete=True
        mockisBeforeNudgeEnd.return_value = True
        self.assertFalse(completion.isNudge())

        mockisNudgeTimely.return_value = True
        completion.isComplete=False
        mockisBeforeNudgeEnd.return_value = False
        self.assertFalse(completion.isNudge())

        mockisNudgeTimely.return_value = True
        completion.isComplete=True
        mockisBeforeNudgeEnd.return_value = False
        self.assertFalse(completion.isNudge())

        mockisNudgeTimely.return_value = True
        completion.isComplete=False
        mockisBeforeNudgeEnd.return_value = True
        self.assertTrue(completion.isNudge())

        mockisNudgeTimely.return_value = True
        completion.isComplete=True
        mockisBeforeNudgeEnd.return_value = True
        self.assertFalse(completion.isNudge())

        db.rollback()

    @db_session
    @mock.patch('psynudge.src.db.getUtcNow')
    def test_isAfterCompletion(self, mock):

        # Start and finish of each completion
        #    ('2020-01-10T20:00:00', '2020-01-11T20:00:00')
        #    ('2020-01-10T21:00:00', '2020-01-11T21:00:00')
        #    ('2020-01-10T22:00:00', '2020-01-11T22:00:00')
        #    ('2020-01-10T23:00:00', '2020-01-11T23:00:00')
        #    ('2020-01-11T00:00:00', '2020-01-12T00:00:00')
        #    ('2020-01-11T00:00:00', '2020-01-12T00:00:00')
        #    ('2020-01-11T01:00:00', '2020-01-12T01:00:00')
        #    ('2020-01-11T02:00:00', '2020-01-12T02:00:00')
        #    ('2020-01-11T03:00:00', '2020-01-12T03:00:00')
        #    ('2020-01-11T04:00:00', '2020-01-12T04:00:00')

        #    ('2020-01-15T20:00:00', '2020-01-16T20:00:00')
        #    ('2020-01-15T21:00:00', '2020-01-16T21:00:00')
        #    ('2020-01-15T22:00:00', '2020-01-16T22:00:00')
        #    ('2020-01-15T23:00:00', '2020-01-16T23:00:00')
        #    ('2020-01-16T00:00:00', '2020-01-17T00:00:00')
        #    ('2020-01-16T00:00:00', '2020-01-17T00:00:00')
        #    ('2020-01-16T01:00:00', '2020-01-17T01:00:00')
        #    ('2020-01-16T02:00:00', '2020-01-17T02:00:00')
        #    ('2020-01-16T03:00:00', '2020-01-17T03:00:00')
        #    ('2020-01-16T04:00:00', '2020-01-17T04:00:00')

        psynudge.core.updateParticipant(
            db = db,
            ps_file_path = os.path.join(test_dir, 'fixtures', 'ps_data.json'),
            study = db.Study.select(lambda study: study.name=='indep_test').first())

        self.assertEqual(db.Completion.select().count(), 20)

        mock.return_value = dateutil.parser.parse("2020-01-10T19:59:59Z").astimezone(pytz.timezone('UTC'))
        self.assertEqual(sum([c.isAfterCompletion() for c in db.Completion.select().fetch()]), 0)

        mock.return_value = dateutil.parser.parse("2020-01-11T20:00:01Z").astimezone(pytz.timezone('UTC'))
        self.assertEqual(sum([c.isAfterCompletion() for c in db.Completion.select().fetch()]), 1)

        mock.return_value = dateutil.parser.parse("2020-01-11T23:00:01Z").astimezone(pytz.timezone('UTC'))
        self.assertEqual(sum([c.isAfterCompletion() for c in db.Completion.select().fetch()]), 4)

        mock.return_value = dateutil.parser.parse("2020-01-12T01:00:01Z").astimezone(pytz.timezone('UTC'))
        self.assertEqual(sum([c.isAfterCompletion() for c in db.Completion.select().fetch()]), 7)

        mock.return_value = dateutil.parser.parse("2020-01-17T03:00:01Z").astimezone(pytz.timezone('UTC'))
        self.assertEqual(sum([c.isAfterCompletion() for c in db.Completion.select().fetch()]), 19)

        mock.return_value = dateutil.parser.parse("2020-01-17T05:00:01Z").astimezone(pytz.timezone('UTC'))
        self.assertEqual(sum([c.isAfterCompletion() for c in db.Completion.select().fetch()]), 20)

        db.rollback()

    @db_session
    @mock.patch('psynudge.src.db.getUtcNow')
    def test_isNudgeTimely(self, mock):

        psynudge.core.updateParticipant(
            db = db,
            ps_file_path = os.path.join(test_dir, 'fixtures', 'ps_data.json'),
            study = db.Study.select(lambda study: study.name=='indep_test').first())
        completion = db.Completion.select().first()

        mock.return_value = dateutil.parser.parse("2020-01-10T12:00:00Z").astimezone(pytz.timezone('UTC'))
        completion.lastNudgeSend = "2020-01-10T00:00:01Z"
        self.assertFalse(completion.isNudgeTimely())

        mock.return_value = dateutil.parser.parse("2020-01-10T23:38:00Z").astimezone(pytz.timezone('UTC'))
        completion.lastNudgeSend = "2020-01-10T00:00:01Z"
        self.assertFalse(completion.isNudgeTimely())

        mock.return_value = dateutil.parser.parse("2020-01-10T23:39:00Z").astimezone(pytz.timezone('UTC'))
        completion.lastNudgeSend = "2020-01-10T00:00:01Z"
        self.assertTrue(completion.isNudgeTimely())

        mock.return_value = dateutil.parser.parse("2020-01-11T03:39:00Z").astimezone(pytz.timezone('UTC'))
        completion.lastNudgeSend = "2020-01-10T00:00:01Z"
        self.assertTrue(completion.isNudgeTimely())

        db.rollback()
