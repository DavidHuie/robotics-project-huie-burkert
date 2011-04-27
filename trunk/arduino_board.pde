/* 
 arduino_board.pde
 Arduino side controller file for interfacing with Python
 Summer 2010
 Beryl Egerter, Sarah Johnson, Philip Aelion-Moss
 */


#include <Servo.h>      // include the servo library
#include "pitches.h"    // include the library of pitches

Servo servoMotor1;       // creates an instance of the servo object to control a servo
Servo servoMotor2;       
Servo servoMotors[] = {servoMotor1, servoMotor2};
float servoStop1 = 94.0;    // degree at which the servo motors stop 
float servoStop2 = 94.0;    // these values can be changed from the python interface
float servoStops[] = {servoStop1,servoStop2};
float originalStop = 94.0;  // keeps track of the original stopping value

int msg; // global variable for the Serial input

int pitches[255]; // Limited by the Serial cap at 1 byte.  This could be compensated
int noteLengths[255]; // for, but delaring arrays in this manner limits us to ~300 anyway
int placeInNoteArrays = 0; // Keeps track of where the next note will be placed

int servoPins[] = { 
  2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 }; // These pins can host servos or piezos
int analogPins[] = {
  14, 15, 16, 17, 18, 19 }; // These pins can be input or output LEDs
  
int sensorValue = 0;        // value read from analog input

void setup()
{
  Serial.begin( 9600 );         // set up the serial communications
  
  for (int i = 0; i < 12; i++) 
  {
    pinMode(servoPins[i], OUTPUT); // Sets these pins as digital (LED) output by default
  }
  
  for (int i = 0; i < 6; i++)
  {
    pinMode(analogPins[i], INPUT); // Sets the analog pins as input by default
  }
  
  // Yes, the following is bulky, but it is the best
  // way in Arduino to make the 2D array of notes 
  for(int i=0; i<NUMOCTAVES; i++)       
  {
    for(int j=0; j<NUMNOTES; j++)
    {
      if (i == 0){
      OCTAVES[i][j] = OCTAVE0[j];}
      if (i == 1){
      OCTAVES[i][j] = OCTAVE1[j];}
      if (i == 2){
      OCTAVES[i][j] = OCTAVE2[j];}
      if (i == 3){
      OCTAVES[i][j] = OCTAVE3[j];}
      if (i == 4){
      OCTAVES[i][j] = OCTAVE4[j];}
      if (i == 5){
      OCTAVES[i][j] = OCTAVE5[j];}
      if (i == 6){
      OCTAVES[i][j] = OCTAVE6[j];}
      if (i == 7){
      OCTAVES[i][j] = OCTAVE7[j];}
      if (i == 8){
      OCTAVES[i][j] = OCTAVE8[j];}
      if (i == 9){
      OCTAVES[i][j] = OCTAVE9[j];}
      if (i == 10){
      OCTAVES[i][j] = OCTAVE10[j]; }
    }
  }
  
}



