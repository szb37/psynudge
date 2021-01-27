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

#test_dir = os.path.dirname(os.path.abspath(__file__))
#db = psynudge.db.build_db(filepath=':memory:', create_db=True) # DB wo participant, just studys and timepoints


class DatetimeTests(unittest.TestCase):
    """ Tests for datetime manipulations """

    dtStartUTC = dateutil.parser.parse("2020-01-10T00:00:00Z").astimezone(pytz.timezone('UTC'))

    def test_iso2dt(self):

        dt_loc = psynudge.mydt.iso2dt('2020-01-10T00:00:00Z')
        self.assertEqual(dt_loc, dateutil.parser.parse('2020-01-10T00:00:00Z').astimezone(pytz.timezone('UTC')))

        dt_loc = psynudge.mydt.iso2dt('2020-01-10T00:00:00+00:00')
        self.assertEqual(dt_loc, dateutil.parser.parse('2020-01-10T00:00:00Z').astimezone(pytz.timezone('UTC')))

        dt_loc = psynudge.mydt.iso2dt('2020-01-10T00:00:00+02:00')
        dt_utc = psynudge.mydt.iso2utcdt('2020-01-10T00:00:00+02:00')
        self.assertEqual(dt_loc.astimezone(pytz.timezone('UTC')), dt_utc)
        self.assertEqual(dt_loc.astimezone(pytz.timezone('UTC')), dateutil.parser.parse('2020-01-10T00:00:00+02:00').astimezone(pytz.timezone('UTC')))

        dt_loc = psynudge.mydt.iso2dt('2020-01-10T00:00:00-03:00')
        dt_utc = psynudge.mydt.iso2utcdt('2020-01-10T00:00:00-03:00')
        self.assertEqual(dt_loc.astimezone(pytz.timezone('UTC')), dt_utc)
        self.assertEqual(dt_loc.astimezone(pytz.timezone('UTC')), dateutil.parser.parse('2020-01-10T00:00:00-03:00').astimezone(pytz.timezone('UTC')))

    def test_iso2utcdt(self):

        dt_utc = psynudge.mydt.iso2utcdt('2020-01-10T00:00:00Z')
        self.assertEqual(dt_utc, dateutil.parser.parse('2020-01-10T00:00:00Z').astimezone(pytz.timezone('UTC')))

        dt_utc = psynudge.mydt.iso2utcdt('2020-01-10T00:00:00+00:00')
        self.assertEqual(dt_utc, dateutil.parser.parse('2020-01-10T00:00:00Z').astimezone(pytz.timezone('UTC')))

        dt_utc = psynudge.mydt.iso2utcdt('2020-01-10T00:00:00+02:00')
        self.assertEqual(dt_utc, dateutil.parser.parse('2020-01-10T00:00:00+02:00').astimezone(pytz.timezone('UTC')))

        dt_utc = psynudge.mydt.iso2utcdt('2020-01-10T00:00:00-03:00')
        self.assertEqual(dt_utc, dateutil.parser.parse('2020-01-10T00:00:00-03:00').astimezone(pytz.timezone('UTC')))

    @mock.patch('psynudge.src.mydt.getUtcNow')
    def test_isWithinTimeWindow(self, mock):

        mock.return_value = dateutil.parser.parse("2020-01-10T00:00:00Z").astimezone(pytz.timezone('UTC'))
        start = dateutil.parser.parse("2020-01-09T00:00:00Z").astimezone(pytz.timezone('UTC'))
        end =   dateutil.parser.parse("2020-01-11T00:00:00Z").astimezone(pytz.timezone('UTC'))
        self.assertTrue(psynudge.mydt.isWithinTimeWindow(start, end))

        mock.return_value = dateutil.parser.parse("2020-01-08T00:00:00Z").astimezone(pytz.timezone('UTC'))
        start = dateutil.parser.parse("2020-01-09T00:00:00Z").astimezone(pytz.timezone('UTC'))
        end =   dateutil.parser.parse("2020-01-11T00:00:00Z").astimezone(pytz.timezone('UTC'))
        self.assertFalse(psynudge.mydt.isWithinTimeWindow(start, end))

        # Cases when time zone is non UTC
        mock.return_value = dateutil.parser.parse("2020-01-10T04:00:01Z").astimezone(pytz.timezone('UTC'))
        start = dateutil.parser.parse("2020-01-10T00:00:00-04:00").astimezone(pytz.timezone('UTC'))
        end =   dateutil.parser.parse("2020-01-11T00:00:00-04:00").astimezone(pytz.timezone('UTC'))
        self.assertTrue(psynudge.mydt.isWithinTimeWindow(start, end))

        mock.return_value = dateutil.parser.parse("2020-01-10T03:59:59Z").astimezone(pytz.timezone('UTC'))
        start = dateutil.parser.parse("2020-01-10T00:00:00-04:00").astimezone(pytz.timezone('UTC'))
        end =   dateutil.parser.parse("2020-01-11T00:00:00-04:00").astimezone(pytz.timezone('UTC'))
        self.assertFalse(psynudge.mydt.isWithinTimeWindow(start, end))

        mock.return_value = dateutil.parser.parse("2020-01-11T03:59:59Z").astimezone(pytz.timezone('UTC'))
        start = dateutil.parser.parse("2020-01-10T00:00:00-04:00").astimezone(pytz.timezone('UTC'))
        end =   dateutil.parser.parse("2020-01-11T00:00:00-04:00").astimezone(pytz.timezone('UTC'))
        self.assertTrue(psynudge.mydt.isWithinTimeWindow(start, end))

        mock.return_value = dateutil.parser.parse("2020-01-11T04:00:01Z").astimezone(pytz.timezone('UTC'))
        start = dateutil.parser.parse("2020-01-10T00:00:00-04:00").astimezone(pytz.timezone('UTC'))
        end =   dateutil.parser.parse("2020-01-11T00:00:00-04:00").astimezone(pytz.timezone('UTC'))
        self.assertFalse(psynudge.mydt.isWithinTimeWindow(start, end))

        # UTC representation assertion check
        mock.return_value = dateutil.parser.parse("2020-01-10T00:00:00Z").astimezone(pytz.timezone('UTC'))
        start = dateutil.parser.parse("2020-01-09T00:00:00Z")
        end =   dateutil.parser.parse("2020-01-11T00:00:00Z")
        with self.assertRaises(AssertionError):
            self.assertTrue(psynudge.mydt.isWithinTimeWindow(start, end))
