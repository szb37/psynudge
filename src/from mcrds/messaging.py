# Make sure gecko exe is on path for protonmail to work!
# export PATH=$PATH:/home/bazsi/Desktop/gecko/

from mcrds.src.globals import BASE_DIR
from mcrds.src import ps
from mcrds import controllers
from time import sleep
import protonmail
import os

client = protonmail.core.ProtonmailClient()
client.login("microdose-study@protonmail.com", "AcidForLife0309")

def send_reports():
    reports_dir = os.path.join(BASE_DIR, 'reports/')
    #emails = utilities.getEmailsFromReportFilename(reports_dir)
    emails = ['b.szigeti@protonmail.com']

    for email in emails:

        report_file = utilities.matchReportToEmail(dir=reports_dir, email=email)

        assert isinstance(report_file, str)
        assert isinstance(email, str)
        assert '@' in email

        message = 'Hello, \n\
    \
    Please find your report from the self-blinding microdose study attached. \
    The file that you receive is a plain text file, probably best viewed with Chrome / Firefox.\n\
    \
    As it is outlined in the study manual, we only share guessing and cognitive performance scores, but not psychological assessments. \n\
    \
    If you would like to further help the project, please spread the word about the project on social media and microdosing related forums.\n\
    The best advertisement for us is by the word of mouth, so it is much appreciated if you share your experiences about the study with others who could be interested!\n\
    \n\
    One last time, we would like to thank you for participating. \
    We know completing this study required effort and dedication, with your help we will be able to expand psychedelics science!'

        logging.info('Sending email to {}'.format(email))
        client.send_mail([email], 'Missing data', message, attachments=[report_file])
        sleep(3)

def send_finished_QRmiss():

    db  = controllers.buildDB()
    weekDict = utilities.getFinishedQRmiss(db)
    userDict = utilities.convertWeek2UserDict(weekDict)
    #userDict = {'szbazsu@gmail.com': [1], 'b.szigeti@protonmail.com': [1, 2, 3, 4]}

    for email in userDict.keys():

        assert isinstance(email, str)
        assert '@' in email

        message = 'Hello, \n\
    \n\
    During data analysis we noticed that your weekly QR codes are missing for week(s): {}. \
    The weekly QR codes (4 digits long numbers) are obtained when scanning the QR codes from the envelopes.\n\
    \n\
    We need these codes to process your data. Do you have the codes somewhere, maybe on the provided experience tracking sheet? \
    Most QR readers have a history feature, so you could recover the QR codes from there as well. Please send us the codes \
    if you find them and then we will update our database.\n\
    \n\
    If you need further information, please do not hesitate to get in touch, we are committed to support our participants.\n\
    \n\
    ps.: there is a small chance that you have received this request earlier, if you have already responded, \
    please ignore this email'.format(str(userDict[email]).replace('[', '').replace( ']', ''))

        logging.info('Sending email to {}'.format(email))
        client.send_mail([email], 'Missing data', message)
        sleep(3)

def send_ongoing_QRmiss():
    """ Message ONGOING participants missing QR codes """

    db  = controllers.buildDB()
    weekDict = utilities.getOngoingQRmiss(db)
    userDict = utilities.convertWeek2UserDict(weekDict)
    #userDict = {'szbazsu@gmail.com': [1], 'b.szigeti@protonmail.com': [1, 2, 3, 4]}

    for email in userDict.keys():

        assert isinstance(email, str)
        assert '@' in email

        message = 'Hello, \n\
    \n\
    During data analysis we noticed that your weekly QR codes are missing for week(s): {}. \
    The weekly QR codes (4 digits long numbers) are obtained when scanning the QR codes from the envelopes.\n\
    \n\
    We need these codes to process your data. Do you have the codes somewhere, maybe on the provided experience tracking sheet? \
    Most QR readers have a history feature, so you could recover the QR codes from there as well. Please send us the codes \
    if you find them and then we will update our database.\n\
    \n\
    If you need further information, please do not hesitate to get in touch, we are committed to support our participants.\
    '.format(str(userDict[email]).replace('[', '').replace( ']', ''))

    logging.info('Sending email to {}'.format(email))
    client.send_mail([email], 'Missing data', message)
    sleep(3)





def send_nonCompliants():
    """ Message NON COMPLIANT participants """
    #emails = ['b.szigeti@protonmail.com', 'b.szigeti@pm.me', 'szbazsu@gmail.com', 'b.islander@protonmail.com', 'b.islander@pm.me']



from time import sleep
import protonmail
import os
import mcrds
import pickle

client = protonmail.core.ProtonmailClient()
client.login("microdose-study@protonmail.com", "AcidForLife0309")

message = '<p><span style="font-weight: 400;">Hello,</span></p>\
<p><span style="font-weight: 400;">You have signed up for the self-blinding microdose study, but according to our records you have not started the experiment. If you are still interested, we ask you to read carefully the </span><a href="https://selfblinding-microdose.org/sign-up.html"><span style="font-weight: 400;">participant information sheet</span></a><span style="font-weight: 400;">, so you know what the study requires. </span></p>\
<p><span style="font-weight: 400;">Since launching the study, we have made a number of amendments to make it easier to participate. These include:</span></p>\
<ul>\
<li style="font-weight: 400;"><span style="font-weight: 400;">a </span><a href="https://www.youtube.com/watch?v=crd3EMUM7DM"><span style="font-weight: 400;">video guide</span></a><span style="font-weight: 400;"> how to setup the study</span></li>\
<li style="font-weight: 400;"><span style="font-weight: 400;">the manual now includes Amazon links for the accessories needed </span></li>\
<li style="font-weight: 400;"><span style="font-weight: 400;">support for participating with </span><a href="https://selfblinding-microdose.org/study_manual.html"><span style="font-weight: 400;">magic mushrooms</span></a></li>\
<li style="font-weight: 400;"><span style="font-weight: 400;">support for participating with </span><a href="https://selfblinding-microdose.org/study_manual.html"><span style="font-weight: 400;">volumetric dosing</span></a></li>\
</ul>\
<p><span style="font-weight: 400;">The </span><strong>last valid starting date for the study is 31st of October</strong><span style="font-weight: 400;">, please plan your participation accordingly. Thank you for your help again to push forward the boundaries of psychedelics science!</span></p>'

sent_already = pickle.load(open('sent_already.pic', 'rb'))
db = mcrds.controllers.buildDB()
absents = db.filterTrials(
              completion = mcrds.datastructures.Completion.absent,
              stage = mcrds.datastructures.Stage.finished,
              )

emails=[]
for id, trial in absents.items():
    if trial.email not in sent_already:
        emails.append(trial.email)

for email in emails[0:40]:

    assert isinstance(email, str)
    assert '@' in email
    logging.info('Sending email to {}'.format(email))
    client.send_mail(to=[email], subject='Study update', message=message, as_html=True)
    sent_already.append(email)
    sleep(3)

pickle.dump(sent_already, open('sent_already.pic', 'wb'))
