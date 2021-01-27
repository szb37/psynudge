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

db = psynudge.db.build_db(filepath=':memory:', create_db=True) # DB wo participant, just studys and timepoints


class CoreTests(unittest.TestCase):

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

    @db_session
    @mock.patch('psynudge.src.core.getUtcNow')
    def test_getDataFileName(self, mockNow):

        data_dir = os.path.join(psynudge.core.base_dir, 'data')
        indep_study = db.Study.select(lambda s: s.type.type=='indep').first()
        stack_study = db.Study.select(lambda s: s.type.type=='stack').first()
        indep_tp1 = db.Timepoint.select(lambda tp: tp.name=='indep_tp1').first()
        indep_tp2 = db.Timepoint.select(lambda tp: tp.name=='indep_tp2').first()
        stack_tp1 = db.Timepoint.select(lambda tp: tp.name=='stack_tp1').first()
        stack_tp2 = db.Timepoint.select(lambda tp: tp.name=='stack_tp2').first()

        indep_study.lastPsCheck = '2020-01-01T00:00:00+00:00'
        indep_tp1.lastSgCheck   = '2020-02-02T00:00:00+00:00'
        indep_tp2.lastSgCheck   = '2020-03-03T00:00:00+00:00'
        mockNow.return_value = dateutil.parser.parse('2021-04-04T00:00:00Z').astimezone(pytz.timezone('UTC'))

        self.assertEqual(
            psynudge.core.getDataFilePath(study=indep_study, tp=indep_tp1, source='sg'),
            os.path.join(data_dir, 'indep_test_sg_indep_tp1_from(2020-02-02T00:00:00)_to(2021-04-04T00:00:00).json')
        )

        self.assertEqual(
            psynudge.core.getDataFilePath(study=indep_study, tp=indep_tp2, source='sg'),
            os.path.join(data_dir, 'indep_test_sg_indep_tp2_from(2020-03-03T00:00:00)_to(2021-04-04T00:00:00).json')
        )

        self.assertEqual(
            psynudge.core.getDataFilePath(study=indep_study, source='ps'),
            os.path.join(data_dir, 'indep_test_ps_to(2021-04-04T00:00:00).json')
        )

        stack_tp1.lastSgCheck = '2020-02-22T00:00:00+00:00'
        stack_tp2.lastSgCheck = '2020-02-22T00:00:00+00:00'

        self.assertEqual(
            psynudge.core.getDataFilePath(study=stack_study, source='sg'),
            os.path.join(data_dir, 'stack_test_sg_stack_from(2020-02-22T00:00:00)_to(2021-04-04T00:00:00).json')
        )

        db.rollback()
