#!/usr/bin/python
import smtplib
from email.mime.text import MIMEText
import json
import sys
import hashlib
filelist='/changelog.json'
SEEDTIMER=12887388299187726

# This is the send mail function
# it takes 3 strings: destination address, subject, and text as input
# Fill here your email account details i use the same server.
def send_mail(to_address, subject, text):
    from_address = 'sender@yourdomain.tld'
    msg = MIMEText(text)
    msg['subject'] = subject
    msg['From'] = from_address
    msg['To'] = to_address

    s = smtplib.SMTP('localhost:587')
    s.ehlo()
    s.starttls()
    s.login('sender@yourdomain.tld', 'your_email_password')
    s.sendmail(from_address, to_address, msg.as_string())
    s.quit

def createDicHash(pathbase):
    pathlog=pathbase+filelist
    fileDict={}

    with open(pathlog, 'w') as fh:
            for path, subdirs, files in os.walk(userpath):
                for name in files:
                    print(name)
                    filepath = os.path.join(path, name)

                    #Hashing using sha algoritm
                    sha = hashlib.sha1(filepath.encode('utf-8'))
                    hashkey=sha.hexdigest()
                    #hashkey= hash(filepath) % ((SEEDTIMER+ 1) * 2)

                    statinfo = os.stat(filepath)

                    fileDict.update({ hashkey :
                        {'hashkey':hashkey,
                        'filename': filepath,
                         'modify': time.ctime(os.path.getmtime(filepath)),
                         'size':statinfo.st_size}
                             })
                                 #memorizza i dati in un dizionario utilizzando l'hash del percorso del file

                    #print(fileDict) #dizionario stampato

            fh.write(json.dumps(fileDict))


def loadLog(pathbase):
    path = pathbase+filelist
    exists = os.path.isfile(path)
    fileDict={}

    if exists:
        #apre il file legge i dati e li carica in un dizionario
        with open(path, 'r') as json_file:
            fileDict=json.load(json_file)
            #print(fileDict)
            return fileDict

    else:
        #crea un file di changelog nella directory principale
        createDicHash(pathbase)

def isChangedFile(dic, filepath):
    # Hashing using sha algoritm
    sha = hashlib.sha1(filepath.encode('utf-8'))
    hashkey = sha.hexdigest()
    # hashkey= hash(filepath) % ((SEEDTIMER+ 1) * 2)


    modify=time.ctime(os.path.getmtime(filepath))
    statinfo = os.stat(filepath)
    size=statinfo.st_size

    if hashkey in dic:
        if dic[hashkey]['modify']== modify:
            return False
        else:
            return True
    else:
        return True

def addtofile(message, filename):
    # crea il file se non presente e accoda il testo se il file esiste
    filestream = open(filename, 'a+')
    filestream.write(message)


import os
import subprocess
import re
import string
import os.path, time

# this list used to exclude files that starts with this string
# keep in mind that you place here the path after /home/user/public_html
# for example if you want to exclude /home/user/public_html/wp-content/cache you just write '/wp-content/cache'
excluded_paths = ['/wp-content/cache',
                  '/wp-content/plugins/si-contact-form/captcha/cache',
                  '/magento/var/cache',
                  '/assets/cache',
                  ]


# It takes the output of find command in one string,
def check_lines(output, userpath):
    output=str(output)
    #print(output)

    new_output = ""
    # split the output string to check line by line
    lines = output.split('\n')
    for line in lines:
        exclude_it = False
        # here is where the exclusion list filter works
        #
        for ex_path in excluded_paths:
            if (re.match(userpath + ex_path, line) != None):
                exclude_it = True
                break
        # filter out files ends with error_log
        if (re.match(r'(.*error_log$)', line) != None):
            exclude_it = True
        if (exclude_it == False) and (line != ''):
            new_output += line + '\n'
    return new_output

root="var/cpanel/users/"
user_list = os.listdir(root)
# user_list = os.listdir("/var/cpanel/users/")

#print(user_list)

message = ""
fileslist=[]

for user in user_list:
    #userpath = "/home/" + user + "/public_html"

    userpath = root+user+"/home/" + user + "/public_html"
    logfile=loadLog(userpath)

    # here is the find command, -182 is how many minutes back
    # i choose to see changes every 3 hours, i run this script every 3 hours on my server thats why i have 182
    p = subprocess.Popen(["find", userpath, "-name", "*", "-mmin", "-182", "-print"], stdout=subprocess.PIPE)
    output, err = p.communicate()

    #print(output)

    lastFileVersion=loadLog(userpath)

    if (output != ""):
        processed_output = check_lines(output, userpath)
        if (processed_output != ''):
            message += "username: " + user + '\n'
            #message += processed_output + '\n'
            print(userpath)

            for path, subdirs, files in os.walk(userpath):
                for name in files:
                    print(name)
                    filepath=os.path.join(path, name)
                    fileslist.append(filepath)
                    if isChangedFile(lastFileVersion,filepath):
                        message += "----***--- MODIFICATO --- : "+time.ctime(os.path.getmtime(filepath)) +" - "+filepath+ '\n'

    #print(fileslist)

    #ricrea il file dello storico delle modifiche
    createDicHash( userpath)

addtofile(message, "CHANGELOG-%s" % user)

# where to send the email and what subject
# send_mail('recipient@yourdomain.tld', 'File changes', message)
