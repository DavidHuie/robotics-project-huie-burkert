"""
arduinoController.py
Python side controller file for interfacing with Arduino
Summer 2010
Beryl Egerter, Sarah Johnson, Philip Aelion-Moss
"""

import serial
import time
import threading
import commands
import os
import platform
import math

# The numbers below CANNOT be changed here without changing the ARDUINO
# code. They contain the commands sent to the Arduino via Serial to perform
# various actions.


DIGITAL_OUTPUT_ON_OFF = chr(120) # Turns an LED to HIGH or LOW

# The following commands deal with servo motors
ATTACH_SERVO = chr(121) # Attaches a servo motor to a pin
DETACH_SERVO = chr(122) # Detaches a servo motor from a pin
SERVO_GO = chr(123) # Gives a servo a speed at which to rotate
SET_SERVO_STOP = chr(124) # Gives a servo a new base or "stopped" speed
RESTORE_STOP = chr(125) # Restores the base speed of a servo to 94.0

# The following commands deal with piezo speakers
PLAY_NOTE = chr(126) # Plays a single note 
ADD_NOTE = chr(127) # Adds a note to arrays containing a melody
PLAY_MELODY = chr(128) # Plays the melody
CLEAR_MELODY = chr(129) # Clears the melody from the arrays
PLAY_PITCH = chr(130) # Plays a single user-defined pitch
ADD_PITCH = chr(131) # Adds a single user-defined pitch to the arrays

# The following commands deal with Analog inputs
MAKE_INPUT = chr(132) # Switches an Analog pin back to Analog Input
MAKE_OUTPUT = chr(133) # Turns an Analog pin to Digital Output
GET_ANALOG = chr(134) # Gets a number representing the input value
GET_RANGE = chr(135) # Gets the input value with \n between each reading

# Commands added for laser pointer!
RAW_SERVO_POS = chr(142) # why not...



# The following are global variables used throughout the code
VALID_OUTPUT_PINS = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, \
                     14, 15, 16, 17, 18, 19] 
VALID_SERVO_PIEZO_PINS = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
ANALOG_PINS = [True, True, True, True, True, True] 
SERVO_PINS = [0,0]
SERVO1_SPEED = [0,False]
SERVO2_SPEED = [0,False]
SERVO_SPEEDS = [SERVO1_SPEED,SERVO2_SPEED]
MELODY_LIST = []
PLACE_IN_MELODY_LIST = 0
BLINK = False
RUN = True
ser = None


# The following functions control the connection to the arduino:

def getPort():
    '''Initializes without a port'''

    linux = str(platform.dist())
    mac = str(platform.mac_ver())
    pc = str(platform.win32_ver())

    if len(mac) == max([len(mac), len(linux), len(pc)]):
        print "You're using a mac!"
        try:
            listing = commands.getoutput("ls -l /dev/tty.*").split('\n')[1:]
            portlines = [x for x in listing if 'usb' in x]
            for line in portlines:
                line = line.split()
                port = [x for x in line if 'tty.usbserial' in x]
                if port: print port[0]
            if port: return port[0]
        except:
            print "Either you aren't in the mac lab, or SOMEBODY messed up. \
Go find Dodds, he understands this stuff"
    elif len(pc) == max([len(mac), len(linux), len(pc)]):
        print "You're using a PC!"
        return 29
    else:
        print "You appear to be using a linux machine."
        print "The port system for that is not implemented yet"

def init(portString):
    ''' Initializes Arduino board by finding a port, checking and
    catching errors, and starting the loop thread'''
    global RUN
    RUN = True
    global ser
    try:
        ser = serial.Serial(portString)
    except serial.SerialException:
        try:
            close()
            ser = serial.Serial(portString)
        except AttributeError:
            try:
                ser = serial.Serial(portString)
            except serial.SerialException:
                print "Looks like you didn't properly exit last time. "
                print "Make sure to call close().  Please unplug Arduino and \
try again."
        except serial.SerialException:
            print "Could not find Arduino board.  Please unplug it and try \
again."

    print "About to start the run loop..."
    runLoop().start()

def close(port = ''):
    '''Ends all contact with the Arduino and ends the runLoop thread
    in a safe manner; always call this function when you're done using
    the Arduino'''
    global RUN
    RUN = False
    time.sleep(.15)
    if not port:
        try:
            ser.close()
        except AttributeError:
            print "It looks like you plugged in your Arduino too long."
    else:
        try:
            serial.Serial(port).close()
        except AttributeError:
            print "It looks like you plugged in your Arduino too long."

