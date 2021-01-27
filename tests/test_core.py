"""
:Author: Balazs Szigeti <b.islander@protonmail.com>
:Copyright: 2020, DrugNerdsLab
:License: MIT

python -m pytest psynudge/tests/
"""

from pony.orm import db_session
from unittest import mock
import dateutil.parser
import psynudge
import unittest
import pytz
import json
import os

db = psynudge.db.build_empty_db(filepath=':memory:', create_db=True, mock_db=True) # DB wo participant, just studys and timepoints


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
            os.path.join(data_dir, 'indep_study_sg_indep_tp1_from(2020-02-02T00:00:00)_to(2021-04-04T00:00:00).json')
        )

        self.assertEqual(
            psynudge.core.getDataFilePath(study=indep_study, tp=indep_tp2, source='sg'),
            os.path.join(data_dir, 'indep_study_sg_indep_tp2_from(2020-03-03T00:00:00)_to(2021-04-04T00:00:00).json')
        )

        self.assertEqual(
            psynudge.core.getDataFilePath(study=indep_study, source='ps'),
            os.path.join(data_dir, 'indep_study_ps_to(2021-04-04T00:00:00).json')
        )

        stack_tp1.lastSgCheck = '2020-02-22T00:00:00+00:00'
        stack_tp2.lastSgCheck = '2020-02-22T00:00:00+00:00'

        self.assertEqual(
            psynudge.core.getDataFilePath(study=stack_study, source='sg'),
            os.path.join(data_dir, 'stack_study_sg_stack_from(2020-02-22T00:00:00)_to(2021-04-04T00:00:00).json')
        )

        db.rollback()

    @db_session
    def test_getSgData(self):
        # The 4 responses for stack mock survey were submitted at:
        # 2020-11-06T10:58:09+00:00
        # 2020-11-06T11:02:18+00:00
        # 2020-11-06T11:04:22+00:00
        # 2020-11-06T11:05:14+00:00

        stack_study = db.Study.select(lambda s: s.name=='stack_study').first()

        for tp in stack_study.timepoints: # No new submissions
            tp.lastSgCheck = '2020-11-11T11:11:11+00:00'
        sg_json = psynudge.core.getSgData(study=stack_study)
        self.assertEqual(sg_json['total_count'], 0)

        for tp in stack_study.timepoints: # One new submissions
            tp.lastSgCheck = '2020-11-06T11:04:44+00:00'
        sg_json = psynudge.core.getSgData(study=stack_study)
        self.assertEqual(sg_json['total_count'], 1)

        for tp in stack_study.timepoints: # One new submissions
            tp.lastSgCheck = '2020-11-06T10:58:08+00:00'
        sg_json = psynudge.core.getSgData(study=stack_study)
        self.assertEqual(sg_json['total_count'], 4)

        # The 2 responses for indep mock survey were submitted at:
        # 2020-11-06T11:13:49+00:00
        # 2020-11-06T11:14:01+00:00

        indep_study = db.Study.select(lambda s: s.name=='indep_study').first()
        tp = db.Timepoint.select(lambda tp: tp.name=='indep_tp2').first()

        tp.lastSgCheck = '2020-11-06T11:13:40+00:00'
        sg_json = psynudge.core.getSgData(study=indep_study, tp=tp)
        self.assertEqual(sg_json['total_count'], 2)

        tp.lastSgCheck = '2020-11-06T11:13:50+00:00'
        sg_json = psynudge.core.getSgData(study=indep_study, tp=tp)
        self.assertEqual(sg_json['total_count'], 1)

        tp.lastSgCheck = '2020-11-06T11:16:40+00:00'
        sg_json = psynudge.core.getSgData(study=indep_study, tp=tp)
        self.assertEqual(sg_json['total_count'], 0)