void loop()
{
  // check if there is a message
  if (Serial.available() > 0) 
  {
    msg = Serial.read(); // reads one incoming byte:
    //Serial.println(msg);
    switch (msg)
    {
      
      case 120: // Sets an LED pin to HIGH or LOW
      {
        delay(1);
        int pinNum = Serial.read(); // Finds which pin we are turning on or off
        delay(1);
        boolean state = Serial.read(); // Finds if the pin is to be set to HIGH or LOW
        if (state) { 
          digitalWrite(pinNum, HIGH);
        }
        else { 
          digitalWrite(pinNum, LOW);
        }
        break;
      }
      
      // The following cases deal with servo motors
      
      case 121: // Turns an LED pin into a servo pin
      {
        delay(1);
        int servoNum = Serial.read();
        delay(1);
        int pinNum = Serial.read();
        servoMotors[servoNum-1].attach(pinNum);
        servoMotors[servoNum-1].write('^');
        break;
      }
   
      case 122: // Turns a servo pin into an LED pin
      {
        delay(1);
        int servoNum = Serial.read();
        servoMotors[servoNum-1].detach();
        break;
      }
      
      case 123: // Changes the speed of a servo motor
      {
        delay(1);
        int servoNum = Serial.read();
        delay(1);
        float servoSpeed = Serial.read();
        float servoSpeedChange = servoSpeed / 10.0;
        float servoRealSpeed;
        delay(1);
        int servoDir = Serial.read();
        if (servoDir == 1)
        {
          servoRealSpeed = servoStops[servoNum-1] - servoSpeedChange;
        }
        else
        {
          servoRealSpeed = servoStops[servoNum-1] + servoSpeedChange;
        }
        servoMotors[servoNum-1].write(servoRealSpeed);
        break;
      }
      
      case 124: // Changes the stopping speed of a servo motor
      {
        delay(1);
        int servoNum = Serial.read();
        delay(1);
        float servoSpeed = Serial.read();
        float servoStopSpeed = servoSpeed / 10.0;
        float servoNewStop;
        delay(1);
        int servoDir = Serial.read();
        if (servoDir == 1)
        {
          servoNewStop = servoStops[servoNum-1] - servoStopSpeed;
        }
        else
        {
          servoNewStop = servoStops[servoNum-1] + servoStopSpeed;
        }
        servoStops[servoNum-1] = servoNewStop;
        break;
      }
      
      case 125: // Restores the stopping speed of a servo motor to 94.0
      {
        delay(1);
        int servoNum = Serial.read();
        servoStops[servoNum-1] = originalStop;
        break;
      }
      
      // The following cases deal with piezo speakers
      
      case 126: // Plays a single note
      {
        delay(1);
        int numLen = Serial.read();
        delay(1);
        int denomLen = Serial.read();
        int noteLength = (numLen*1000)/(denomLen); //Converts the input note length into a fraction of a second.
        delay(1);
        int pinNum = Serial.read();
        delay(1);
        int octaveNum = Serial.read(); 
        delay(1);
        int noteNum = Serial.read();
        tone(pinNum, OCTAVES[octaveNum][noteNum], noteLength); // The command to play the specified tone.
        delay(noteLength*1.10); // Gives the tone time to be played. (Time given is the input length of the note plus 10% of that length more)
        noTone(pinNum); // Allows a tone to be played on a different pin later on.
        break;
      }
      
      case 127: // Adds a note to the pitches[] and noteLengths[] arrays
      {
        delay(1);
        int numLen = Serial.read();
        delay(1);
        int denomLen = Serial.read();
        int noteLength = (numLen*1000)/(denomLen); //Converts the input note length into a fraction of a second.
        delay(1);
        int octaveNum = Serial.read(); 
        delay(1);
        int noteNum = Serial.read();
        delay(1);
        int replace = Serial.read();
        
        if (replace > -1 && replace < placeInNoteArrays) // For replacing an existing note
        {
          pitches[replace] = OCTAVES[octaveNum][noteNum];
          noteLengths[replace] = noteLength;
        }
        else
        { 
          pitches[placeInNoteArrays] = OCTAVES[octaveNum][noteNum]; // For adding a new note
          noteLengths[placeInNoteArrays] = noteLength;
          placeInNoteArrays += 1;
        }
        Serial.print(1); // Tells the Python that a note has been added
        break;
      }
      
      case 128: // Plays the notes controlled by pitches[] and noteLengths[]
      {
        delay(1);
        int pinNum = Serial.read();
        for (int thisNote = 0; thisNote < placeInNoteArrays; thisNote++)
        {
          int pitch = pitches[thisNote];
          int noteLength = noteLengths[thisNote];
          tone(pinNum, pitch, noteLength);
          // to distinguish the notes, set a minimum time between them.
          // the note's duration + 30% works well:
          int pauseBetweenNotes = noteLength * 1.30;
          delay(pauseBetweenNotes);
        }
        noTone(pinNum);
        break;
      }
      
      case 129: //Clears the data in pitches[] and noteLengths[] and starts the note adder back at zero
      {
       for (int thisNote = 0; thisNote < placeInNoteArrays; thisNote++)
        {
          pitches[thisNote] = 0;
          noteLengths[thisNote] = 0; 
        } 
        placeInNoteArrays = 0;
        break; 
      }
      
      case 130: //Plays a single user-determined pitch
      {
        delay(1);
        int numLen = Serial.read();
        delay(1);
        int denomLen = Serial.read();
        int noteLength = (numLen*1000)/(denomLen); //Converts the input note length into a fraction of a second.        delay(50);
        int pinNum = Serial.read();
        delay(1);
        long pitchPart1 = Serial.read(); 
        delay(1);
        long pitchPart2 = Serial.read();
        delay(1);
        long pitchPart3 = Serial.read();
        delay(1);
        long pitch = (pitchPart3*10000) + (pitchPart2*100) + pitchPart1;
        tone(pinNum, pitch, noteLength); // The command to play the specified tone.
        delay(noteLength*1.10); // Gives the note time to be played. (Time given is the input length of the note plus 10% of that length more)
        noTone(pinNum); // Allows a tone to be played on a different pin later on.
        break;
      }
      
      case 131: // Adds a pitch to the pitches[] and noteLengths[] arrays
      {
        delay(1);
        int numLen = Serial.read();
        delay(1);
        int denomLen = Serial.read();
        int noteLength = (numLen*1000)/(denomLen); //Converts the input note length into a fraction of a second.        delay(50);
        delay(1);
        long pitchPart1 = Serial.read(); 
        delay(1);
        long pitchPart2 = Serial.read();
        delay(1);
        long pitchPart3 = Serial.read();
        long newPitch = (pitchPart3*10000) + (pitchPart2*100) + pitchPart1;
        delay(1);
        int replace = Serial.read();
        if (replace > -1 && replace < placeInNoteArrays) // For replacing an existing pitch
        {
          pitches[replace] = newPitch;
          noteLengths[replace] = noteLength;
        }
        else
        { 
          pitches[placeInNoteArrays] = newPitch; // For adding a new pitch
          noteLengths[placeInNoteArrays] = noteLength;
          placeInNoteArrays += 1;
        }
        Serial.print(1); // Tells the Python that a pitch has been added
        break;
      }
      
      // The following cases deal with analog inputs

      case 132: // Turns an analog pin into an input
      {
        delay(1);
        int pinNum = Serial.read();
        pinMode(pinNum, INPUT);
        break;
      }
      
      case 133: // Turns an analog pin into an output
      {
        delay(1);
        int pinNum = Serial.read();
        pinMode(pinNum, OUTPUT);
        break;
      }
      
      case 134: // Reading from analog pins without new lines
      {
        delay(1);
        int analogPin = Serial.read();
        sensorValue = analogRead(analogPin);
        Serial.print(sensorValue);
        break; 
      }
      
      case 135: // Reads from an analog pin with new lines
      {
        delay(1);
        int analogPin = Serial.read();
        sensorValue = analogRead(analogPin);
        Serial.println(sensorValue);
        break;
      }
      
      case 142: // Changes the speed of a servo motor
      {
        delay(1);
        int servoNum = Serial.read();
        servoNum = servoNum -1;
        if (servoNum != 1) { servoNum = 0; } // almost always zero
        delay(1);
        int servo_destination = Serial.read();
        delay(1);
        servoMotors[servoNum].write(servo_destination);
        break;
      }
      
      default:
      {
        delay(15);
        break;
      }
    }
    delay(3); //because otherwise Arduino gets ahead of itself sometimes
  }
  else delay(15);
  
}

