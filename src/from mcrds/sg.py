"""
Methods to access and manipulate SG (questionnaire platform) data

:Author: Balazs Szigeti <szbazsu@gmail.com>
:Copyright: 2019, DrugNerdsLab
:License: MIT
"""

from mcrds.src.questions import survey_questions, qids_responses
from mcrds.access_tokens import sg_api_token, sg_api_token_secret
from mcrds.config import sg_surveys
from pony.orm.core import ObjectNotFound
from pony.orm import commit, db_session, select, show
from surveygizmo import SurveyGizmo
from mcrds.src import datemanager
from mcrds.src.database_entities import *
from mcrds.src.globals import *
from mcrds.src.errors import *
from bs4 import BeautifulSoup
from mcrds.src import io
import logging
import itertools
import datetime
import json
import copy
import os


class SgClient():
    """ Methods to download ang manage data from SG """

    def download_data(save=True):
        """ Download SG data from servers, put together pages and save concatenated JSON to disk """

        client = SurveyGizmo(api_version='v5',
                             response_type='json',
                             api_token = sg_api_token,
                             api_token_secret = sg_api_token_secret)

        client.config.base_url = 'https://restapi.surveygizmo.eu/'

        # Create folder
        now_dt  = datetime.datetime.now()
        date_str = datemanager.dt2str(now_dt)
        data_folder = os.path.join(BASE_DIR, 'data/SG/', date_str)
        os.makedirs(data_folder)

        sg_data={}

        for survey_name in sg_surveys.keys():

            pages = []
            surveyID = sg_surveys[survey_name]
            temp = client.api.surveyresponse.list(surveyID)

            if isinstance(temp,str): # Not sure why, but sometimes getting str response
                temp=json.loads(temp)
                assert isinstance(temp, dict)

            total_pages = int(temp['total_pages'])

            for nPage in range(1, total_pages+1):

                survey_page = client.api.surveyresponse.page(nPage).list(surveyID)
                if isinstance(survey_page,str): # Not sure why, but sometimes getting str response
                    survey_page=json.loads(survey_page)
                    assert isinstance(survey_page, dict)
                assert(isinstance(survey_page, dict))

                print("Saving page {} (out of {}) of survey '{}'.".format(nPage, total_pages, survey_name))
                pages.append(survey_page)

                # Save individual page file
                file_name = '{}_page_{}.json'.format(survey_name, nPage)
                file = open(os.path.join(data_folder, file_name), "w")
                file.write(json.dumps(survey_page))
                file.close()

            # Concatenate JSONs on data
            print("Finished downloading data for '{}'.".format(survey_name))
            print('Concatenate JSONs.')
            assert(len(pages)==total_pages)

            for pageIdx, survey_page in enumerate(pages):

                if pageIdx == 0:
                    conSurveyPages = survey_page
                    continue

                conSurveyPages['data'] = conSurveyPages['data'] + survey_page['data']
                conSurveyPages['page'] = str(conSurveyPages['page']) + '+' + str(survey_page['page'])

            sg_data[survey_name] = conSurveyPages

        # Saving SG data
        print("Completed SG data aggregation.")

        if save:
            print("Saving 'sg_data_YYYY_MM_DD_HH_MM.json'.")
            filename  = 'sg_data_' + date_str + '.json'
            file = open(os.path.join(BASE_DIR, 'data/SG/', filename), "w")
            json_str = json.dumps(sg_data)
            file.write(json_str)
            file.close()

