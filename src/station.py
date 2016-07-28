#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import time

from smbus import SMBus

import Adafruit_BMP.BMP085 as BMP085   # Actually using it for BMP180 here
import Adafruit_BBIO.GPIO as GPIO

import grove_oled

def blink(pin, blinktime=0.1):
    """ Blink a single LED
    """
    blinks([pin], blinktime)

def blinks(pins, blinktime=0.1):
    """ Blink a list of LEDs
    """
    for pin in pins:
        GPIO.output(pin, GPIO.HIGH)
    time.sleep(blinktime)
    for pin in pins:
        GPIO.output(pin, GPIO.LOW)

if __name__ == "__main__":
    # Set up GPIO pins
    pin0 = "P9_14"   # GPIO_50, blue, down
    GPIO.setup(pin0, GPIO.OUT)
    GPIO.output(pin0, GPIO.LOW)

    pin1 = "P9_16"   # GPIO_51, red, up
    GPIO.setup(pin1, GPIO.OUT)
    GPIO.output(pin1, GPIO.LOW)

    grove_oled.oled_init()
    grove_oled.oled_clearDisplay()
    grove_oled.oled_setNormalDisplay()
    grove_oled.oled_setVerticalMode()
    time.sleep(.1)

    blinkshort = 0.05
    blinklong = 0.8

    sensor = BMP085.BMP085(busnum=2, i2c_interface=SMBus, mode=BMP085.BMP085_ULTRAHIGHRES)

    # ARTIK Cloud setup
    api_client = artikcloud.ApiClient()
    DEVICE_ID = os.getenv('ARTIKCLOUD_DEVICE_ID')
    DEVICE_TOKEN = os.getenv('ARTIKCLOUD_DEVICE_TOKEN')
    api_client.set_default_header(header_name="Authorization", header_value="Bearer {}".format(DEVICE_TOKEN))
    messages_api = artikcloud.MessagesApi(api_client)
    message = artikcloud.MessageAction()
    message.type = "message"
    message.sdid = "{}".format(DEVICE_ID)

    # Default is to monitor the temperature
    TEST_PRESSURE = True if os.getenv('TEST_PRESSURE', default='0') == '1' else False

    if TEST_PRESSURE:
        reading = sensor.read_pressure
        printreading = '{} Pa'
    else:
        reading = sensor.read_temperature
        printreading = '{:.1f} C'

    # Holt-Winters parameters
    alpha = 0.15
    beta = 0.05

    # Set up initial values
    x = reading()
    a = x
    b = 0
    blinktime = blinkshort
    print("{},{},{}".format(x, a, b))

    try:
        PERIOD = int(os.getenv('PERIOD', default='1'))
    except ValueError:
        PERIOD = 1
    if PERIOD < 1:
        PERIOD = 1

    try:
        # different display trashhold, in units of X unit/min, above which do long blink
        SENSOR_THRESHOLD = float(os.getenv('PERIOD', default='1.0'))
    except ValueError:
        SENSOR_THRESHOLD = 1.0
    if SENSOR_THRESHOLD < 0:
        SENSOR_THRESHOLD = 1.0

    i = 0
    trend = ''
    while True:
        time.sleep(PERIOD - blinktime)
        x = reading()
        aold, bold = a, b
        a = alpha * x + (1 - alpha) * (aold + bold)
        b = beta * (a - aold) + (1 - beta) * bold
        print("Reading: {0:0.1f}; a[t]: {1:0.3f}; b[t]: {2:0.3f}".format(x, a, b))
        # Do long blink if temperature change is more than 1 unit/min
        blinktime = blinklong if abs(b) >= SENSOR_THRESHOLD / 60.0 * PERIOD else blinkshort
        if abs(b) < 0.001:
            blinks([pin0, pin1], blinktime)
            trend += '-'
        elif b < 0:
            blink(pin0, blinktime)
            trend += '\\'
        else:
            blink(pin1, blinktime)
            trend += '/'
        if len(trend) > 12:
            trend = trend[-12:]
        grove_oled.oled_setTextXY(0,0)
        grove_oled.oled_putString(printreading.format(x))
        message.ts = int(round(time.time() * 1000))
        message.data = {'Temperature': x}
        if i % 120 == 0:
            response = messages_api.send_message_action(message)
            print(response)
        i += 1
