"""
:Author: Balazs Szigeti <b.islander@protonmail.com>
:Copyright: 2020, DrugNerdsLab
:License: MIT

python -m pytest psynudge/tests/
"""


from unittest import mock
from pony.orm import db_session
import dateutil.parser
import datetime
import psynudge
import mock_db
import unittest
import pytz
import json
import os

test_dir = os.path.dirname(os.path.abspath(__file__))

#    tp = db.Timepoint(
#        name='test',
#        surveyId='000',
#        td2start=datetime.timedelta(days=6),
#        td2end=datetime.timedelta(days=1),
#        td2nudge=datetime.timedelta(days=1),)

class DatetimeTests(unittest.TestCase):
    """ Tests for datetime manipulations """

    dtStartUTC = dateutil.parser.parse("2020-01-10T00:00:00Z").astimezone(pytz.timezone('UTC'))

    def test_iso2utcdt(self):

        dt_utc = psynudge.core.iso2utcdt('2020-01-10T00:00:00Z')
        self.assertEqual(dt_utc, dateutil.parser.parse('2020-01-10T00:00:00Z').astimezone(pytz.timezone('UTC')))

        dt_utc = psynudge.core.iso2utcdt('2020-01-10T00:00:00+00:00')
        self.assertEqual(dt_utc, dateutil.parser.parse('2020-01-10T00:00:00Z').astimezone(pytz.timezone('UTC')))

        dt_utc = psynudge.core.iso2utcdt('2020-01-10T00:00:00+02:00')
        self.assertEqual(dt_utc, dateutil.parser.parse('2020-01-10T00:00:00+02:00').astimezone(pytz.timezone('UTC')))

        dt_utc = psynudge.core.iso2utcdt('2020-01-10T00:00:00-03:00')
        self.assertEqual(dt_utc, dateutil.parser.parse('2020-01-10T00:00:00-03:00').astimezone(pytz.timezone('UTC')))


    def test_iso2dt(self):

        dt_loc = psynudge.core.iso2dt('2020-01-10T00:00:00Z')
        self.assertEqual(dt_loc, dateutil.parser.parse('2020-01-10T00:00:00Z').astimezone(pytz.timezone('UTC')))

        dt_loc = psynudge.core.iso2dt('2020-01-10T00:00:00+00:00')
        self.assertEqual(dt_loc, dateutil.parser.parse('2020-01-10T00:00:00Z').astimezone(pytz.timezone('UTC')))

        dt_loc = psynudge.core.iso2dt('2020-01-10T00:00:00+02:00')
        dt_utc = psynudge.core.iso2utcdt('2020-01-10T00:00:00+02:00')
        self.assertEqual(dt_loc.astimezone(pytz.timezone('UTC')), dt_utc)
        self.assertEqual(dt_loc.astimezone(pytz.timezone('UTC')), dateutil.parser.parse('2020-01-10T00:00:00+02:00').astimezone(pytz.timezone('UTC')))

        dt_loc = psynudge.core.iso2dt('2020-01-10T00:00:00-03:00')
        dt_utc = psynudge.core.iso2utcdt('2020-01-10T00:00:00-03:00')
        self.assertEqual(dt_loc.astimezone(pytz.timezone('UTC')), dt_utc)
        self.assertEqual(dt_loc.astimezone(pytz.timezone('UTC')), dateutil.parser.parse('2020-01-10T00:00:00-03:00').astimezone(pytz.timezone('UTC')))

    @mock.patch('psynudge.src.core.getUtcNow')
    def test_isWithinWindow(self, mock):

        mock.return_value = dateutil.parser.parse("2020-01-10T00:00:00Z").astimezone(pytz.timezone('UTC'))
        start = dateutil.parser.parse("2020-01-09T00:00:00Z").astimezone(pytz.timezone('UTC'))
        end =   dateutil.parser.parse("2020-01-11T00:00:00Z").astimezone(pytz.timezone('UTC'))
        self.assertTrue(psynudge.core.isWithinWindow(start, end))

        mock.return_value = dateutil.parser.parse("2020-01-08T00:00:00Z").astimezone(pytz.timezone('UTC'))
        start = dateutil.parser.parse("2020-01-09T00:00:00Z").astimezone(pytz.timezone('UTC'))
        end =   dateutil.parser.parse("2020-01-11T00:00:00Z").astimezone(pytz.timezone('UTC'))
        self.assertFalse(psynudge.core.isWithinWindow(start, end))

        # Cases when time zone is non UTC
        mock.return_value = dateutil.parser.parse("2020-01-10T04:00:01Z").astimezone(pytz.timezone('UTC'))
        start = dateutil.parser.parse("2020-01-10T00:00:00-04:00").astimezone(pytz.timezone('UTC'))
        end =   dateutil.parser.parse("2020-01-11T00:00:00-04:00").astimezone(pytz.timezone('UTC'))
        self.assertTrue(psynudge.core.isWithinWindow(start, end))

        mock.return_value = dateutil.parser.parse("2020-01-10T03:59:59Z").astimezone(pytz.timezone('UTC'))
        start = dateutil.parser.parse("2020-01-10T00:00:00-04:00").astimezone(pytz.timezone('UTC'))
        end =   dateutil.parser.parse("2020-01-11T00:00:00-04:00").astimezone(pytz.timezone('UTC'))
        self.assertFalse(psynudge.core.isWithinWindow(start, end))

        mock.return_value = dateutil.parser.parse("2020-01-11T03:59:59Z").astimezone(pytz.timezone('UTC'))
        start = dateutil.parser.parse("2020-01-10T00:00:00-04:00").astimezone(pytz.timezone('UTC'))
        end =   dateutil.parser.parse("2020-01-11T00:00:00-04:00").astimezone(pytz.timezone('UTC'))
        self.assertTrue(psynudge.core.isWithinWindow(start, end))

        mock.return_value = dateutil.parser.parse("2020-01-11T04:00:01Z").astimezone(pytz.timezone('UTC'))
        start = dateutil.parser.parse("2020-01-10T00:00:00-04:00").astimezone(pytz.timezone('UTC'))
        end =   dateutil.parser.parse("2020-01-11T00:00:00-04:00").astimezone(pytz.timezone('UTC'))
        self.assertFalse(psynudge.core.isWithinWindow(start, end))

        # UTC representation assertion check
        mock.return_value = dateutil.parser.parse("2020-01-10T00:00:00Z").astimezone(pytz.timezone('UTC'))
        start = dateutil.parser.parse("2020-01-09T00:00:00Z")
        end =   dateutil.parser.parse("2020-01-11T00:00:00Z")
        with self.assertRaises(AssertionError):
            self.assertTrue(psynudge.core.isWithinWindow(start, end))

