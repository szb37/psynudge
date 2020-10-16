"""
:Author: Balazs Szigeti <b.islander@protonmail.com>
:Copyright: 2020, DrugNerdsLab
:License: MIT
"""

from surveygizmo import SurveyGizmo
from psynudge import tokens

client = SurveyGizmo(api_version='v5',
                     response_type='json',
                     api_token = tokens.api_key,
                     api_token_secret = tokens.secret_key)

id = 90076350

with open('ceremony.json', 'w') as outfile:
    json.dump(sg, outfile)



item_match=[]
question='email'
question_in_bold='EMAIL'

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



 dateutil.parser.parse('2020-01-10T00:00:00Z')
