"""
:Author: Balazs Szigeti <b.islander@protonmail.com>
:Copyright: 2020, DrugNerdsLab
:License: MIT

'ceremony2':[
    {'tp':None, 'id':'90203577', 'name':'Beads task R/B 1', 'remind':False},
    {'tp':None, 'id':'90203575', 'name':'Beads task P/Y 1', 'remind':False},
    {'tp':None, 'id':'90176399', 'name':'Ceremony Study 2.0', 'remind':False},
    {'tp':None, 'id':'90170989', 'name':'Test pre-post Survey', 'remind':False},
    {'tp':'endpoint1', 'id':'90159708', 'name':'CStudy 2.0: Endpoint I (1 week)', 'remind':True},
    {'tp':'pre' , 'id':'90159703', 'name':'CStudy 2.0: Pre-ceremony', 'remind':True},
    {'tp':'post' , 'id':'90159702', 'name':'CStudy 2.0: Post-ceremony 1', 'remind':True},
    {'tp':'baseline', 'id':'90159701', 'name':'CStudy 2.0: Baseline', 'remind':True},
    ],

"""

https://survey.alchemer.eu/s3/90286853/Piping2?sguid=011&name=tester&__sgtarget=1

#Response A
https://survey.alchemer.eu/s3/90286853/Piping2?sguid=012&name=tester&__sgtarget=1
https://survey.alchemer.eu/s3/90286853/Piping2?sguid=012&name=tester&__sgtarget=5

#Response B
https://survey.alchemer.eu/s3/90286853/Piping2?sguid=013&name=tester&__sgtarget=1
https://survey.alchemer.eu/s3/90286853/Piping2?sguid=013&name=tester&__sgtarget=5


""" DOWNLAOD DATA OF GIVEN SURVEY """
from surveygizmo import SurveyGizmo
from psynudge import tokens
import json

client = SurveyGizmo(api_version='v5',
                     response_type='json',
                     api_token = tokens.api_key,
                     api_token_secret = tokens.secret_key)

client.config.base_url = 'https://restapi.surveygizmo.eu/'

id = 90288073

temp = client.api.surveyresponse.resultsperpage(value=100000).list(id)
assert isinstance(temp, str)
data = json.loads(temp)

with open('test_data.json', 'w+') as outfile:
    json.dump(data, outfile)

""" filter sponses """
client.api.surveyresponse.filter(field='date_submitted', operator='<', value='2020-10-27 14:14:32 GMT').resultsperpage(value=100000).list(id)

https://restapi.alchemer.com/v5/survey/123456/surveyresponse?filter[field][0]=

date_submitted&filter[operator][0]=>=&filter[value][0]=2011-02-23+13:23:28

date_submitted>'2011-02-23+13:23:28'


""" load test data """
import json
file_path='/media/sf_vm_share/psynudge/tests/fixtures/stacked_test_stacked.json'
with open(file_path, 'r') as file:
        file_data = json.load(file)