class DatabaseTests(unittest.TestCase):

    db = mock_db.getMockDb() # wo participant, just studys and timepoints

    @db_session
    def test_updateParticipant_fromFile(self, db=db):

        psynudge.core.updateParticipant(
            db = db,
            ps_file_path = os.path.join(test_dir, 'fixtures', 'ps_data.json'),
            study = db.Study.select(lambda study: study.name=='indep_test').first())

        self.assertEqual(db.Participant.select().count(), 9)
        self.assertEqual(db.Participant.select().count()*2, db.Completion.select().count())

        # Check that Ids are correct
        ps_ids = [part.psId for part in db.Participant.select().fetch()]
        expected_ps_ids = ['001', '002', '003', '004', '005', '006', '007', '008', '009']
        for expected_ps_id in expected_ps_ids:
            self.assertTrue(expected_ps_id in ps_ids)

        #{"key":"test7", "email":"test7@test.net", "date":"2020-01-10T00:00:00+02:00", "id":"007"},
        test7p = db.Participant.select(lambda p: p.psId=='007').first()
        self.assertEqual(test7p.whenStart, '2020-01-09T22:00:00+00:00')
        self.assertEqual(test7p.whenFinish, '2020-01-18T22:00:00+00:00')

        #{"key":"test5", "email":"test5@test.net", "date":"2020-01-10T00:00:00Z", "id":"005"},
        test7p = db.Participant.select(lambda p: p.psId=='005').first()
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
            {"key":"test3", "email":"test3@test.net", "date":"2020-01-10T00:00:00-04:00", "id":"003"},
            {"key":"test4", "email":"test4@test.net", "date":"2020-01-10T00:00:00-01:00", "id":"004"},
            {"key":"test5", "email":"test5@test.net", "date":"2020-01-10T00:00:00Z"     , "id":"005"},
            {"key":"test6", "email":"test6@test.net", "date":"2020-01-10T00:00:00+01:00", "id":"006"},
            {"key":"test7", "email":"test7@test.net", "date":"2020-01-10T00:00:00+02:00", "id":"007"},
            {"key":"test8", "email":"test8@test.net", "date":"2020-01-10T00:00:00+03:00", "id":"008"},
            {"key":"test9", "email":"test9@test.net", "date":"2020-01-10T00:00:00+04:00", "id":"009"}]

        psynudge.core.updateParticipant(
            db = db,
            ps_data = mock_ps,
            study = db.Study.select(lambda study: study.name=='indep_test').first())

        self.assertEqual(db.Participant.select().count(), 9)
        self.assertEqual(db.Participant.select().count()*2, db.Completion.select().count())

        # Check that Ids are correct
        ps_ids = [part.psId for part in db.Participant.select().fetch()]
        expected_ps_ids = ['001', '002', '003', '004', '005', '006', '007', '008', '009']
        for expected_ps_id in expected_ps_ids:
            self.assertTrue(expected_ps_id in ps_ids)

        #{"key":"test7", "email":"test7@test.net", "date":"2020-01-10T00:00:00+02:00", "id":"007"},
        test7p = db.Participant.select(lambda p: p.psId=='007').first()
        self.assertEqual(test7p.whenStart, '2020-01-09T22:00:00+00:00')
        self.assertEqual(test7p.whenFinish, '2020-01-18T22:00:00+00:00')

        #{"key":"test5", "email":"test5@test.net", "date":"2020-01-10T00:00:00Z", "id":"005"},
        test7p = db.Participant.select(lambda p: p.psId=='005').first()
        self.assertEqual(test7p.whenStart, '2020-01-10T00:00:00+00:00')
        self.assertEqual(test7p.whenFinish, '2020-01-19T00:00:00+00:00')

        #{"key":"test1", "email":"test1@test.net", "date":"2020-01-10T00:00:00-04:00", "id":"001"},
        test7p = db.Participant.select(lambda p: p.psId=='001').first()
        self.assertEqual(test7p.whenStart, '2020-01-10T04:00:00+00:00')
        self.assertEqual(test7p.whenFinish, '2020-01-19T04:00:00+00:00')

        # Add duplcate participants
        mock_ps2 = [
            {"key":"001", "email":"test1@test.net", "date":"2020-01-10T00:00:00-04:00", "id":"001"},
            {"key":"005", "email":"test5@test.net", "date":"2020-01-10T00:00:00Z"     , "id":"005"},]

        psynudge.core.updateParticipant(
            db = db,
            ps_data = mock_ps2,
            study = db.Study.select(lambda study: study.name=='indep_test').first())

        self.assertEqual(db.Participant.select().count(), 9)
        self.assertEqual(db.Participant.select().count()*2, db.Completion.select().count())

        # Check that Ids are correct
        ps_ids = [part.psId for part in db.Participant.select().fetch()]
        expected_ps_ids = ['001', '002', '003', '004', '005', '006', '007', '008', '009']
        for expected_ps_id in expected_ps_ids:
            self.assertTrue(expected_ps_id in ps_ids)

        #{"key":"test5", "email":"test5@test.net", "date":"2020-01-10T00:00:00Z", "id":"005"},
        test7p = db.Participant.select(lambda p: p.psId=='005').first()
        self.assertEqual(test7p.whenStart, '2020-01-10T00:00:00+00:00')
        self.assertEqual(test7p.whenFinish, '2020-01-19T00:00:00+00:00')

        #{"key":"test1", "email":"test1@test.net", "date":"2020-01-10T00:00:00-04:00", "id":"001"},
        test7p = db.Participant.select(lambda p: p.psId=='001').first()
        self.assertEqual(test7p.whenStart, '2020-01-10T04:00:00+00:00')
        self.assertEqual(test7p.whenFinish, '2020-01-19T04:00:00+00:00')

        db.rollback()

    @db_session
    def test_deleteInactiveParticipants(self, db=db):

        psynudge.core.updateParticipant(
            db = db,
            ps_file_path = os.path.join(test_dir, 'fixtures', 'ps_data.json'),
            study = db.Study.select(lambda study: study.name=='indep_test').first())

        self.assertEqual(db.Participant.select().count(), 9)
        self.assertEqual(db.Completion.select().count(), db.Participant.select().count()*2)

        test5 = db.Participant.select(lambda p: p.psId=='005').first()
        test5.isActive = False
        psynudge.core.deleteInactiveParticipants(db=db)
        self.assertEqual(db.Participant.select().count(), 8)
        self.assertEqual(db.Completion.select().count(), db.Participant.select().count()*2)

        test5 = db.Participant.select(lambda p: p.psId=='001').first()
        test5.isActive = False
        psynudge.core.deleteInactiveParticipants(db=db)
        self.assertEqual(db.Participant.select().count(), 7)
        self.assertEqual(db.Completion.select().count(), db.Participant.select().count()*2)

        db.rollback()

    @db_session
    @mock.patch('psynudge.src.core.getUtcNow')
    def test_updateParticipantIsActive(self, mock, db=db):

        psynudge.core.updateParticipant(
            db = db,
            ps_file_path = os.path.join(test_dir, 'fixtures', 'ps_data.json'),
            study = db.Study.select(lambda study: study.name=='indep_test').first())

        self.assertEqual(db.Participant.select(lambda p: p.isActive is True).count(), 9)

        mock.return_value = dateutil.parser.parse("2020-01-18T23:59:59Z").astimezone(pytz.timezone('UTC'))
        psynudge.core.updateParticipantIsActive(db=db)
        self.assertEqual(db.Participant.select(lambda p: p.isActive is True).count(), 5)

        mock.return_value = dateutil.parser.parse("2020-01-19T00:00:01Z").astimezone(pytz.timezone('UTC'))
        psynudge.core.updateParticipantIsActive(db=db)
        self.assertEqual(db.Participant.select(lambda p: p.isActive is True).count(), 4)

        mock.return_value = dateutil.parser.parse("2022-01-10T00:00:00Z").astimezone(pytz.timezone('UTC'))
        psynudge.core.updateParticipantIsActive(db=db)
        self.assertEqual(db.Participant.select(lambda p: p.isActive is True).count(), 0)

        db.rollback()

    @db_session
    @mock.patch('psynudge.src.core.getUtcNow')
    def test_updateCompletionIsNeeded(self, mock, db=db):

        psynudge.core.updateParticipant(
            db = db,
            ps_file_path = os.path.join(test_dir, 'fixtures', 'ps_data.json'),
            study = db.Study.select(lambda study: study.name=='indep_test').first())

        self.assertEqual(db.Completion.select(lambda c: c.isNeeded is False).count(), 18)

        # Start dt: "2020-01-10T00:00:00Z"
        mock.return_value = dateutil.parser.parse("2020-01-01T12:12:12Z").astimezone(pytz.timezone('UTC'))
        psynudge.core.updateCompletionIsNeeded(db=db)
        self.assertEqual(db.Completion.select(lambda c: c.isNeeded is True).count(), 0)

        mock.return_value = dateutil.parser.parse("2020-01-10T23:59:59Z").astimezone(pytz.timezone('UTC'))
        psynudge.core.updateCompletionIsNeeded(db=db)
        self.assertEqual(db.Completion.select(lambda c: c.isNeeded is True).count(), 4)

        mock.return_value = dateutil.parser.parse("2020-01-11T00:00:11Z").astimezone(pytz.timezone('UTC'))
        psynudge.core.updateCompletionIsNeeded(db=db)
        self.assertEqual(db.Completion.select(lambda c: c.isNeeded is True).count(), 5)

        mock.return_value = dateutil.parser.parse("2020-01-11T12:12:12Z").astimezone(pytz.timezone('UTC'))
        psynudge.core.updateCompletionIsNeeded(db=db)
        self.assertEqual(db.Completion.select(lambda c: c.isNeeded is True).count(), 9)

        mock.return_value = dateutil.parser.parse("2020-01-11T23:59:59Z").astimezone(pytz.timezone('UTC'))
        psynudge.core.updateCompletionIsNeeded(db=db)
        self.assertEqual(db.Completion.select(lambda c: c.isNeeded is True).count(), 5)

        mock.return_value = dateutil.parser.parse("2020-01-12T00:00:11Z").astimezone(pytz.timezone('UTC'))
        psynudge.core.updateCompletionIsNeeded(db=db)
        self.assertEqual(db.Completion.select(lambda c: c.isNeeded is True).count(), 4)

        mock.return_value = dateutil.parser.parse("2022-01-15T00:00:00Z").astimezone(pytz.timezone('UTC'))
        psynudge.core.updateCompletionIsNeeded(db=db)
        self.assertEqual(db.Completion.select(lambda c: c.isNeeded is True).count(), 0)

        db.rollback()

    @db_session
    def test_updateIndepStudyComp(self, db=db):

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

        self.assertEqual(db.Completion.select().count(), 18)
        self.assertEqual(db.Completion.select(lambda c: c.isComplete is True).count(), 0)

        # Add completions for tp1
        tp1 = db.Timepoint.select(lambda tp: tp.name=='indep_tp1').first()
        fp = os.path.join(test_dir, 'fixtures', 'indep_tp1.json')
        psynudge.core.updateIndepStudyComp(db=db, timepoint=tp1, alchemy_file_path=fp)

        self.assertEqual(db.Completion.select().count(), 18)
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
        psynudge.core.updateIndepStudyComp(db=db, timepoint=tp2, alchemy_file_path=fp)

        self.assertEqual(db.Completion.select().count(), 18)
        self.assertEqual(db.Completion.select(lambda c: c.isComplete is True).count(), 2)

        self.assertFalse(
            db.Completion.select(lambda c: c.participant.psId=='001' and c.timepoint==tp2).first().isComplete)
        self.assertFalse(
            db.Completion.select(lambda c: c.participant.psId=='002' and c.timepoint==tp2).first().isComplete)
        self.assertTrue(
            db.Completion.select(lambda c: c.participant.psId=='003' and c.timepoint==tp2).first().isComplete)

        db.rollback()

    @db_session
    def test_updateStackStudyComp(self, db=db):

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

        self.assertEqual(db.Completion.select().count(), 18)
        self.assertEqual(db.Completion.select(lambda c: c.isComplete is True).count(), 0)

        # Add completions from stacked study JSON
        fp = os.path.join(test_dir, 'fixtures', 'stack.json')
        study = db.Study.select(lambda s: s.name=='stack_test').first()
        stack_tp1 = db.Timepoint.select(lambda tp: tp.name=='stack_tp1').first()
        stack_tp2 = db.Timepoint.select(lambda tp: tp.name=='stack_tp2').first()
        psynudge.core.updateStackStudyComp(db=db, study=study, alchemy_file_path=fp)

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


