#!/usr/bin/env python

################################################
# Module:   servo.py
# Created:  2 April 2008
# Author:   Brian D. Wendt
#   http://principialabs.com/
# Version:  0.3
# License:  GPLv3
#   http://www.fsf.org/licensing/
'''
Provides a serial connection abstraction layer
for use with Arduino "MultipleSerialServoControl" sketch.
'''
################################################


# Modified by David Huie

import serial
import time

usbport = '/dev/tty.usbserial-A6008eib'

# Set up serial baud rate
ser = serial.Serial(usbport, 9600, timeout=1)

def move(servo, angle):
    '''Moves the specified servo to the supplied angle.

    Arguments:
        servo
          the servo number to command, an integer from 1-4
        angle
          the desired servo angle, an integer from 0 to 180

    (e.g.) >>> servo.move(2, 90)
           ... # "move servo #2 to 90 degrees"'''

    if (0 <= angle <= 180):
        ser.write(chr(255))
        ser.write(chr(servo))
        ser.write(chr(angle))
    else:
        print "Servo angle must be an integer between 0 and 180.\n"

# Info
PAN_SERVO = 1
TILT_SERVO = 2

# Angle Ranges
PAN_MIN = 0
PAN_MAX = 180

TILT_MIN = 0
TILT_MAX = 150

def move_until_callback(servo, callback, start_angle = 0, end_angle = 150, delta = 1, sleep_time = .01, clockwise = True):
    """
    Moves the servo until callback evaluates to True or the servo has
    completely moved from start_angle to end_angle.

    Returns the end angle of the servo
    """
    while (not callback()) and ( abs(start_angle - end_angle) > 1):
        time.sleep(sleep_time)
        move(servo, start_angle)
        
        if clockwise:
            start_angle += delta
        else:
            start_angle -= delta

    return start_angle

def delta_move(servo, start_angle, delta = 1, sleep_time = .05):
    angle = start_angle + delta
    move(servo, angle)
    time.sleep(sleep_time)
    return angle