def wait(n):
    '''Waits for n seconds; use to prevent Arduino from doing
    too many things at once''' 
    time.sleep(n)

def digitNumber(n, digitNum):
    '''The digitNumth digit of a 2-digit binary number n'''
    if digitNum == 1:
        if len(str(n)) == 1: return 0
        elif len(str(n)) == 2: return int(str(n)[0])
        else: return "Number must be 2 digits!" 
    elif digitNum == 2: return int(str(n)[-1])
    else: return "digitNum must be 1 or 2 since n is a 2-digit number"

def __flush():
    '''Flushes all data waiting to be read from arduino'''
    x = ser.inWaiting()
    while x > 0:
        ser.read(ser.inWaiting())
        x = ser.inWaiting()


# The following functions control digital outputs and the built-in LED at pin 13

def setLED(ledOn_Off):
    '''Sets the Arduino's LED (pin 13) light on if ledOn_Off is True and off if
False'''
    if ledOn_Off:
        return output(13, True)
    else:
        return output(13, False)

def setBlink(blinkOn_Off):
    ''' Turns the Arduino's LED (pin 13) light on blink if blinkOn_Off is True
and turns blink off if False'''
    global BLINK
    BLINK = blinkOn_Off

def blink():
    '''Blinks the Arduino's LED once'''
    time.sleep(.1)
    setLED(True)
    time.sleep(.1)
    setLED(False)


def output(pinNum, pinOn_Off):
    ''' Sets the output of the given pin (2 - 19) to HIGH if pinOn_Off is True
and to LOW if it is False, assuming the given pin is not in
use as anything else. '''
    if (pinNum not in VALID_OUTPUT_PINS):
        return "Pin " + str(pinNum) + " is not valid. Only use Pins \
2 - 19, as long as they are not attached to a servo or set as an analog input."
    elif (pinNum in SERVO_PINS):
        return "Please choose another pin. Pin " + str(pinNum) + " is currently\
 attached to a servo."
    elif (pinNum > 13 and pinNum < 20 and ANALOG_PINS[pinNum - 14]):
        return "Pin " + str(pinNum) + " is currently in use as an \
analog input pin. Please choose a different pin."
    else:
        ser.write(DIGITAL_OUTPUT_ON_OFF)
        ser.write(chr(pinNum))
        if (pinOn_Off):
            ser.write(chr(1))
        else:
            ser.write(chr(0))


# The following functions control actions with servo motors:

def attachServo(servoNum, pinNum):
    ''' Attaches the specified servo (1 or 2) to the specified pin. '''
    if (servoNum not in [1, 2]):
        return "You may only use two servos. Please choose 1 or 2."
    elif (pinNum not in VALID_SERVO_PIEZO_PINS) or (pinNum in SERVO_PINS):
        return "Pin " + str(pinNum) + " is not available for use. Please \
choose a pin between 2 and 13 that is not already attached to a servo."
    elif (SERVO_PINS[servoNum-1] != 0):
        return "Servo "+str(servoNum)+" is already attached to pin "\
               +str(SERVO_PINS[servoNum-1])+"."
    else:
        ser.write(ATTACH_SERVO)
        ser.write(chr(servoNum))
        ser.write(chr(pinNum))
        SERVO_PINS[servoNum-1] = pinNum
        print "Attached servo "+str(servoNum)+" to pin "+str(pinNum)+"."
        
		
def detachServo(servoNum):
    ''' Detaches the specified servo (1 or 2) from its current pin. '''
    if (servoNum not in [1,2]):
        return "You may only use two servos. Please choose 1 or 2."
    elif (SERVO_PINS[servoNum-1] == 0):
        return "Servo "+str(servoNum)+" is not currently attached to a pin."
    else:
        print "Detaching servo "+str(servoNum)+" from pin " \
              +str(SERVO_PINS[servoNum-1])+"."
        SERVO_PINS[servoNum-1] = 0
        ser.write(DETACH_SERVO)
        ser.write(chr(servoNum))