class SgMiner():
    """ Methods to get information from SG data """

    @staticmethod
    def get_response(responses=None, trial_id=None):
        """ Finds response with trial ID

            Input:
                responses: SG_DATA[survey_name]
            Returns:
                SG_DATA[survey_name]['data'][trial_id=trial_id]['survey_data']
            Raises:
                ResponseNotFound
                MultipleResponsesFound
        """

        assert isinstance(responses, dict)
        assert isinstance(trial_id, str)
        responses = responses['data']
        assert isinstance(responses, list)

        matched_responses = []
        for response in responses:
            sguid=None

            try:
                sguid = SgMiner.get_response_sguid(response)
            except MissingSGUID:
                pass

            if sguid == trial_id:
                matched_responses.append(response)

        if len(matched_responses)==1:
            assert 'survey_data' in matched_responses[0].keys()
            return matched_responses[0]['survey_data']
        elif len(matched_responses)==0:
            raise ResponseNotFound()
        else:
            raise MultipleResponsesFound()

        raise MCRDSException()

    @staticmethod
    def get_response_sguid(response):
        """ Returns SGUID of an SG response

            Input:
                response: element of SG_DATA[survey_name]['data']
            Returns:
                SGUID:
            Raises:
                MissingSGUID:
                MCRDSException: did not reach return statement
        """

        sguid_url    = None
        sguid_hidden = None

        try:
            query = SgMiner.get_question(response['survey_data'], 'sguid')
            sguid_hidden = query['answer']
        except (QuestionNotFound, QuestionFoundButNotShown, KeyError):
            pass

        try:
            sguid_url = response['url_variables']['sguid']['value']
        except:
            pass

        if isinstance(sguid_url, str) and isinstance(sguid_hidden, str):
            assert(sguid_url==sguid_hidden) # Both SGUID sources found, but they disagree
            return sguid_url
        elif isinstance(sguid_url, str) and sguid_hidden is None:
            return sguid_url
        elif sguid_url is None and isinstance(sguid_hidden, str):
            return sguid_hidden
        elif sguid_url is None and sguid_hidden is None:
            raise MissingSGUID()

        raise MCRDSException()

    @staticmethod
    def get_question(response, question):
        """ Returns element of SG_DATA[survey_name]['data'][x]['survey_data'] dict with matching 'question'

            Input:
                response: element of SG_DATA[survey_name]['data']
            Returns:
                 item: SG_DATA[survey_name]['data'][x]['survey_data'][question = question]
            Raises:
                QuestionNotFound()
                QuestionFoundButNotShown()
                MCRDSException: did not reach return statement
        """

        assert(isinstance(response, dict))
        assert(isinstance(question, str))

        question_in_bold = '<strong>' + question + '</strong>'
        item_match = []

        for item in response:
            assert 'question' in response[item].keys()
            if (response[item]['question']==question) or (response[item]['question']==question_in_bold):
                item_match.append(response[item])

        if len(item_match)==0:
            raise QuestionNotFound()
        assert len(item_match)==1 # Each question should be featured once

        assert 'shown' in item_match[0].keys()
        if item_match[0]['shown'] is False:
            raise QuestionFoundButNotShown()
        else:
            return item_match[0]

        raise MCRDSException()

    @staticmethod #CHECK TRIALID + SCHEDULES EXCLUSITIVITY
    def get_schedule(schedules=None, trial_id=None, response=None, returnIsStandard=False):
        """ Returns trial schedule
            (trial_id & schedules) / response are mutually exclusive inputs!
            Input:
                schedules: SG_DATA['scheudle']
                trial_id:
                response: element of SG_DATA['scheudle']['data']
                returnIsStandard: if True, function returns whether schedule is standard
            Returns:
                schedule:
            Raises:
                InvalidCall
                ResponseNotFound:
                QuestionNotFound:
                MCRDSException: did not reach return statement
        """

        if isinstance(trial_id, str) and (response is None):
            try:
                response = SgMiner.get_response(responses=schedules, trial_id=trial_id)
            except ResponseNotFound:
                raise ResponseNotFound()
        elif (trial_id is None) and isinstance(response, dict):
            pass
        else:
            raise InvalidCall()

        try:
            question = 'Are you following the example schedule from Figure 1 of the manual?'
            query = SgMiner.get_question(response, question)
        except (QuestionNotFound, QuestionFoundButNotShown):
            raise QuestionNotFound()

        assert query['answer'] in ['Yes', 'No']

        if query['answer'] == 'Yes':
            schedule = copy.deepcopy(STANDARD_SCHEDULE)
            isStandard = True
        elif query['answer'] == 'No':
            schedule = SgMiner._extract_schedule(response)
            isStandard = False

        if returnIsStandard is False:
            return schedule
        elif returnIsStandard is True:
            return isStandard, schedule

        raise MCRDSException()

    @staticmethod
    def get_week_labels(SG_DATA, trial_id=None):
        """ Get week labels """

        week_labels = {'week1': None, 'week2': None, 'week3': None, 'week4': None}

        for i in range(1,5):
            responses = SG_DATA['blindW{}'.format(i)]

            try:
                response = SgMiner.get_response(responses, trial_id)
                question = "Please scan the QR code that is in your weekly envelope. " + \
                           "Scanning the QR will display some text and a 4 digit long numerical code, please enter the code below:"
                query = SgMiner.get_question(response, question)
            except ResponseNotFound:
                raise ResponseNotFound()
            except (QuestionNotFound, QuestionFoundButNotShown):
                raise QuestionNotFound()

            assert 'answer' in query.keys()
            blinding_code = query['answer']
            assert(isinstance(blinding_code, str))
            assert(len(blinding_code)==4)

            if blinding_code == '8415':
                week_labels['week{}'.format(i)] = 'MD1'
            elif blinding_code == '4627':
                week_labels['week{}'.format(i)] = 'MD2'
            elif blinding_code == '6132':
                week_labels['week{}'.format(i)] = 'MD3'
            elif blinding_code == '4143':
                week_labels['week{}'.format(i)] = 'MD4'
            elif blinding_code == '3666':
                week_labels['week{}'.format(i)] = 'PL'
            elif blinding_code == '9056':
                week_labels['week{}'.format(i)] = 'PL'
            elif blinding_code == '7786':
                week_labels['week{}'.format(i)] = 'PL'
            elif blinding_code == '8771':
                week_labels['week{}'.format(i)] = 'PL'
            else:
                raise UnexpectedResponse()

        return week_labels

    @staticmethod
    def get_guesses(SG_DATA, trial_id):
        """ Get participants guesses """

        guesses = copy.deepcopy(EMPTY_GUESSES)

        try:
            schedule = SgMiner.get_schedule(SG_DATA['schedule'], trial_id=trial_id)
        except (ResponseNotFound, QuestionNotFound):
            raise ResponseNotFound()

        for i in range(1,5):
            week = 'week{}'.format(i)
            responses = SG_DATA['w{}s2'.format(i)]
            guess_found = False # This is needed to assign NC/PL vs None (i.e. guess not found) cases

            try:
                response = SgMiner.get_response(responses, trial_id)
            except ResponseNotFound:
                continue

            try:
                question = "How confident are you in your judgement of whether you microdosed this week or not?"
                query    = SgMiner.get_question(response, question)
            except (QuestionNotFound, QuestionFoundButNotShown):
                pass
            else:
                guesses[week]['confidence'] = query['answer']

            try:
                question = 'Do you think this week was a microdosing week?'
                query    = SgMiner.get_question(response, question)
            except (QuestionNotFound, QuestionFoundButNotShown):
                continue
            else:
                guess_found = True

            if query['answer']=='Yes':
                guesses[week]['guess_week'] = 'microdose'
            elif query['answer']=='No (placebo week)':
                guesses[week]['guess_week'] = 'placebo'
            else:
                raise UnexpectedResponse()

            # Get daily guesses if it was MD week
            if guesses[week]['guess_week']=='microdose':

                try:
                    question = "If you think it was a microdosing week, on which days you took the microdoses?"
                    query    = SgMiner.get_question(response, question)
                except (QuestionNotFound, QuestionFoundButNotShown):
                    pass
                else:
                    guess_found = True
                    for entry in query['options']:
                        if query['options'][entry]['answer'] == 'Monday':
                            guesses[week]['guess_days']['mon']='MD'
                        elif query['options'][entry]['answer'] == 'Tuesday':
                            guesses[week]['guess_days']['tue']='MD'
                        elif query['options'][entry]['answer'] == 'Wednesday':
                            guesses[week]['guess_days']['wed']='MD'
                        elif query['options'][entry]['answer'] == 'Thursday':
                            guesses[week]['guess_days']['thu']='MD'
                        elif query['options'][entry]['answer'] == 'Friday':
                            guesses[week]['guess_days']['fri']='MD'
                        elif query['options'][entry]['answer'] == 'Saturday':
                            guesses[week]['guess_days']['sat']='MD'
                        else:
                            raise UnexpectedResponse()

            # Fill up guesses with PLs
            for day in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']:
                dayGuess = guesses[week]['guess_days'][day]
                if (dayGuess != 'MD') and (guess_found is True):
                    guesses[week]['guess_days'][day] = schedule['PL'][day]

        return guesses

    @staticmethod
    def _extract_schedule(response):
        """ Calculates schedule from the incomplete SG data """

        question = 'Your microdosing schedule (tick the days when you plan to microdose):'
        query = SgMiner.get_question(response, question)
        query = query['subquestions']

        # Mine what days were set to be MD - this is explicitly stated in the SG data
        schedule = copy.deepcopy(EMPTY_SCHEDULE)
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        weeks = ['1','2','3','4']

        # Get which weeks of which days were MD
        for subquery_id in query:
            subquery = query[subquery_id]

            for week, day in itertools.product(weeks, days):
                question = 'Microdose week {} (MD{}) : {}'.format(week, week, day)

                try:
                    sub2query = SgMiner.get_question(subquery, question)
                except QuestionNotFound:
                    continue

                if sub2query['answer'] == day:
                    day_format = day[0:3].lower()
                    schedule['MD{}'.format(week)][day_format] = 'MD'

        schedule = SgMiner._infer_schedule_from_SG(schedule)
        return schedule

    @staticmethod
    def _infer_schedule_from_SG(schedule):
        """ Calculates schedule from the incomplete SG data """

        # Infer PL week - if MD is scheduled any day, it is PL, NC otherwise
        days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']
        weeks = ['MD1','MD2','MD3','MD4']
        for week, day in itertools.product(weeks, days):
            if schedule[week][day] == 'MD':
                schedule['PL'][day] = 'PL'

        for day in days:
            if schedule['PL'][day] is None:
                schedule['PL'][day] = 'NC'

        # Infer MD weeks based on PL week schedule
        for week, day in itertools.product(weeks, days):

            if schedule[week][day] == 'MD':
                continue

            if schedule['PL'][day] == 'PL':
                schedule[week][day] = 'PL'
            elif schedule['PL'][day] == 'NC':
                schedule[week][day] = 'NC'
            else:
                raise UnexpectedResponse()

        return schedule

    @staticmethod
    def decode_blinding_code(blinding_code):
        """ Returns week label based on blinding code """

        if blinding_code == '8415':
            return 'MD1'
        elif blinding_code == '4627':
            return 'MD2'
        elif blinding_code == '6132':
            return 'MD3'
        elif blinding_code == '4143':
            return 'MD4'
        elif blinding_code == '3666':
            return 'PL'
        elif blinding_code == '9056':
            return 'PL'
        elif blinding_code == '7786':
            return 'PL'
        elif blinding_code == '8771':
            return 'PL'
        else:
            raise UnexpectedResponse(response_value=blinding_code)

        raise MCRDSException()

