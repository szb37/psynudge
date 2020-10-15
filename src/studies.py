"""
:Author: Balazs Szigeti <b.islander@protonmail.com>
:Copyright: 2020, DrugNerdsLab
:License: MIT
"""

import datetime
import collections

Timepoint = collections.namedtuple('Timepoint', 'name, id, td2tp, td2nudge, remind')
# td2tp: the datetime.deltatime from start (as entered to PS) to the end of tp, i.e. start + td2tp = end of TP
# td2nudge: the datetime.deltatime from start (as entered to PS) to the end of the nudge period, i.e. start + td2tp = end of TP

studies={
    'mock':[
        Timepoint('pre',  0, datetime.timedelta(days=-7), datetime.timedelta(days=-6), True),
        Timepoint('w1',   1, datetime.timedelta(days= 7), datetime.timedelta(days= 8), True),
        Timepoint('w2',   2, datetime.timedelta(days=14), datetime.timedelta(days=15), True),
        Timepoint('post', 3, datetime.timedelta(days=21), datetime.timedelta(days=22), True),
        Timepoint('ltfu', 4, datetime.timedelta(days=28), datetime.timedelta(days=30), True),
        ],

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

}
