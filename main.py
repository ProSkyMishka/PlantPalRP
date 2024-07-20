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
        self.current_deg = 130  # Track the current angle
        
    def rotateDeg(self, deg, duration=2):  # Add duration parameter
        if deg < 0:
            deg = 0
        elif deg > 180:
            deg = 180
        
        # Calculate the duty cycle for the target angle
        target_duty_ns = int(self.MAX_DUTY - deg * (self.MAX_DUTY-self.MIN_DUTY)/180)
        
        # Calculate the step size for smooth rotation
        steps = 100  # Adjust for smoothness (more steps = smoother)
        step_size = (target_duty_ns - self.pwm.duty_ns()) / steps
        
        # Rotate smoothly
        for _ in range(steps):
            self.pwm.duty_ns(int(self.pwm.duty_ns() + step_size))
            time.sleep(duration / steps)  # Divide duration across steps
            
        self.current_deg = deg  # Update the current angle

def connect_WiFi(ssid, password):
    wlan.active(True)
    wlan.connect(ssid, password)
    connection_timeout = 600
    print('Waiting for Wi-Fi connection...')
    while connection_timeout > 0:
        if wlan.status() >= 3:
            break
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

# URL сайта
device_id = "aezsxdfcgvhbjknl37y2y87ehd"
url = f"http://10.29.91.45:8080/water/{device_id}" # поменять 10.29.91.60 на ip Ромы
frequency = 2
servo = Servo()
led = machine.Pin('LED', machine.Pin.OUT)
wlan = network.WLAN(network.STA_IF)
wlan.active(False)
led.on()
time.sleep(3)
led.off()

ssid = 'Servo-Control'
password = 'PicoW-Servo'
# device_id = "12345rtghjde782yhiux"

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
# Listen for connections
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
            if connect_WiFi(' Plants_smart', 'SmartPla9t6'):
                station.active(False)
                break
    except OSError as e:
        conn.close()
        print('Connection closed')
    
led.on()
while True:
    # Отправка GET-запроса
    try:
#         print("hi")
        response = urequests.get(url)
#         print("hello")
        if response.status_code == 200:
        # Декодирование ответа в формате JSON
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
#             print(watering, frequency, timeInterval)
        
            if watering == 1:
                servo.rotateDeg(140)
                time.sleep(timeInterval)
                servo.rotateDeg(50)
            time.sleep(frequency * 60)
#         else:
            # Обработка ошибки
#             print("Ошибка запроса:", response.status_code)
    except OSError as e:
        conn.close()
#         print('Connection closed')