class PreRefactoringTests(unittest.TestCase):

    @unittest.skip('wip')
    def test_appendData(self, test_dir=test_dir):

        # Create test file
        test_data = [1,2,3]
        file_path = os.path.join(test_dir, 'fixtures/appendDataTest.json')
        with open(file_path, 'w+') as file:
            json.dump(test_data, file)

        with open(file_path, 'r') as file:
            file_data = json.load(file)
        self.assertEqual(file_data, [1,2,3])

        # Append to file
        psynudge.core.appendData(file_path, [4,5])

        with open(file_path, 'r') as file:
            file_data = json.load(file)
        self.assertEqual(file_data, [1,2,3,4,5])

    @unittest.skip('wip')
    def test_getDataFileName(self):

        data_dir = os.path.join(psynudge.core.base_dir, 'data')

        self.assertEqual(
            psynudge.core.getDataFileName(psynudge.indep_test_study, psynudge.indep_test_study.tps[0]),
            os.path.join(data_dir, 'indep_test_tp1.json')
        )

        self.assertEqual(
            psynudge.core.getDataFileName(psynudge.indep_test_study, psynudge.indep_test_study.tps[1]),
            os.path.join(data_dir, 'indep_test_tp2.json')
        )

        self.assertEqual(
            psynudge.core.getDataFileName(psynudge.stack_test_study, psynudge.stack_test_study.tps[0]),
            os.path.join(data_dir, 'stack_test_stack.json')
        )

        self.assertEqual(
            psynudge.core.getDataFileName(psynudge.stack_test_study, psynudge.stack_test_study.tps[1]),
            os.path.join(data_dir, 'stack_test_stack.json')
        )

    @unittest.skip('wip')
    @mock.patch('psynudge.src.core.getUtcNow')
    def test_readWriteLastTimeCheck(self, mock):

        mock.return_value = dateutil.parser.parse("2020-01-10T00:00:00Z").astimezone(pytz.timezone('UTC'))
        psynudge.core.writeLastCheckTime()
        lastTimeStr = psynudge.core.readLastCheckTime()
        self.assertEqual(lastTimeStr, '2020-01-10T00:00:00+00:00')
        self.assertEqual(
            dateutil.parser.parse("2020-01-10T00:00:00Z").astimezone(pytz.timezone('UTC')),
            dateutil.parser.parse(lastTimeStr))

        mock.return_value = dateutil.parser.parse("3020-01-10T06:07:55Z").astimezone(pytz.timezone('UTC'))
        psynudge.core.writeLastCheckTime()
        lastTimeStr = psynudge.core.readLastCheckTime()
        self.assertEqual(lastTimeStr, '3020-01-10T06:07:55+00:00')
        self.assertEqual(
            dateutil.parser.parse("3020-01-10T06:07:55Z").astimezone(pytz.timezone('UTC')),
            dateutil.parser.parse(lastTimeStr))

    @unittest.skip('wip')
    @mock.patch('psynudge.src.core.getUtcNow')
    def test_isWithinNudgeWindow(self, mock):

        mock.return_value = dateutil.parser.parse("2020-01-15T12:00:00Z").astimezone(pytz.timezone('UTC'))
        self.assertFalse(psynudge.core.isWithinNudgeWindow(self.dtStartUTC, self.tp))

        mock.return_value = dateutil.parser.parse("2020-01-16T12:00:00Z").astimezone(pytz.timezone('UTC'))
        self.assertFalse(psynudge.core.isWithinNudgeWindow(self.dtStartUTC, self.tp))

        # Just before nudge start
        mock.return_value = dateutil.parser.parse("2020-01-16T23:59:59Z").astimezone(pytz.timezone('UTC'))
        self.assertFalse(psynudge.core.isWithinNudgeWindow(self.dtStartUTC, self.tp))

        # Right on nudge start
        mock.return_value = dateutil.parser.parse("2020-01-17T00:00:00Z").astimezone(pytz.timezone('UTC'))
        self.assertTrue(psynudge.core.isWithinNudgeWindow(self.dtStartUTC, self.tp))

        mock.return_value = dateutil.parser.parse("2020-01-17T11:11:11Z").astimezone(pytz.timezone('UTC'))
        self.assertTrue(psynudge.core.isWithinNudgeWindow(self.dtStartUTC, self.tp))

        # Right on nudge end
        mock.return_value = dateutil.parser.parse("2020-01-18T00:00:00Z").astimezone(pytz.timezone('UTC'))
        self.assertTrue(psynudge.core.isWithinNudgeWindow(self.dtStartUTC, self.tp))

        # Right just after nudge end
        mock.return_value = dateutil.parser.parse("2020-01-18T00:00:01Z").astimezone(pytz.timezone('UTC'))
        self.assertFalse(psynudge.core.isWithinNudgeWindow(self.dtStartUTC, self.tp))

        mock.return_value = dateutil.parser.parse("2020-01-18T11:11:11Z").astimezone(pytz.timezone('UTC'))
        self.assertFalse(psynudge.core.isWithinNudgeWindow(self.dtStartUTC, self.tp))

    @unittest.skip('wip')
    @mock.patch('psynudge.src.core.isWithinNudgeWindow')
    @mock.patch('psynudge.src.core.isCompleted')
    def test_isNudge(self, mockIsCompleted, mockIsWithinNudgeWindow):

        mockIsCompleted.return_value = False
        mockIsWithinNudgeWindow.return_value = False
        self.assertFalse(psynudge.core.isNudge(userId='000', dtStartUTC=self.dtStartUTC, tp=self.tp, surveyData=[]))

        mockIsCompleted.return_value = True
        mockIsWithinNudgeWindow.return_value = False
        self.assertFalse(psynudge.core.isNudge(userId='000', dtStartUTC=self.dtStartUTC, tp=self.tp, surveyData=[]))

        mockIsCompleted.return_value = False
        mockIsWithinNudgeWindow.return_value = True
        self.assertTrue(psynudge.core.isNudge(userId='000', dtStartUTC=self.dtStartUTC, tp=self.tp, surveyData=[]))

        mockIsCompleted.return_value = True
        mockIsWithinNudgeWindow.return_value = True
        self.assertFalse(psynudge.core.isNudge(userId='000', dtStartUTC=self.dtStartUTC, tp=self.tp, surveyData=[]))

    @unittest.skip('wip')
    def test_isCompleted(self):
        """
        https://survey.alchemer.eu/s3/90288073/indep-tp1?sguid=002 # Done - started, not finished
        https://survey.alchemer.eu/s3/90288073/indep-tp1?sguid=003 # Done - finished

        https://survey.alchemer.eu/s3/90288074/indep-tp2?sguid=002 # Survey did nto work for soem reason
        https://survey.alchemer.eu/s3/90288074/indep-tp2?sguid=003  # Survey did nto work for soem reason

        https://survey.alchemer.eu/s3/90289410/indep-tp2-copy?sguid=002 # Done - started, not finished
        https://survey.alchemer.eu/s3/90289410/indep-tp2-copy?sguid=003 # Done, finished

        https://survey.alchemer.eu/s3/90286853/stack?sguid=002                # Done - started, not finished
        https://survey.alchemer.eu/s3/90286853/stack?sguid=002&__sgtarget=5   # Done - started, not finished
        https://survey.alchemer.eu/s3/90286853/stack?sguid=003                # Done - finished both
        https://survey.alchemer.eu/s3/90286853/stack?sguid=003&__sgtarget=5   # Done - finished both
        https://survey.alchemer.eu/s3/90286853/stack?sguid=004                # Done - started TP1, finished TP2
        https://survey.alchemer.eu/s3/90286853/stack?sguid=004&__sgtarget=5   # Done - started TP1, finished TP2
        https://survey.alchemer.eu/s3/90286853/stack?sguid=005                # Done - finished TP1, started TP2
        https://survey.alchemer.eu/s3/90286853/stack?sguid=005&__sgtarget=5   # Done - finished TP1, started TP2
        """

        # Independent study case
        file_path=os.path.join(test_dir, 'fixtures/indep_test_tp1.json')
        with open(file_path, 'r') as file:
            surveyDataTP1 = json.load(file)

        file_path=os.path.join(test_dir, 'fixtures/indep_test_tp2.json')
        with open(file_path, 'r') as file:
            surveyDataTP2 = json.load(file)

        for tp in psynudge.indep_test_study.tps:
            if tp.name=='tp1':
                tp1 = tp

        for tp in psynudge.indep_test_study.tps:
            if tp.name=='tp2':
                tp2 = tp

        self.assertFalse(
            psynudge.core.isCompleted(userId='001', surveyData=surveyDataTP1, firstQID=tp1.firstQID, lastQID=tp1.lastQID))
        self.assertFalse(
            psynudge.core.isCompleted(userId='002', surveyData=surveyDataTP1, firstQID=tp1.firstQID, lastQID=tp1.lastQID))
        self.assertTrue(
            psynudge.core.isCompleted(userId='003', surveyData=surveyDataTP1, firstQID=tp1.firstQID, lastQID=tp1.lastQID))

        self.assertFalse(
            psynudge.core.isCompleted(userId='001', surveyData=surveyDataTP2, firstQID=tp2.firstQID, lastQID=tp2.lastQID))
        self.assertFalse(
            psynudge.core.isCompleted(userId='002', surveyData=surveyDataTP2, firstQID=tp2.firstQID, lastQID=tp2.lastQID))
        self.assertTrue(
            psynudge.core.isCompleted(userId='003', surveyData=surveyDataTP2, firstQID=tp2.firstQID, lastQID=tp2.lastQID))


        # stack study case
        file_path=os.path.join(test_dir, 'fixtures/stack_test_stack.json')
        with open(file_path, 'r') as file:
            surveyData = json.load(file)

        for tp in psynudge.stack_test_study.tps:
            if tp.name=='tp1':
                tp1 = tp

        for tp in psynudge.stack_test_study.tps:
            if tp.name=='tp2':
                tp2 = tp

        self.assertFalse(
            psynudge.core.isCompleted(userId='001', surveyData=surveyData, firstQID=tp1.firstQID, lastQID=tp1.lastQID))
        self.assertFalse(
            psynudge.core.isCompleted(userId='002', surveyData=surveyData, firstQID=tp1.firstQID, lastQID=tp1.lastQID))
        self.assertTrue(
            psynudge.core.isCompleted(userId='003', surveyData=surveyData, firstQID=tp1.firstQID, lastQID=tp1.lastQID))

        self.assertFalse(
            psynudge.core.isCompleted(userId='001', surveyData=surveyData, firstQID=tp2.firstQID, lastQID=tp2.lastQID))
        self.assertFalse(
            psynudge.core.isCompleted(userId='002', surveyData=surveyData, firstQID=tp2.firstQID, lastQID=tp2.lastQID))
        self.assertTrue(
            psynudge.core.isCompleted(userId='003', surveyData=surveyData, firstQID=tp2.firstQID, lastQID=tp2.lastQID))

    @unittest.skip('wip')
    def test_getResponseSguid(self):

        # Only URL SGUID variable
        response= {
         'url_variables': {'sguid':
                            {'key': 'sguid',
                             'value': 'Qwwm5fd6fdlllll6',
                             'type': 'url'}},
         'survey_data': {
           '72': {
                'id': 72,
                'type': 'HIDDEN',
                'question': 'Capture SGUID',
                'section_id': 4,
                'shown': False}}}
        self.assertEqual(psynudge.core.getResponseSguid(response), 'Qwwm5fd6fdlllll6')

        # Only hidden SGUID variable
        response= {
         'id': '666',
         'url_variables': {},
         'survey_data': {
             '72': {'id': 72,
             'type': 'HIDDEN',
             'question': 'Capture SGUID',
             'answer': 'Qwwm5fd6fdlllll6',
             'shown': True}}}
        self.assertEqual(psynudge.core.getResponseSguid(response), 'Qwwm5fd6fdlllll6')

        # Both hidden + URL SGUID variable - match
        response = {
         'id': '666',
         'url_variables': {'sguid':
                            {'key': 'sguid',
                             'value': 'Qwwm5fd6fdlllll6',
                             'type': 'url'}},
         'survey_data': {
             '72': {'id': 72,
             'type': 'HIDDEN',
             'question': 'Capture SGUID',
             'answer': 'Qwwm5fd6fdlllll6',
             'shown': True}}}
        self.assertEqual(psynudge.core.getResponseSguid(response), 'Qwwm5fd6fdlllll6')

        # Both hidden + URL SGUID variable - mismatch
        response = {
         'id': '666',
         'url_variables': {'sguid':
                            {'key': 'sguid',
                             'value': 'Qwwm5fd6fdlllll6',
                             'type': 'url'}},
         'survey_data': {
             '72': {'id': 72,
             'type': 'HIDDEN',
             'question': 'Capture SGUID',
             'answer': 'aaaaaaaaaaaaaaaaa',
             'shown': True}}}
        with self.assertRaises(AssertionError):
            psynudge.core.getResponseSguid(response)

        # Neither SGUID sources are present
        response = {
         'id': '666',
         'url_variables': {'AAAA':
                            {'key': 'sguid',
                             'value': 'Qwwm5fd6fdlllll6',
                             'type': 'url'}},
         'survey_data': {
             '72': {'id': 72,
             'type': 'HIDDEN',
             'question': 'BBBB',
             'answer': 'aaaaaaaaaaaaaaaaa',
             'shown': True}}}
        with self.assertRaises(AssertionError):
            psynudge.core.getResponseSguid(response)

    @unittest.skip('wip')
    def test_isNudgeSent(self):

        test_db = psynudge.db.getDb(filepath=':memory:', create_db=True)

        with db_session:
            test_db.Nudge(userId='1', studyId='2', surveyId='3', isSent=True)
            test_db.Nudge(userId='2', studyId='3', surveyId='4', isSent=True)
            test_db.Nudge(userId='3', studyId='4', surveyId='5', isSent=False)

        self.assertFalse(psynudge.core.isNudgeSent(userId='9', studyId='9', surveyId='9', db=test_db))
        self.assertTrue(psynudge.core.isNudgeSent(userId='1', studyId='2', surveyId='3', db=test_db))
        self.assertTrue(psynudge.core.isNudgeSent(userId='2', studyId='3', surveyId='4', db=test_db))

        with self.assertRaises(AssertionError):
            psynudge.core.isNudgeSent(userId='3', studyId='4', surveyId='5', db=test_db)

        with db_session:
            test_db.Nudge(userId='1', studyId='2', surveyId='3', isSent=True)

        with self.assertRaises(AssertionError):
            psynudge.core.isNudgeSent(userId='1', studyId='2', surveyId='3', db=test_db)
