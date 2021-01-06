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
import unittest
import pytz
import json
import os

test_dir = os.path.dirname(os.path.abspath(__file__))

class CoreTestSuit(unittest.TestCase):

    tp = psynudge.Timepoint(
        name='test',
        surveyId='000',
        td2start=datetime.timedelta(days=6),
        td2end=datetime.timedelta(days=1),
        td2nudge=datetime.timedelta(days=1),
        )
    dtStartUTC = dateutil.parser.parse("2020-01-10T00:00:00Z").astimezone(pytz.timezone('UTC'))

    def test_iso2dt(self):

        dt_loc, dt_utc = psynudge.core.iso2dt('2020-01-10T00:00:00Z')
        self.assertEqual(dt_loc, dateutil.parser.parse('2020-01-10T00:00:00Z').astimezone(pytz.timezone('UTC')))
        self.assertEqual(dt_utc, dateutil.parser.parse('2020-01-10T00:00:00Z').astimezone(pytz.timezone('UTC')))

        dt_loc, dt_utc = psynudge.core.iso2dt('2020-01-10T00:00:00+02:00')
        self.assertEqual(dt_loc.astimezone(pytz.timezone('UTC')), dt_utc)
        self.assertEqual(dt_loc.astimezone(pytz.timezone('UTC')), dateutil.parser.parse('2020-01-10T00:00:00+02:00').astimezone(pytz.timezone('UTC')))
        self.assertEqual(dt_utc, dateutil.parser.parse('2020-01-10T00:00:00+02:00').astimezone(pytz.timezone('UTC')))

        dt_loc, dt_utc = psynudge.core.iso2dt('2020-01-10T00:00:00-03:00')
        self.assertEqual(dt_loc.astimezone(pytz.timezone('UTC')), dt_utc)
        self.assertEqual(dt_loc.astimezone(pytz.timezone('UTC')), dateutil.parser.parse('2020-01-10T00:00:00-03:00').astimezone(pytz.timezone('UTC')))
        self.assertEqual(dt_utc, dateutil.parser.parse('2020-01-10T00:00:00-03:00').astimezone(pytz.timezone('UTC')))

    @mock.patch('psynudge.src.core.getUTCnow')
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
            psynudge.core.getDataFileName(psynudge.stacked_test_study, psynudge.stacked_test_study.tps[0]),
            os.path.join(data_dir, 'stacked_test_stacked.json')
        )

        self.assertEqual(
            psynudge.core.getDataFileName(psynudge.stacked_test_study, psynudge.stacked_test_study.tps[1]),
            os.path.join(data_dir, 'stacked_test_stacked.json')
        )

    @mock.patch('psynudge.src.core.getUTCnow')
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

    @mock.patch('psynudge.src.core.getUTCnow')
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

    def test_isCompleted(self):
        """
        https://survey.alchemer.eu/s3/90288073/indep-tp1?sguid=002 # Done - started, not finished
        https://survey.alchemer.eu/s3/90288073/indep-tp1?sguid=003 # Done - finished

        https://survey.alchemer.eu/s3/90288074/indep-tp2?sguid=002 # Survey did nto work for soem reason
        https://survey.alchemer.eu/s3/90288074/indep-tp2?sguid=003  # Survey did nto work for soem reason

        https://survey.alchemer.eu/s3/90289410/indep-tp2-copy?sguid=002 # Done - started, not finished
        https://survey.alchemer.eu/s3/90289410/indep-tp2-copy?sguid=003 # Done, finished

        https://survey.alchemer.eu/s3/90286853/stacked?sguid=002                # Done - started, not finished
        https://survey.alchemer.eu/s3/90286853/stacked?sguid=002&__sgtarget=5   # Done - started, not finished
        https://survey.alchemer.eu/s3/90286853/stacked?sguid=003                # Done - finished both
        https://survey.alchemer.eu/s3/90286853/stacked?sguid=003&__sgtarget=5   # Done - finished both
        https://survey.alchemer.eu/s3/90286853/stacked?sguid=004                # Done - started TP1, finished TP2
        https://survey.alchemer.eu/s3/90286853/stacked?sguid=004&__sgtarget=5   # Done - started TP1, finished TP2
        https://survey.alchemer.eu/s3/90286853/stacked?sguid=005                # Done - finished TP1, started TP2
        https://survey.alchemer.eu/s3/90286853/stacked?sguid=005&__sgtarget=5   # Done - finished TP1, started TP2
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


        # Stacked study case
        file_path=os.path.join(test_dir, 'fixtures/stacked_test_stacked.json')
        with open(file_path, 'r') as file:
            surveyData = json.load(file)

        for tp in psynudge.stacked_test_study.tps:
            if tp.name=='tp1':
                tp1 = tp

        for tp in psynudge.stacked_test_study.tps:
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
