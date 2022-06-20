from time import sleep
import sys
from mfrc522 import SimpleMFRC522
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import RPi.GPIO as GPIO
import datetime

GPIO.setwarnings(False)
cred = credentials.Certificate("smartlock-project-firebase-adminsdk.json")
firebase_admin.initialize_app(cred, {'databaseURL': 'https://smartlock-project-default-rtdb.firebaseio.com/'})
logLength = 0

def logListener(event):
    global logLength
    if type(event.data) is dict:
        if (len(event.data) == 5 and 'index' in event.data):
            logLength = logLength + 1
        else:
            logLength = len(event.data)

db.reference("Users/qWkZp1WoXMWfvxLDjFPBRl7wA1F2/Log").listen(logListener)

def getLockStatus():
    file = open("LockStatus.txt","r")
    temp = file.read()
    file.close()

    if temp == 'True':
        return True
    else:
        return False
status = getLockStatus()

reader = SimpleMFRC522()

try:
    while True:
        print("Hold a tag near the reader")
        id, text = reader.read()
        print("ID: %s\nText: %s" % (id,text))
        currentDate = datetime.datetime.now()
        fDate = currentDate.strftime("%a")+" "+currentDate.strftime("%b")+" "+currentDate.strftime("%d")+" "+currentDate.strftime("%Y")
        fTime = currentDate.strftime("%I")+":"+currentDate.strftime("%M")+" "+currentDate.strftime("%p")
        print("Time" + str(fTime))
        if 459913888891 == id:
            if getLockStatus():
                print("ACCESS GRANTED!!!!")
                db.reference("Users/qWkZp1WoXMWfvxLDjFPBRl7wA1F2/lockStatus").set(False)
                db.reference("Users/qWkZp1WoXMWfvxLDjFPBRl7wA1F2/Log").push().set({
                    'date':fDate,
                    'lockStatus':"Unlocked" if status else "Locked",
                    'method':"RF-ID",
                    'time':fTime,
                    'index':logLength+1
                })
                sleep(5)
                db.reference("Users/qWkZp1WoXMWfvxLDjFPBRl7wA1F2/lockStatus").set(True)
            else:
                sleep(2)
                continue
        else:
            db.reference("Users/qWkZp1WoXMWfvxLDjFPBRl7wA1F2/Log").push().set({
                'date':fDate,
                'lockStatus':"Failed",
                'method':"RF-ID",
                'time':fTime,
                'index':logLength+1
            })
            print("ACCESS DENIED!!!!")
        sleep(2)
except KeyboardInterrupt:
    GPIO.cleanup()
    raise
