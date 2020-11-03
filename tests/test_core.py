"""
:Author: Balazs Szigeti <b.islander@protonmail.com>
:Copyright: 2020, DrugNerdsLab
:License: MIT
"""


from unittest import mock
import dateutil.parser
import datetime
import psynudge
import unittest
import pytz
import json
import os

test_dir = os.path.dirname(os.path.abspath(__file__))

class CoreTestSuit(unittest.TestCase):

    def test_convert_iso2dt(self):

        dt_loc, dt_utc = psynudge.core.convert_iso2dt('2020-01-10T00:00:00Z')
        self.assertEqual(dt_loc, dateutil.parser.parse('2020-01-10T00:00:00Z').astimezone(pytz.timezone('UTC')))
        self.assertEqual(dt_utc, dateutil.parser.parse('2020-01-10T00:00:00Z').astimezone(pytz.timezone('UTC')))

        dt_loc, dt_utc = psynudge.core.convert_iso2dt('2020-01-10T00:00:00+02:00')
        self.assertEqual(dt_loc.astimezone(pytz.timezone('UTC')), dt_utc)
        self.assertEqual(dt_loc.astimezone(pytz.timezone('UTC')), dateutil.parser.parse('2020-01-10T00:00:00+02:00').astimezone(pytz.timezone('UTC')))
        self.assertEqual(dt_utc, dateutil.parser.parse('2020-01-10T00:00:00+02:00').astimezone(pytz.timezone('UTC')))

        dt_loc, dt_utc = psynudge.core.convert_iso2dt('2020-01-10T00:00:00-03:00')
        self.assertEqual(dt_loc.astimezone(pytz.timezone('UTC')), dt_utc)
        self.assertEqual(dt_loc.astimezone(pytz.timezone('UTC')), dateutil.parser.parse('2020-01-10T00:00:00-03:00').astimezone(pytz.timezone('UTC')))
        self.assertEqual(dt_utc, dateutil.parser.parse('2020-01-10T00:00:00-03:00').astimezone(pytz.timezone('UTC')))

    @mock.patch('psynudge.src.core.getNowUtc')
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
