"""
:Author: Balazs Szigeti <b.islander@protonmail.com>
:Copyright: 2020, DrugNerdsLab
:License: MIT
"""

import unittest
from unittest import mock
import datetime
import dateutil.parser
import psynudge
import pytz


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