def servoOn(servoNum, speed, CLOCKWISE):
    ''' Sets the servo (1 or 2) to a floating point speed between 0.0 and 10.0,
clockwise or ccw'''
    if (servoNum not in [1, 2]):
        return "There are only two servos. Please choose 1 or 2."
    elif (speed < 0 or speed > 10):
        return "Your speed for servo " + str(servoNum) + " was " \
               + str(speed) + ".  Speed must be between 0.0 and 10.0!"
    elif CLOCKWISE not in [False,True]:
        return str(CLOCKWISE) + " is not a valid input for CLOCKWISE. \
Please input a boolean."
    elif (SERVO_PINS[servoNum-1] == 0):
        return "Servo "+str(servoNum)+" is not attached to a pin yet. \
Please attach it to a pin before setting a speed. "
    elif speed == SERVO_SPEEDS[servoNum-1][0] and \
         CLOCKWISE == SERVO_SPEEDS[servoNum-1][1]:
        return
    else:
        SERVO_SPEEDS[servoNum-1][0] = speed
        SERVO_SPEEDS[servoNum-1][1] = CLOCKWISE
        speed = int(speed * 10)
        direction = 0
        if (CLOCKWISE): direction = 1
        ser.write(SERVO_GO)
        ser.write(chr(servoNum))
        ser.write(chr(speed))
        ser.write(chr(direction))


def servoPos(servoNum, destination):
    if (servoNum not in [1, 2]):
        return "There are only two servos. Please choose 1 or 2."
    elif (SERVO_PINS[servoNum-1] == 0):
        return "Servo "+str(servoNum)+" is not attached to a pin yet. \
Please attach it to a pin before setting a speed. "
    else:
        print "In servoPos: writing GO", servoNum, destination
        ser.write(RAW_SERVO_POS)
        ser.write(chr(servoNum))
        ser.write(chr(destination))
    
    
    
def servoOff(servoNum):
    ''' Turns servo (1 or 2) off. '''
    return servoOn(servoNum, 0, True)


def setServoStop(servoNum, speed, CLOCKWISE):
    ''' Sets the servo's (1 or 2) stopping speed to a speed between 0.0 and 10.0,
clockwise or ccw'''
    direction = 0
    cwString = "counter-clockwise"
    if (servoNum not in [1, 2]):
        return "There are only two servos. Please choose 1 or 2."
    elif (speed < 0 or speed > 10):
        return "Your stopping speed for servo " + str(servoNum) + " was " \
               + str(speed) + ".  Speed must be between 0.0 and 10.0!" 
    elif (CLOCKWISE not in [False,True]):
        return str(CLOCKWISE) + " is not a valid input for CLOCKWISE. \
Please input a boolean."
    elif (SERVO_PINS[servoNum-1] == 0):
        return "Servo "+str(servoNum)+" is not attached to a pin yet. \
Please attach it to a pin before setting a stopping speed. "
    else:
        if (CLOCKWISE):
            direction = 1
            cwString = "clockwise"
        print "Changing servo "+str(servoNum)+"'s stopping speed to " \
              +str(speed)+" away from the previous, and "+cwString+"."
        speed = int(speed * 10)
        ser.write(SET_SERVO_STOP)
        ser.write(chr(servoNum))
        ser.write(chr(speed))
        ser.write(chr(direction))


def restoreServoStop(servoNum):
    ''' Returns the stopping speed of the servo (1 or 2) to the preset stopping\
 speed.'''
    if (servoNum not in [1, 2]):
        return "There are only two servos. Please choose 1 or 2."
    else:
        ser.write(RESTORE_STOP)
        ser.write(chr(servoNum))



# The following functions are for dealing with Piezo speakers

def convertNoteLength(noteLength):
    ''' Gives a list of the numerator and denominator of noteLength.
convertNoteLength is a helper function for playNote, playPitch, addNote,
addPitch, replaceNote, and replacePitch.'''
    for i in noteLength:
        if (i not in '0123456789/'):
            print "noteLength should be a fraction. Please \
include only digits and the '/' character."
            return "no"
    noteLength = noteLength.split('/')
    if len(noteLength) == 1:
        noteLength.append('1')
    if len(noteLength) != 2:
        print "The input noteLength is not a fraction."
        return "no"
    noteLength = [int(x) for x in noteLength]
    for x in noteLength:
        if (x > 255 or x < 0 or noteLength[1] == 0):
            print "Please use a fraction with a numerator \
between 0 and 255 and a denominator between 1 and 255 for noteLength."
            return "no"
    return noteLength


