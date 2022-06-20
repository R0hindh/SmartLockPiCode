import firebase_admin
import RPi.GPIO as GPIO
from firebase_admin import credentials
from firebase_admin import db
from time import sleep 

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
channel = 15
GPIO.setup(channel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


cred = credentials.Certificate("smartlock-project-firebase-adminsdk.json")
firebase_admin.initialize_app(cred, {'databaseURL': 'https://smartlock-project-default-rtdb.firebaseio.com/'})

def lockSwitch(status):
    if status:
        print("LOCKED")
    else:
        print("UNLOCKED")

def listener(event):
    print(event.data)
    lockSwitch(event.data)
    file = open(r"LockStatus.txt","w+")
    file.write(str(event.data))
    file.close()

def unlockFromInside():
    db.reference("Users/qWkZp1WoXMWfvxLDjFPBRl7wA1F2/lockStatus").set(False)
    sleep(5)
    db.reference("Users/qWkZp1WoXMWfvxLDjFPBRl7wA1F2/lockStatus").set(True)

db.reference("Users/qWkZp1WoXMWfvxLDjFPBRl7wA1F2/lockStatus").listen(listener)

while True:
    if GPIO.input(channel) == GPIO.HIGH:
        print("Button pressed")
        unlockFromInside()
        sleep(2)
