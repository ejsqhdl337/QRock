# Add your code here to run in your startup task
import RPi.GPIO as gpio
import requests as request
import json
import io
import time
import picamera
import zbar
from PIL import Image
 
#token error : message,code
headera={"Content-type":"application/x-www-form-urlencoded","x-access-token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzZXJpYWxfbnVtYmVyIjoiV0VBUkVLWloiLCJpYXQiOjE1MDM5MjEyNjYsImV4cCI6MTUwNDUyNjA2NiwiaXNzIjoieW91bmdoLmNvbSIsInN1YiI6ImlvdFByb2R1Y3QifQ.6_byKh_XlNoSTlyT69QgUV4MJixgAJLXuuxvorUVphM "}
#headera={"Content-type":"application/x-www-form-urlencoded"}
 
gpio.setmode(gpio.BCM)
 
gpio.setup(23,gpio.OUT)
gpio.setup(24,gpio.OUT)
 
gpio.output(23,False)
gpio.output(24,False)
# Create an in-memory stream
# Camera warm-up time
#compare parts
while True:
 
    my_stream = io.BytesIO()
    with picamera.PiCamera() as camera:
        camera.start_preview()
        
        camera.capture(my_stream, format='jpeg')
 
    scanner = zbar.ImageScanner()
    scanner.parse_config('enable')   
 
    my_stream.seek(0)
    pil = Image.open(my_stream).convert('L')
    width, height = pil.size
    raw = pil.tostring()
 
    dcdImg = zbar.Image(width, height, 'Y800', raw) 
 
    scanner.scan(dcdImg)
 
    for symbol in dcdImg: 
	if symbol.data != None:
		primary_key = symbol.data.split(',')[0]
		serial_number = "WEAREKZZ"
		user_email = symbol.data.split(',')[1]
		qrock_key = symbol.data.split(',')[2]
		data = {}
		data['qrock_pk'] = primary_key
		data['serial_number'] = serial_number
		data['user_email'] = user_email
		data['qrock_key'] = qrock_key
		r = request.post("http://youngh.cafe24app.com/iot/select",headers=headera,data=data)
                #print r.text
		jsonData = json.loads(r.text)
                #need Exception Handling : success, fail, error
		print jsonData
		print jsonData[0]['code']
		if jsonData[0]['code'] == "success" :
                    gpio.output(23,False)
                    gpio.output(24,True)
                    time.sleep(100)
                    gpio.output(23,False)
                    gpio.output(24,False)