def playNote(pin, noteName, octave, noteLength):
    ''' Sends signal to the piezo speaker attached to pin to play noteName for
noteLength time (noteLength should be a string: '1' or '1/1' for a whole note,
'1/4' for a quarter note, '1/8' for an eighth note, '3/4' for a three quarters
note and so on). octave is an int representing the octave (with each octave
number starting from C, ascending) where 4 is the octave starting at middle C.
note is a string representing the name of the note you wish to play (i.e. A,B,G)
All enharmonics are registered as sharps. For a sharp note, please enter the
note name followed by the symbol # (i.e. C# for C sharp, A# for A sharp or
B flat) You may use capital or lowercase letters. NOTE: You have octaves
0 to 10 available to you, which should well encompass the upper range of human
hearing. '''
    newNoteLength = convertNoteLength(noteLength)
    if (pin not in VALID_SERVO_PIEZO_PINS):
        return str(pin) + " is not an available pin. Please only use \
pins 2 - 13."
    elif (pin in SERVO_PINS):
        return "Please choose another pin. Pin "+str(pinNum)+" is currently \
attached to a servo."
    elif (octave < 0 or octave > 10):
        return "Octave " +str(octave)+ " is not available. Please stick to \
octaves 0 through 10."
    elif noteName not in "C#D#EF#G#A#Bc#d#ef#g#a#b":
        return str(noteName)+ " is not a valid note name! A-G please. \
(With perhaps a sharp)"
    elif newNoteLength == "no":
        return
    else:   
        noteList = ["Cc","C#c#","Dd","D#d#","Ee","Ff",\
                    "F#f#","Gg","G#g#","Aa","A#a#","Bb"]
        for i in range(len(noteList)):
            if noteName in noteList[i]:
                ser.write(PLAY_NOTE)
                ser.write(chr(newNoteLength[0]))
                ser.write(chr(newNoteLength[1]))
                ser.write(chr(pin))
                ser.write(chr(octave)) 
                ser.write(chr(i))
                return
        return str(noteName)+ " is not a valid note name!"


def sendNote(notePlace, noteName, octave, noteLength):
    ''' sendNote is a helper function for addNote and replaceNote. Do not use
sendNote on its own. '''
    global MELODY_LIST
    global PLACE_IN_MELODY_LIST
    newNoteLength = convertNoteLength(noteLength)
    newNote = noteName + str(octave), noteLength
    stringPiece = " was added to the end of "
    __flush()
    if octave < 0 or octave > 10:
        return "Octave " +str(octave)+ " is not available. Please stick to \
octaves 0 through 10."
    elif (noteName not in "C#D#EF#G#A#Bc#d#ef#g#a#b"):
        return str(noteName)+ " is not a valid note name! A-G please. \
(With perhaps a sharp)"
    elif newNoteLength == "no":
        return
    else:
        noteList = ["Cc","C#c#","Dd","D#d#","Ee","Ff", \
                    "F#f#","Gg","G#g#","Aa","A#a#","Bb"]
        for i in range(len(noteList)):
            if noteName in noteList[i]:
                if (notePlace == 255):
                    MELODY_LIST.append(newNote)
                    PLACE_IN_MELODY_LIST += 1
                else:
                    MELODY_LIST[notePlace] = newNote
                    stringPiece = " replaced position "+str(notePlace)+" in "
                ser.write(ADD_NOTE)
                ser.write(chr(newNoteLength[0]))
                ser.write(chr(newNoteLength[1]))
                ser.write(chr(octave)) 
                ser.write(chr(i))
                ser.write(chr(notePlace))
                
                while ser.inWaiting() < 1:
                    time.sleep(0.001)
                text = ser.read(ser.inWaiting())
                
                return str(newNote) +stringPiece+ "the MELODY_LIST."
            
        return str(noteName) + " is not a valid note name. "


def addNote(noteName, octave, noteLength):
    ''' Adds the note indicated by note (string) and octave (integer between
0 and 10) of length noteLength (a fraction represented by a string, e.g. '1/4')
and adds it to the end of MELODY_LIST which holds the information for the melody
to be played. '''
    global PLACE_IN_MELODY_LIST
    if PLACE_IN_MELODY_LIST > 254:
        return "Please limit your melody to a length of 255 notes or pitches."
    else:
        # Because the user is restricted to note places 0 - 254,
        # 255 is free to serve as a separate command which in this case
        # is the command to add a NEW note to the end of MELODY_LIST rather
        # than replacing an existing note
        return sendNote(255, noteName, octave, noteLength)


