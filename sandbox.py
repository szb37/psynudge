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
import psynudge
db = psynudge.db.build_empty_db()
psynudge.controllers.updatePsData2Db(db=db)

https://survey.alchemer.eu/s3/90288073/indep-tp1
https://survey.alchemer.eu/s3/90289410/indep-tp2
https://survey.alchemer.eu/s3/90286853/stacked

#Read in JSON
import dateutil.parser
import json

file_path='/media/sf_vm_share/psynudge/tests/fixtures/indep_tp1.json'
with open(file_path, 'r') as f:
    data = json.loads(f.read())

for entry in data['data']:
    print(
        dateutil.parser.parse(entry['date_submitted']).isoformat()
    )

import psynudge
db = psynudge.controllers.build_db(filepath=':memory:')

db.Study.select(lambda s: s.name=='indep_study').first().participants.select().count()


psynudge.core.getPsData(study=db.Study.select(lambda s: s.name=='indep_study').first())

#2020-11-06T10:58:09+00:00
#2020-11-06T11:02:18+00:00
#2020-11-06T11:04:22+00:00
#2020-11-06T11:05:14+00:00







https://survey.alchemer.eu/s3/90286853/Piping2?sguid=011&name=tester&__sgtarget=1

#Response A
https://survey.alchemer.eu/s3/90286853/Piping2?sguid=012&name=tester&__sgtarget=1
https://survey.alchemer.eu/s3/90286853/Piping2?sguid=012&name=tester&__sgtarget=5

#Response B
https://survey.alchemer.eu/s3/90286853/Piping2?sguid=013&name=tester&__sgtarget=1
https://survey.alchemer.eu/s3/90286853/Piping2?sguid=013&name=tester&__sgtarget=5


""" DOWNLAOD DATA OF GIVEN SURVEY """
#indep tp1: 90288073
#indep tp2: 90289410
#stack: 90286853

from surveygizmo import SurveyGizmo
from psynudge.src import tokens
import json

client = SurveyGizmo(api_version='v5',
                     response_type='json',
                     api_token = tokens.sg_key,
                     api_token_secret = tokens.secret_key)

client.config.base_url = 'https://restapi.surveygizmo.eu/'

id = 90286853

temp = client.api.surveyresponse.resultsperpage(value=100000).list(id)
assert isinstance(temp, str)
data = json.loads(temp)

with open('stack_data.json', 'w+') as outfile:
    json.dump(data, outfile)







def filterSgResponses():
    client.api.surveyresponse.filter(field='date_submitted', operator='<', value='2020-10-27 14:14:32 GMT').resultsperpage(value=100000).list(id)
    https://restapi.alchemer.com/v5/survey/123456/surveyresponse?filter[field][0]=
    date_submitted&filter[operator][0]=>=&filter[value][0]=2011-02-23+13:23:28
    date_submitted>'2011-02-23+13:23:28'

def createdb():
    from pony.orm import *
    import datetime
    import os

    db = Database()
    filepath=os.path.join('/media/sf_vm_share', 'test.sqlite')

    class Timepoint(db.Entity):
        id = PrimaryKey(int, auto=True)
        td2start = Required(datetime.timedelta) # td2start: datetime.deltatime from user['date'] to start of TP, i.e. user['date'] + td2start = start of TP

    db.bind(provider='sqlite', filename=filepath, create_db=True)
    db.generate_mapping(create_tables=True)

    Timepoint(td2start = datetime.timedelta(hours=6))
    db.commit()
    db.flush()
    db.disconnect()

def connect_db():
    from pony.orm import *
    import datetime
    import os
    db = Database()

    class Timepoint(db.Entity):
        id = PrimaryKey(int, auto=True)
        td2start = Required(datetime.timedelta) # td2start: datetime.deltatime from user['date'] to start of TP, i.e. user['date'] + td2start = start of TP

    filepath=os.path.join('/media/sf_vm_share', 'test.sqlite')
    db.bind(provider='sqlite', filename=filepath, create_db=False)
    db.generate_mapping(create_tables=True)


        file_path = getDataFileName(study, tp)

        # Either save new file or append to existing file
        if os.path.isfile(file_path) is True:
            appendData(file_path, sg_data['data'])

        if os.path.isfile(file_path) is False:
            with open(file_path, 'w+') as file:
                json.dump(sg_data['data'], file)

        # no need to iterate over tps with stack studies
        if study.type=='stack':
            return
