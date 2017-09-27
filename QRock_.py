from PIL import Image
import requests as request
import json
import time
import io
import picamera
import zbar
import RPi.GPIO as g
import threading

g.setwarnings(False)
#SerialNumberSet
SERIALNUMBER = "YHCO234"
#GPIOSet
g.setmode(g.BCM)
#0 is Close, 1 is Open
DRStat = 0
#pinNumberSet (5,6) == (1,0) is Open
motOpen = 5
motClose = 6
rgbR = [16,26]
rgbG = [20,19]
rgbB = [21,13]
startBtn = 25
tglBtn = 12
lmtStch = 24
#token
tknValue = ""
def mtrAction(mtrPin):
    mtrOther = 0
    global DRStat
    #print mtrPin, DRStat
    if mtrPin == motOpen:
        mtrOther = motClose
        DRStat = 1
        #print 'Open'
    else:
        mtrOther = motOpen
        DRStat = 0
        #print 'Close'
    g.output(mtrPin,True)
    g.output(mtrOther,False)
    time.sleep(0.5)
    g.output(mtrPin,False)
    g.output(mtrOther,False)
def ledTurn(leds):
    for r in rgbR:
        g.output(r,True)
    for rg in rgbG:    
        g.output(rg,True)
    for b in rgbB:
        g.output(b,True)
    for led in leds:
        for l in led:
            g.output(l,False)
def refreshTkn():
    header={"Content-type":"application/x-www-form-urlencoded"}
    data = {}
    data['serial_number']=SERIALNUMBER
    r = request.post("http://qrock.cafe24app.com/iot/token",headers=header,data=data)
    jsonData = json.loads(r.text)
    if jsonData[0]['code']=='fail':
        for i in range(3):
            ledTurn([rgbR,rgbG])
            time.sleep(0.8)
            ledTurn([])
            time.sleep(0.8)
    else:
        tknValue = jsonData[1]['token']
        f = open('QRCODE_LOCK.token','w')
        f.write(tknValue)
        f.close();
#Check Part
def CheckPart():
    #print "Scanning Start"
    timeOut=0
    while True:
        my_stream = io.BytesIO()

        if timeOut >= 7:
            return

        with picamera.PiCamera() as camera :
            camera.capture(my_stream, format='jpeg')

        timeOut=timeOut+1
        scanner = zbar.ImageScanner()
        scanner.parse_config('enable')

        my_stream. seek(0)
        pil = Image.open(my_stream).convert('L')
        
        width, height = pil.size
        raw = pil.tostring()

        dcdImg = zbar.Image(width, height, 'Y800', raw) 

        scanner.scan(dcdImg)

        #print "QR Code Sencing"
        for symbol in dcdImg:
            #print 'decoded', symbol.type, 'symbol', '"%s"' % symbol.data
            #time.sleep(0.5)
            if symbol.data != None:
                    try:
                        primary_key = symbol.data.split(',')[0]
                        user_email = symbol.data.split(',')[1]
                        qrock_key = symbol.data.split(',')[2]
                    except:
                        primary_key = ''
                        user_email = ''
                        qrock_key = ''
                    data = {}
                    data['qrock_pk'] = primary_key
                    data['serial_number'] = SERIALNUMBER
                    data['user_email'] = user_email
                    data['qrock_key'] = qrock_key
                    while True:
                        header={"Content-type":"application/x-www-form-urlencoded","x-access-token":tknValue[0]}
                        #print header
                        r = request.post("http://qrock.cafe24app.com/iot/select",headers=header,data=data)
                        #print r.text
                        jsonData = json.loads(r.text)
                        #Exception Handling : success, fail
                        #print jsonData[0][u'code']
                        if jsonData[0][u'code'] == "success" :
                            mtrAction(motOpen)
                            return
                        elif jsonData[0][u'code'] == "not-token" :
                            #print "token refresh"
                            refreshTkn()
                        elif jsonData[0][u'code'] == "fail" :
                            print "It's wrong code"
                            for i in range(3):
                                ledTurn([rgbR])
                                time.sleep(0.8)
                                ledTurn(())
                                time.sleep(0.8)
                            return
                            
#setup
g.setup(motOpen,g.OUT)
g.setup(motClose,g.OUT)
for rr in rgbR:
    g.setup(rr,g.OUT)
for rg in rgbG:
    g.setup(rg,g.OUT)
for rb in rgbB:
    g.setup(rb,g.OUT)
g.setup(startBtn,g.IN)
g.setup(tglBtn,g.IN)
g.setup(lmtStch,g.IN)
#motorSet
mtrAction(motClose)
#ledSet
ledTurn([])
#internetSet
try:
    request.post("http://www.naver.com")
except request.exceptions.ConnectionError:
    #print "internet Connection error"
    for i in range(3):
        ledTurn([rgbR,rgbG])
        time.sleep(0.8)
        ledTurn([])
        time.sleep(0.8)
    exit()
#tokenSet
try:
    f = open('QRCODE_LOCK.token','r')
    tknValue = f.readlines()
    f.close()
except:
    refreshTkn()
#Action Part
flagS = False
def CameraPart():
    global flagS
    while True:
        print "1"
        if g.input(startBtn) == True:
            flagS = True
            ledTurn([rgbR,rgbG,rgbB])
            continue
        if flagS == True:
            CheckPart()
            #print "Scanning end"
            flagS = False
        else:
            ledTurn([])
            
flag = False
ct = 0

def SensPart():
    global DRStat
    global flag
    global ct
    while True:
        print "2"
        if  DRStat == 1 :
            if g.input(lmtStch) == False :
                if ct >= 7 :
                    ct = 0
                    mtrAction(motClose)
                else :
                    #print ct
                    ct=ct+1;
                    time.sleep(0.2)
            else :
                ct = 0
        if g.input(tglBtn) == True :
            #print 'push1'
            flag = True
            continue
        if flag == True :
            #print 'push2'
            if DRStat == 1 :
                mtrAction(motClose)
            else :
                mtrAction(motOpen)
            flag = False
            
            
ca = threading.Thread(target=CameraPart)
sen = threading.Thread(target=SensPart)
ca.start()
sen.start()

"""
global DRStat
flag = False
flagS = False
ct = 0
while True:
    if  DRStat == 1 :
        if g.input(lmtStch) == False :
            if ct >= 3 :
                ct = 0
                mtrAction(motClose)
            else :
                #print ct
                ct=ct+1;
                time.sleep(0.5)
        else :
            ct = 0
    if g.input(startBtn) == True:
            flagS = True
            ledTurn([rgbR,rgbG,rgbB])
            continue
        if flagS = True:
            CheckPart()
            print "Scanning end"
            flagS = False
        else
            ledTurn([])
    if g.input(tglBtn) == True :
        #print 'push1'
        flag = True
        continue
    if flag == True :
        #print 'push2'
        if DRStat == 1 :
            mtrAction(motClose)
        else :
            mtrAction(motOpen)
        flag = False
"""