def replaceNote(notePlace,noteName,octave,noteLength):
    ''' Replaces any note in your melody (you can have up to 255 notes (0-244))
with the given note defined with noteName (string), octave (integer between
0 and 10), and noteLength (a fraction represented by a string, e.g. '1/4').'''
    global PLACE_IN_MELODY_LIST
    if notePlace >= PLACE_IN_MELODY_LIST:
        return "You can only replace notes or pitches that exist. You can \
replace any note from 0 to " + str(PLACE_IN_MELODY_LIST-1) + "."
    else:
        return sendNote(notePlace, noteName, octave, noteLength)
    

def playMelody(pinNum):
    ''' Plays the melody held in MELODY_LIST from pin. '''
    if pinNum not in VALID_SERVO_PIEZO_PINS:
        return str(pinNum) + " is not an available pin. Please only use pins \
2 - 13."
    elif pinNum in SERVO_PINS:
        return "Please choose another pin. Pin " + str(pinNum) + " is \
currently attached to a servo."
    else:
        ser.write(PLAY_MELODY)
        ser.write(chr(pinNum))


def showMelody():
    ''' Displays the MELODY_LIST, so that you may see what your
melody currently is.'''
    description = 'noteName and octave / pitch', 'noteLength'
    print description
    for i in range(PLACE_IN_MELODY_LIST):
        print str(i) +" "+ str(MELODY_LIST[i])


def clearMelody():
    ''' Wipes clean MELDOY_LIST, which holds the information controlling the
melody. NOTE: You can also do this by refreshing the Python script.'''
    global MELODY_LIST
    global PLACE_IN_MELODY_LIST
    MELODY_LIST = []
    PLACE_IN_MELODY_LIST = 0
    ser.write(CLEAR_MELODY)


def simpleSendPitch(pitch):
    '''Sends a pitch in parts to the Arduino, as the Arduino's Serial connection
can only handle one byte at a time. simpleSendPitch is a helper function for
playPitch, addPitch, and replacePitch. '''
    pitchPart1 = pitch%100
    helperPart1 = (pitch-pitchPart1)/100
    ser.write(chr(pitchPart1))
    pitchPart2 = helperPart1%100
    helperPart2 = (helperPart1-pitchPart2)/100
    ser.write(chr(pitchPart2))
    pitchPart3 = helperPart2
    ser.write(chr(pitchPart3))


def playPitch(pinNum, pitch, noteLength):
    ''' playPitch plays a user-determined pitch for noteLength time \
(a fraction represented by a string, e.g. '1/4') at pin. NOTE: Arduino's int\
is only two bytes, so the highest pitch it can actually deal with is 32767. '''
    newNoteLength = convertNoteLength(noteLength)
    if pinNum not in VALID_SERVO_PIEZO_PINS:
        return str(pin) + " is not an available pin. Please only use pins \
2 - 13."
    elif pinNum in SERVO_PINS:
        return "Please choose another pin. Pin " + str(pinNum) + " is \
currently attached to a servo."
    elif pitch < 0 or pitch > 32767:
        return "Please only input a pitch between 0 and 32767."
    elif newNoteLength == "no":
        return
    else:  
        ser.write(PLAY_PITCH)
        ser.write(chr(newNoteLength[0]))
        ser.write(chr(newNoteLength[1]))
        ser.write(chr(pinNum))
        simpleSendPitch(pitch)


def sendPitch(notePlace, pitch, noteLength):
    ''' sendPitch is a helper function for addPitch and replacePitch.
Do not use sendPitch on its own.'''
    global MELODY_LIST
    global PLACE_IN_MELODY_LIST
    newPitch = pitch, noteLength
    newNoteLength = convertNoteLength(noteLength)
    stringPiece = " was added to the end of "
    __flush()

    if pitch < 0 or pitch > 32767:
        return "Please choose a pitch between 0 and 32767."
    elif newNoteLength == "no":
        return
    else:
        if (notePlace == 255):
            MELODY_LIST.append(newPitch)
            PLACE_IN_MELODY_LIST += 1
        else:
            MELODY_LIST[notePlace] = newPitch
            stringPiece = " replaced position "+str(notePlace)+" in "
        ser.write(ADD_PITCH)
        ser.write(chr(newNoteLength[0]))
        ser.write(chr(newNoteLength[1]))
        simpleSendPitch(pitch)
        ser.write(chr(notePlace))

        while ser.inWaiting() < 1:
            time.sleep(0.001)
        text = ser.read(ser.inWaiting())

        return str(newPitch) +stringPiece+ "the MELODY_LIST."


