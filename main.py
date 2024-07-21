from machine import Pin
import network
import socket
import time
from json import dumps
import urequests
import ujson

class Servo:
    def __init__(self, MIN_DUTY=300000, MAX_DUTY=2300000, pin=0, freq=50):
        self.pwm = machine.PWM(machine.Pin(pin))
        self.pwm.freq(freq)
        self.MIN_DUTY = MIN_DUTY
        self.MAX_DUTY = MAX_DUTY
        self.current_deg = 130
        
    def rotateDeg(self, deg, duration=2):
        if deg < 0:
            deg = 0
        elif deg > 180:
            deg = 180
        
        target_duty_ns = int(self.MAX_DUTY - deg * (self.MAX_DUTY-self.MIN_DUTY)/180)
        
        steps = 100
        step_size = (target_duty_ns - self.pwm.duty_ns()) / steps
        
        # Rotate smoothly
        for _ in range(steps):
            self.pwm.duty_ns(int(self.pwm.duty_ns() + step_size))
            time.sleep(duration / steps)
            
        self.current_deg = deg

def connect_WiFi(ssid, password):
    wlan.active(True)
    wlan.connect(ssid, password)
    connection_timeout = 600
    print('Waiting for Wi-Fi connection...')
    while connection_timeout > 0:
        if wlan.status() >= 3:
            break
        print(wlan.status())
        connection_timeout -= 1
        led.toggle()
        time.sleep(1)
    if wlan.status() != 3:
        print('Failed to connect to Wi-Fi')
        return False
    else:
        print('Connection successful!')
        network_info = wlan.ifconfig()
        print('IP address:', network_info[0])
        return True

device_id = "newDevice"
url = f"http://89.169.161.205:8080/water/{device_id}"
frequency = 2
servo = Servo()
led = machine.Pin('LED', machine.Pin.OUT)
wlan = network.WLAN(network.STA_IF)
led.on()
time.sleep(3)
led.off()

ssid = 'Servo-Control'
password = 'PicoW-Servo'

station = network.WLAN(network.AP_IF)
station.active(False)
station.config(essid=ssid, password=password)
station.active(True)

while station.isconnected() == False:
  pass

print('Connection successful')
print(station.ifconfig())

s = socket.socket()
s.bind(('', 80))
s.listen(5)
while True:
    try:
        conn, addr = s.accept()
        print('Got a connection from %s' % str(addr))
        request = conn.recv(1024)
        request = str(request)
        index = request.find('ssid=') + len('ssid=')
        second = request.find('/password=')
        second_index = second + len('/password=')
        ssid = request[index:second]
        password = request[second_index:request.find(' HTTP')]
        ssid = ssid.replace('%20', ' ')
        print(ssid)
        print(password)
        conn.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        resp = dumps({'id': device_id})
        print(resp)
        conn.send(resp)
        conn.close()
        if ssid != "":
            if connect_WiFi(ssid, password):
                station.active(False)
                break
    except OSError as e:
        conn.close()
        print('Connection closed')
    
led.on()
while True:
    try:
        response = urequests.get(url)
        if response.status_code == 200:
            data = ujson.loads(response.text)
    
            watering = data["watering"]
            frequency = data["timedelta"]
            timeInterval = int(data["seconds"])
            led.toggle()
            time.sleep(0.25)
            led.toggle()
            time.sleep(0.25)
            led.toggle()
            time.sleep(0.25)
            led.toggle()
        
            if watering == 1:
                servo.rotateDeg(140)
                time.sleep(timeInterval)
                servo.rotateDeg(50)
            time.sleep(frequency * 60)
    except:
        pass
