import sys
import time
import RPi_I2C_driver

import firebase_admin
import RPi.GPIO as GPIO
from firebase_admin import credentials
from firebase_admin import db
import json
from datetime import datetime

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

cred = credentials.Certificate("smartlock-project-firebase-adminsdk.json")
firebase_admin.initialize_app(cred, {'databaseURL': 'https://smartlock-project-default-rtdb.firebaseio.com/'})
var=None
logLength = 0

def logListener(event):
    if(event.data):
        global logLength
        if type(event.data) is dict:
            if (len(event.data) == 5 and 'index' in event.data):
                logLength = logLength + 1
            else:
                logLength = len(event.data)

def OTPlistener(event):
    global var
    print("OTP updated")
    data = db.reference("Users/qWkZp1WoXMWfvxLDjFPBRl7wA1F2/OTP").get()
    var = json.loads(json.dumps(data))
    print("DATA", var)

#db.reference("Users/qWkZp1WoXMWfvxLDjFPBRl7wA1F2/Log").listen(logListener)       
#db.reference("Users/qWkZp1WoXMWfvxLDjFPBRl7wA1F2/OTP").listen(OTPlistener)

def getLockStatus():
    file = open("LockStatus.txt","r")
    temp = file.read()
    file.close()
    if temp == 'True':
        return True
    else:
        return False
    

def lockWhenTimeOut(seconds):
    time.sleep(seconds)
    print("time out after "+str(seconds))
    db.reference("Users/qWkZp1WoXMWfvxLDjFPBRl7wA1F2/lockStatus").set(True)

status = getLockStatus()
def triggerAPI(success, status, method):
    currentDate = datetime.now()
    fDate = currentDate.strftime("%a")+" "+currentDate.strftime("%b")+" "+currentDate.strftime("%d")+" "+currentDate.strftime("%Y")
    fTime = currentDate.strftime("%I")+":"+currentDate.strftime("%M")+" "+currentDate.strftime("%p")
    print(fDate)
    print(fTime)
    obj = {}  
    if(success):
        db.reference("Users/qWkZp1WoXMWfvxLDjFPBRl7wA1F2/lockStatus").set(False)
        show_message("Welcome")
        obj = {
            'date':fDate,
            'lockStatus':"Unlocked",
            'method':method,
            'time':fTime,
            'index':logLength+1
            }
        db.reference("Users/qWkZp1WoXMWfvxLDjFPBRl7wA1F2/Log").push().set(obj)
        lockWhenTimeOut(5)
    else:
        obj = {
            'date':fDate,
            'lockStatus':"Failed",
            'method':method,
            'time':fTime,
            'index':logLength+1
            }
        db.reference("Users/qWkZp1WoXMWfvxLDjFPBRl7wA1F2/Log").push().set(obj)    
        
admin_pin=db.reference("Users/qWkZp1WoXMWfvxLDjFPBRl7wA1F2/adminPin").get()
print(admin_pin)

def checkOTP(user_otp):
    global var
    global admin_pin
    if user_otp==admin_pin:
        return "Admin Pin",1
    print("CheckOTP", type(var))
    for i in var:
        print()
        print(i)
        print(var[i])
        print()
        if var[i]["OTPPin"]==user_otp:
            start_date_time=var[i]["start"]["Date"]+" "+var[i]["start"]["Time"]
            end_date_time=var[i]["expired"]["Date"]+" "+var[i]["expired"]["Time"]
            start_date_time = start_date_time.replace("2022","22")
            end_date_time = end_date_time.replace("2022","22")
            date_time_obj_s = datetime.strptime(start_date_time, '%d/%m/%y %H:%M')
            date_time_obj_e = datetime.strptime(end_date_time, '%d/%m/%y %H:%M')
            #current_date_time=datetime.now()
            if (datetime.now()>=date_time_obj_s) and (datetime.now()<=date_time_obj_e):
                return "OTP",1
    return "Admin Pin/OTP",0

mylcd = RPi_I2C_driver.lcd()
mylcd.backlight(0)
mylcd.lcd_clear()
col_list=[6,13,19,26]
row_list=[16,5,20,21]
GPIO.setmode(GPIO.BCM)
for pin in row_list:
  GPIO.setup(pin,GPIO.OUT)
  GPIO.output(pin, GPIO.HIGH)

for pin in col_list:
  GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
key_map=[["1","2","3","A"],\
        ["4","5","6","B"],\
        ["7","8","9","C"],\
        ["*","0","#","D"]]
def Keypad4x4Read(cols,rows):
    for r in rows:
        GPIO.output(r, GPIO.LOW)
        result=[GPIO.input(cols[0]),GPIO.input(cols[1]),GPIO.input(cols[2]),GPIO.input(cols[3])]

        if min(result)==0:
            key=key_map[int(rows.index(r))][int(result.index(0))]
            GPIO.output(r, GPIO.HIGH) # manages key keept pressed
            return(key)
        GPIO.output(r, GPIO.HIGH)
def show_message(m):
    message=m
    mylcd.lcd_display_string(message,1)
    time.sleep(2)
    message=""
    mylcd.lcd_clear()
    
user_password=""
message = ""
db.reference("Users/qWkZp1WoXMWfvxLDjFPBRl7wA1F2/Log").listen(logListener)       
db.reference("Users/qWkZp1WoXMWfvxLDjFPBRl7wA1F2/OTP").listen(OTPlistener)

while True:
    mylcd.lcd_display_string("Enter OTP/PIN", 1)
    try:
        key=Keypad4x4Read(col_list, row_list)
        
        if key:
            char= chr(ord(key))
            print("Char:",char)
            if char != None:
                if char=='A': #enter button
                    if len(user_password)==6:
                        mylcd.lcd_clear()
                        method,check=checkOTP(user_password)
                        if check==1:
                            show_message("Verified")
                            triggerAPI(True,status,method)
                            time.sleep(0.01)
                            user_password=""
                            continue
                        else:
                            triggerAPI(False,status,method)
                            show_message("Wrong Pin")
                            user_password=""
                            continue
                    else:
                        mylcd.lcd_clear()
                        show_message("Invalid Pin")
                        user_password=""
                        continue
                elif char=='C': #clear entire screen
                    user_password=""
                    mylcd.lcd_clear()
                    mylcd.lcd_display_string("Enter OTP/PIN", 1)
                    time.sleep(0.02)
                elif char=='D': #backspace button
                    user_password=user_password[:-1]
                    mylcd.lcd_clear()
                    mylcd.lcd_display_string("Enter OTP/PIN", 1)
                    mylcd.lcd_display_string(user_password,2)
                    time.sleep(0.02)
                    
                else:
                    user_password=user_password+char
                    mylcd.lcd_display_string(user_password,2)
                    time.sleep(0.03)
            

          
        
    except KeyboardInterrupt:
        GPIO.cleanup()
        sys.exit()