class TranslatorSG():
    """ Methods to translate SG data to database """

    def __init__(self, SG_DATA):
        self.SG_DATA = SG_DATA

    def translate_SG(self):
        """ Insert data from SG into DB """

        for sg_timepoint_key in self.SG_DATA.keys():
            print("Processing timepoint '{}'".format(sg_timepoint_key))

            for response_idx, response in enumerate(self.SG_DATA[sg_timepoint_key]['data']):

                try:
                    trial_id = SgMiner().get_response_sguid(response=response)
                except MissingSGUID:
                    logging.info("SGUID not found - Survey: {}; Response Idx: {}".format(
                        sg_timepoint_key,
                        response_idx))
                    continue # Get trial id

                trial_exists = TranslatorSG.check_trial_id(trial_id, response_idx, sg_timepoint_key)
                if trial_exists is False:
                    continue

                response = response['survey_data']

                if sg_timepoint_key == 'schedule':
                    TranslatorSG.process_schedule(trial_id, response, response_idx, sg_timepoint_key)
                elif 'blind' in sg_timepoint_key:
                    TranslatorSG.process_blind(trial_id, response, response_idx, sg_timepoint_key)
                else:
                    assert sg_timepoint_key in ['pre', 'w1s1', 'w2s1', 'w3s1', 'w4s1', 'w1s2', 'w2s2', 'w3s2', 'w4s2', 'post', 'ltfu']
                    TranslatorSG.process_questionnaire(trial_id, response, response_idx, sg_timepoint_key)

    @staticmethod
    @db_session
    def process_blind(trial_id, response, response_idx, sg_timepoint_key):
        """ Parse blinding from SG and add to DB """

        try:
            question = "Please scan the QR code that is in your weekly envelope. Scanning the QR will display some text and a 4 digit long numerical code, please enter the code below:"
            query = SgMiner.get_question(response, question)
        except (QuestionNotFound, QuestionFoundButNotShown):
            logging.info("Blinding question not found - Survey: {}; Response Idx: {}".format(
                sg_timepoint_key,
                response_idx))
            return # Get item

        assert 'answer' in query.keys()
        blinding_code = query['answer']
        assert(isinstance(blinding_code, str))
        assert(len(blinding_code)==4)

        try:
            week_label = SgMiner.decode_blinding_code(blinding_code)
        except UnexpectedResponse as e:
            logging.info("Unexpected blinding code - Survey: {}; Response Idx: {}; Code: {}".format(
                sg_timepoint_key,
                response_idx,
                e.response_value))
            return # Get week label

        week_idx = sg_timepoint_key[-1]
        assert week_idx in ['1', '2', '3', '4']
        week_name = 'week{}'.format(week_idx)

        #tp_name = 'w{}s2'.format(week_idx)
        #ttp=db.Trial[trial_id].ttps.select(lambda ttp: ttp.timepoint.name==tp_name).first()
        #ttp.blinding.week_label=week_label

        db.Trial[trial_id].week_labels[week_name]=week_label
        setattr(Trial[trial_id].completion, sg_timepoint_key, True)

    @staticmethod # schedule not put out
    @db_session
    def process_schedule(trial_id, response, response_idx, sg_timepoint_key):
        """ Parse schedule from SG and add to DB """

        try:
            std_schedule, schedule = SgMiner().get_schedule(response=response, returnIsStandard=True)
        except (QuestionNotFound, QuestionFoundButNotShown):
            logging.info("Schedule question not found - Survey: {}; Response Idx: {}".format(
                sg_timepoint_key,
                response_idx))
            return

        assert isinstance(std_schedule, bool)
        assert isinstance(schedule, dict)
        Trial[trial_id].std_schedule = std_schedule
        Trial[trial_id].schedule = schedule
        setattr(Trial[trial_id].completion, sg_timepoint_key, True)

    @staticmethod
    @db_session
    def process_questionnaire(trial_id, response, response_idx, sg_timepoint_key):
        """ Add questionnaire response to DB """

        setattr(Trial[trial_id].completion, sg_timepoint_key, True)

        for q_idx, question_sg in response.items():

            if (question_sg['type']=='HIDDEN') or (question_sg['shown'] is False):
                continue # DOUBLE CHECK WHETHER IT REMOVES ANYTHING

            question_text = TranslatorSG.clean_question_text(question_sg['question'])
            query = Question.select(lambda q: q.question==question_text)
            assert query.count()==1
            question_db = query.first()

            query = TrialTimepoint.select(lambda tt: tt.trial==Trial[trial_id] and tt.timepoint.name==sg_timepoint_key)
            assert query.count()==1
            ttp_db = query.first()

            if question_db.test.name == 'MISCS':
                continue

            if question_db.response_type == 'MULTICHOICE_LIST':
                assert question_sg['type'] == 'parent'
                TranslatorSG.process_mclist_response(question_sg, question_db, ttp_db)
                continue

            if question_db.response_type == 'MULTICHOICE_TABLE':
                assert question_sg['type'] == 'parent'
                TranslatorSG.process_mctable_response(trial_id, question_sg)
                continue

            assert question_db.response_type == 'NORMAL'

            try:
                answer = TranslatorSG.get_response_value(question_db, question_sg)
            except UnexpectedResponse:
                logging.info("Unexpected response - Survey: {}; response idx: {}; question idx: {}".format(
                    sg_timepoint_key,
                    response_idx,
                    q_idx))
                continue
            except KeyError:
                logging.info("'Answer' not found - Survey: {}; response idx: {}; question idx: {}".format(
                    sg_timepoint_key,
                    response_idx,
                    q_idx))
                continue # Get answer

            Response(
                question = question_db,
                value = str(answer),
                ttp=ttp_db)

    @staticmethod
    @db_session
    def process_mclist_response(question_sg, question_db, ttp_db):
        """ Add multichoice list data to DB """

        for key in question_sg['options'].keys():
            if 'other' not in question_sg['options'][key]['option'].lower():
                assert question_sg['options'][key]['answer'] == question_sg['options'][key]['option']

            answer = question_sg['options'][key]['answer']
            res = Response(
                question = question_db,
                value = str(answer),
                ttp=ttp_db)

            commit()

    @staticmethod # TRIAL.DRUG TURNED OFF HERE
    @db_session
    def process_mctable_response(trial_id, question_sg):
        """ Add multichoice table data to DB """

        question_txt = TranslatorSG.clean_question_text(question_sg['question'])

        if 'what your motives are to undergo a microdosing' in question_txt:
            Trial[trial_id].motivations = TranslatorSG.get_motivation(question_sg['subquestions'])
        elif 'how many times have you used the drugs below?' in question_txt:
            return #Trial[trial_id].drug_use = question_sg['subquestions']
        else:
            raise QuestionNotFound()

    @staticmethod
    @db_session
    def check_trial_id(trial_id, response_idx, sg_timepoint_key):
        """ Check if ID exists within db.Trial """
        try:
            Trial[trial_id]
        except ObjectNotFound:
            logging.info("SGUID found but not in DB (withdraw) - Trial: {}; Survey: {}; Response Idx: {}".format(
                trial_id,
                sg_timepoint_key,
                response_idx))
            return False
        return True

    @staticmethod
    def clean_question_text(question_txt):
        """ Removes HTML tags and leading/trailing whitespace """
        return BeautifulSoup(question_txt, "lxml").text.lstrip().rstrip()

    @staticmethod
    def get_response_value(question_db, question_sg):
        """ Converts text input to numerical where appropiate, returns answer otherwise
            Input:
                question_db: the DB question entity
                question_sg: SG_DATA[timepoint_name]['data'][response]['survey_data'][question]
        """

        answer = question_sg['answer'].lstrip().rstrip()

        if question_db.test.name in ['DEMOGRAPHICS', 'DEMS', 'WEMS', 'GCS']:
            return answer

        if question_db.test.name in ['B5', 'SCS', 'GPTS']:
            if answer == 'Strongly disagree':
                return 1
            elif answer == 'Disagree':
                return 2
            elif answer == 'Neutral':
                return 3
            elif answer == 'Agree':
                return 4
            elif answer == 'Strongly agree':
                return 5
            else:
                raise UnexpectedResponse()

        if question_db.test.name in ['RPWB', 'SWL']:
            if answer == 'Strongly disagree':
                return 1
            elif answer == 'Moderately disagree':
                return 2
            elif answer == 'Slightly disagree':
                return 3
            elif answer == 'Neutral':
                return 4
            elif answer == 'Slightly agree':
                return 5
            elif answer == 'Moderately agree':
                return 6
            elif answer == 'Strongly agree':
                return 7
            else:
                raise UnexpectedResponse()

        if question_db.test.name=='PDEES':
            if answer == 'Strongly disagree':
                return 1
            elif answer == 'Disagree':
                return 2
            elif answer == 'Neutral':
                return 3
            elif answer == 'Agree':
                return 4
            elif answer == 'Strongly agree':
                return 5
            else:
                return answer

        if question_db.test.name=='SSS':
            if answer == 'Not at all or very slightly':
                return 1
            elif answer == 'A little':
                return 2
            elif answer == 'Somewhat':
                return 3
            elif answer == 'Quite a bit':
                return 4
            elif answer == 'A lot':
                return 5
            else:
                raise UnexpectedResponse()

        if question_db.test.name=='PANAS':
            if answer == 'Not at All':
                return 1
            elif answer == 'A Little':
                return 2
            elif answer == 'Moderately':
                return 3
            elif answer == 'Quite a Bit':
                return 4
            elif answer == 'Extremely':
                return 5
            else:
                raise UnexpectedResponse()

        if question_db.test.name=='WEMWB':
            if answer == 'None of the time':
                return 1
            elif answer == 'Rarely':
                return 2
            elif answer == 'Some of the time':
                return 3
            elif answer == 'Often':
                return 4
            elif answer == 'All of the time':
                return 5
            else:
                raise UnexpectedResponse()

        if question_db.test.name=='STAIT':
            if answer == 'Not at all':
                return 1
            elif answer == 'Somewhat':
                return 2
            elif answer == 'Moderately so':
                return 3
            elif answer == 'Very much so':
                return 4
            else:
                raise UnexpectedResponse()

        if question_db.test.name=='CAMS':
            if answer == 'Rarely/Not at all':
                return 1
            elif answer == 'Sometimes':
                return 2
            elif answer == 'Often':
                return 3
            elif answer == 'Almost always':
                return 4
            else:
                raise UnexpectedResponse()

        if question_db.test.name=='QIDS':
            if answer in qids_responses[0]:
                return 0
            elif answer in qids_responses[1]:
                return 1
            elif answer in qids_responses[2]:
                return 2
            elif answer in qids_responses[3]:
                return 3
            else:
                raise UnexpectedResponse()

        raise MCRDSException()

    @db_session
    def get_accuracy_arc(self, trial_id):

        assert isinstance(trial_id, str)

        capsules_taken={'MD':0, 'PL':0, 'ALL':0}
        guessed_right={'MD':0, 'PL':0, 'ALL':0}
        guess_accuracy={'MD':None, 'PL':None, 'ALL':None}

        capsules = Trial[trial_id].capsules
        schedule = Trial[trial_id].schedule
        guesses = SgMiner.get_guesses(self.SG_DATA, trial_id)

        if schedule=={}:
            return None

        assert sorted(list(capsules.keys()))==['week1', 'week2', 'week3', 'week4']
        assert sorted(list(schedule.keys()))==['MD1', 'MD2', 'MD3', 'MD4', 'PL']

        for week_name, week_label in Trial[trial_id].week_labels.items():
            assert week_name in ['week1', 'week2', 'week3', 'week4']

            if week_label is None:
                continue
            if all([day_cap is None for day_cap in capsules[week_name].values()]):
                continue # Should not be different from the week_label=None case, but convenient fo testing
            if all([day_guess is None for day_guess in guesses[week_name]['guess_days'].values()]):
                continue

            for day, capsule in capsules[week_name].items():

                assert day in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']
                assert capsule in ['MD', 'PL', 'NC']
                assert guesses[week_name]['guess_days'][day] in ['MD', 'PL', 'NC']

                if capsule=='NC':
                    continue

                if capsule=='MD':
                    capsules_taken['MD']+=1
                    if guesses[week_name]['guess_days'][day]=='MD':
                        guessed_right['MD']+=1

                if capsule=='PL':
                    capsules_taken['PL']+=1
                    if guesses[week_name]['guess_days'][day]=='PL':
                        guessed_right['PL']+=1

        capsules_taken['ALL'] = capsules_taken['MD'] + capsules_taken['PL']
        guessed_right['ALL']  = guessed_right['MD']  + guessed_right['PL']

        if not capsules_taken['ALL']==0:
            guess_accuracy['ALL'] = round((guessed_right['ALL'] / capsules_taken['ALL'])*100,3)

        if not capsules_taken['MD']==0:
            guess_accuracy['MD'] = round((guessed_right['MD'] / capsules_taken['MD'])*100,3)

        if not capsules_taken['PL']==0:
            guess_accuracy['PL'] = round((guessed_right['PL'] / capsules_taken['PL'])*100,3)

        return guess_accuracy

    """ Functions related to mining motivation """
    @staticmethod
    def get_motivation(motivations): # CURRENTLY GETS HIGHEST MOTVATION LEVEL IN EACH CATEGORY
        assert len(motivations.keys())==16
        trial_motivation = {}

        for subquestion_key, subquestion_value in motivations.items():

            for subquestion_value_key, subquestion_value_value in subquestion_value.items():

                if subquestion_value_value['answer'] is None:
                    continue

                if isinstance(subquestion_value_value['answer'], str):
                    motivation_cat = TranslatorSG.clean_motivation_question(subquestion_value_value['question'])
                    value = TranslatorSG.get_motivation_value(subquestion_value_value['answer'])
                    trial_motivation[motivation_cat] = value

        return trial_motivation

    @staticmethod
    def get_motivation_value(answer):
        """ Get numeric motivation value """

        if answer == 'Not at all':
            return 1
        elif answer == 'Somewhat':
            return 2
        elif answer == 'Moderately':
            return 3
        elif answer == 'Very much':
            return 4
        else:
            raise UnexpectedResponse()

    @staticmethod
    def clean_motivation_question(question):
        """ 'bla bla : Somewhat' => 'bla bla' """
        idx = question.find(':')
        assert idx>0
        return question[:(idx-1)]
