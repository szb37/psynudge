""" Survey data exploration """
def isCompleted(userId, surveyData, firstQID=None, lastQID=None): # Tested
    """ Checks whether user has entry in surveyData """

    assert isinstance(userId, str)
    assert isinstance(surveyData, list)
    assert isinstance(firstQID, int)
    assert isinstance(lastQID, int)

    responseFound = False
    for response in surveyData:
        sguid=getResponseSguid(response)
        if sguid==userId:
            responseFound = True
            break

    if responseFound is False:
        return False # Response with SGUID not found

    isStarted  = 'answer' in response['survey_data'][str(firstQID)].keys() # answer key exists iff answer was given
    isFinished = 'answer' in response['survey_data'][str(lastQID)].keys()

    if (isStarted is False) and (isFinished is False):
        return False
    if (isStarted is True) and (isFinished is False):
        return False
    if (isStarted is False) and (isFinished is True):
        assert False
    if (isStarted is True) and (isFinished is True):
        return True

    assert False

def getResponseSguid(response):
    """ Returns SGUID of a response. The SGUID can be recorded either as hidden or URL variable, code checks both """

    sguid_url    = None
    sguid_hidden = None

    for key, value in response['survey_data'].items():
        if value['question']=='Capture SGUID':
            if value['shown'] is True:
                sguid_hidden = value['answer']

    try:
        sguid_url = response['url_variables']['sguid']['value']
    except:
        pass

    if isinstance(sguid_url, str) and isinstance(sguid_hidden, str):
        assert(sguid_url==sguid_hidden)
        return sguid_url
    elif isinstance(sguid_url, str) and sguid_hidden is None:
        return sguid_url
    elif sguid_url is None and isinstance(sguid_hidden, str):
        return sguid_hidden
    elif sguid_url is None and sguid_hidden is None:
        assert False


"""  Disk data manipulations """
def loadStudyData(study): # WIP

    psData = get_ps_data(study)
    getData(study=study, lastSgCheck=None)
    surveyData = read_sg_data()

    return psData, surveyData

def appendData(file_path, data): # Tested

    assert isinstance(data, list)

    with open(file_path, 'r') as file:
        file_data = json.load(file)
        assert isinstance(file_data, list)

    for element in data:
        file_data.append(element)

    with open(file_path, 'w+') as file:
        json.dump(file_data, file)

def writelastSgCheckTime(base_dir=base_dir): # Tested
    """ Updates last_time_checked.txt, which contains the isostring datetime for the last time the nuddger was run (in UTC) """

    now = getUtcNow()
    file_path = os.path.join(base_dir, 'last_time_checked.txt')
    with open(file_path, 'w+') as file:
        file.write(now.isoformat())

def readlastSgCheckTime(base_dir=base_dir): # Tested
    """ Reads and returns last_time_checked.txt, which contains the isostring datetime for the last time the nuddger was run (in UTC) """

    file_path = os.path.join(base_dir, 'last_time_checked.txt')
    with open(file_path, 'r') as file:
        now_str = file.readline()
    assert len(now_str)==25
    return now_str


# is this ever used?
def isCompleted(db, userId, tp):
    """ Checks if tp has been completed by participant already """

    completions=db.Completion.select(lambda c:
        c.participant.psId==userId and
        c.timepoint == tp).fetch()

    assert len(completions)==1
    completion = completions[0]

    return completion.isComplete
