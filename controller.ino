/************************************************************************

  Test of Pmod TC1
  https://www.electromaker.io/project/view/measure-and-display-the-ambient-temperature-with-digilent-pm

*************************************************************************

  Description: Pmod_TC1
  The ambient temperature (in and ° C) is displayed in the serial monitor.

  Material
  1. Arduino Uno
  2. Pmod TC1 (download library
  https://github.com/adafruit/Adafruit-MAX31855-library)
  

  Wiring
  Module <----------> Arduino
  VCC     to          3V3
  GND     to          GND
  SCK     to          13
  MISO    to          12
  CS      to          10
  
  a logic level converter must be used!!!

************************************************************************/

#define CS 10 //chip select pin

// Call of libraries
#include <SPI.h>
#include <Adafruit_MAX31855.h>

Adafruit_MAX31855 thermocouple(CS); // Creation of the object

void setup()
{
  Serial.begin(38400); // initialization of serial communication
  thermocouple.begin();  //initialize senzor
}

void loop()
{
  delay(250); //wait one second
  Serial.println(thermocouple.readCelsius()); // Acquisition of temperature in degrees  Celsius
}
