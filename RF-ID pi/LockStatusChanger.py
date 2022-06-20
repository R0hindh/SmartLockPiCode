import firebase_admin
import RPi.GPIO as GPIO
from firebase_admin import credentials
from firebase_admin import db
from time import sleep

channel = 17
SwtichChannel = 15
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
#GPIO.setup(channel, GPIO.OUT)
#GPIO.setup(SwtichChannel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
cred = credentials.Certificate("smartlock-project-firebase-adminsdk.json")
firebase_admin.initialize_app(cred, {'databaseURL': 'https://smartlock-project-default-rtdb.firebaseio.com/'})

def lock():
    GPIO.setup(channel, GPIO.OUT)
    GPIO.output(channel, GPIO.HIGH)  # Turn on

def unlock():
    GPIO.setup(channel, GPIO.OUT)
    GPIO.output(channel, GPIO.LOW)  # Turn off
    #GPIO.cleanup(channel)

def lockSwitch(status):
    global recentCall
    recentCall = True
    if status:
        print("LOCKED")
        unlock()
    else:
        print("UNLOCKED")
        lock()

def listener(event):
    print(event.data)
    lockSwitch(event.data)
    file = open(r"LockStatus.txt","w+")
    file.write(str(event.data))
    file.close()

db.reference("Users/qWkZp1WoXMWfvxLDjFPBRl7wA1F2/lockStatus").listen(listener)
