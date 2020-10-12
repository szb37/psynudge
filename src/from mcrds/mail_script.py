#export PATH=$PATH:/home/bazsi/Desktop/gecko/

import protonmail
from time import sleep

client = protonmail.core.ProtonmailClient()
client.login("microdose-study@protonmail.com", "AcidForLife0309")

toSend=[
'szbazsu@gmail.com',
'blblb'
]

message = \
'This message is a test of the \n\
breaking up lines in the email.'

for address in toSend:

    logging.info('Sending email to {}'.format(address))
    client.send_mail([address], 'Updates v4', message)
    sleep(5)

client.destroy()
