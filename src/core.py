"""
:Author: Balazs Szigeti <b.islander@protonmail.com>
:Copyright: 2020, DrugNerdsLab
:License: MIT
"""

from surveygizmo import SurveyGizmo
import json
from .. import tokens
from .. import survey_keys


#def download_sg_data():
#    """ Download SG data from SG server and concatenate to single JSON """
# test

client = SurveyGizmo(api_version='v5',
                     response_type='json',
                     api_token = tokens.api_key,
                     api_token_secret = tokens.secret_key)

client.config.base_url = 'https://restapi.surveygizmo.eu/'

for study, surveys in survey_keys.studies.items():
    for survey in surveys:

        if survey['remind'] is False:
            #continue
            pass

        id = survey['id']

        temp = client.api.surveyresponse.resultsperpage(value=100000).list(id)
        assert isinstance(temp, str)

        sg = json.loads(temp)

        assert sg['total_pages']==1
        import pdb; pdb.set_trace()
