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