def addPitch(pitch, noteLength):
    ''' Adds a user-determined pitch of length noteLength (a fraction
represented by an int, ex. '1/4')to the end of MELODY_LIST which holds the data
of the melody to be played. '''
    global PLACE_IN_MELODY_LIST
    if PLACE_IN_MELODY_LIST > 254:
        return "Please limit your melody to a length of 255 notes or pitches."
    else:
        # Because the user is restricted to note places 0 - 254,
        # 255 is free to serve as a separate command which in this case
        # is the command to add a NEW pitch to the end of MELODY_LIST rather
        # than replacing an existing note or pitch
        return sendPitch(255, pitch, noteLength)
    

def replacePitch(notePlace, pitch, noteLength):
    ''' Replaces any note in your melody (only notes 0-244, and only if they
have been added to the melody already) with the given note defined with pitch
(an integer between 0 and 32767) and noteLength (a fraction represented as a
string, ex. '1/4').'''
    global PLACE_IN_MELODY_LIST
    if notePlace >= PLACE_IN_MELODY_LIST:
        return "You can only replace notes or pitches that exist. You can \
replace any note from 0 to " + str(PLACE_IN_MELODY_LIST) + "."
    return sendPitch(notePlace, pitch, noteLength)



# The following functions control the analog pins:

def setAnalog(pinNum):
    '''Set analog pins 0 - 5 as analog inputs'''
    global ANALOG_PINS
    if (pinNum not in [0, 1, 2, 3, 4, 5]):
        return "Please choose an analog pin from 0 - 5."
    elif (ANALOG_PINS(pinNum)):
        return "Pin "+str(pinNum)+" is already set as an analog input pin."
    else:
        ser.write(MAKE_INPUT)
        ser.write(chr(14 + pinNum))
        ANALOG_PINS[pinNum] = True


def setDigital(pinNum):
    '''Set analog pins 0 - 5 as digital output'''
    global ANALOG_PINS
    if (pinNum not in [0, 1, 2, 3, 4, 5]):
        return "Please choose an analog pin from 0 - 5."
    elif (not ANALOG_PINS(pinNum)):
        return "Pin "+str(pinNum)+" is already set as digital output."
    else:
        ser.write(MAKE_OUTPUT)
        ser.write(chr(14+pinNum))
        ANALOG_PINS[pinNum] = False
        
    
def readAnalog(pinNum):
    '''Returns a value read from the analog pin'''
    if (pinNum > 5 or pinNum < 0):
        return "That is not a valid analog pin. Please choose a pin between \
0 and 5."
    elif not (ANALOG_PINS[pinNum]):
        return "Pin " + str(pinNum) + " is not set as an input. Please set \
it as an input before trying to read from it."
    else:
        __flush()
        ser.write(GET_ANALOG)
        ser.write(chr(pinNum))
        time.sleep(0.1)
        text = ""
        while ser.inWaiting() < 1:
            time.sleep(0.001)
        text = ser.read(ser.inWaiting())
        return text

    
def returnRange(pinNum, pauseTime, numRead):
    '''Returns a list of data ( in integer form), numRead long, read from the
       specified pin at a time interval of pauseTime seconds.'''
    if (pinNum > 5 or pinNum < 0):
        return "That is not a valid analog pin. Please choose a pin between \
0 and 5."
    elif not (ANALOG_PINS[pinNum]):
        return "Pin " + str(pinNum) + " is not set as an input. Please set \
it as an input before trying to read from it."
    else:
        __flush()
        for i in range(numRead):
            ser.write(GET_RANGE)
            ser.write(chr(pinNum))
            time.sleep(pauseTime)
        text = ""
        time.sleep(0.05)
        text = ser.read(ser.inWaiting())
        text = text.split('\r\n')
        return [int(x) for x in text[:-1] ]
    

def getADports():
    '''returns a list of values read from every analog pin'''
    for i in range(6):
        ser.write(GET_RANGE)
        ser.write(chr(i))
    DATA = ''
    time.sleep(0.05)  # initial wait for round-trip
    while True:
        DATA += ser.read(ser.inWaiting()) # get all data
        if DATA.count( '\n' ) >= 6: break # enough!
        time.sleep(0.02)  # otherwise wait a bit...
        #print "Waiting!" printed 0 or one times for me...
    # split and convert to integers
    return [ int(x) for x in DATA.split() ]

    
class runLoop (threading.Thread):
    global BLINK
    global RUN
    def run ( self ):
        while RUN:
            while BLINK and RUN:
                blink()
            time.sleep(.21)
