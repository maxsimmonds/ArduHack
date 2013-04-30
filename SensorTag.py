#!/usr/bin/env python
#
# Initially by Michael Saunby. April 2013
# Modified by Max Simmonds, Member of ArduHack!   
# 
# Notes.
# ~ Pexpect uses regular expression so characters that have special meaning
#   in regular expressions, e.g. [ and ] must be escaped with a backslash.
#
# ~ The main additions are added sensors, debugged and correct sensor output for use with our web server.
# ~ Run sendimg.py to send data and images to the server.

import pexpect
import os
import sys
import time
from sensor_calcs import *
import json

def floatfromhex(h):
    t = float.fromhex(h)
    if t > float.fromhex('7FFF'):
        t = -(float.fromhex('FFFF') - t)
        pass
    return t

class sensorTag: 

    def __init__( self, bluetooth_adr, path_to_gatttool):
	
	print("Preparing to connect, please press the side button...")
	time.sleep(1)							## Brief pause if this isn't the first instance it's run 
	os.system('hcitool lecc ' + bluetooth_adr)			## This stops the program running untill a connection is established
								
        self.con = pexpect.spawn(path_to_gatttool + 'gatttool -b ' + bluetooth_adr + ' --interactive') 
        self.con.expect('\[LE\]>')
        self.con.sendline('connect')
        # test for success of connect
        self.con.expect('\[CON\].*>')
        self.cb = {}
        return
    
    def char_write_cmd( self, handle, value ):
        # The 0%x for value is VERY naughty!  Fix this!
        cmd = 'char-write-cmd 0x%02x 0%x' % (handle, value)
        print cmd
        self.con.sendline( cmd )
        return
    
    def char_read_hnd( self, handle ):
        self.con.sendline('char-read-hnd 0x%02x' % handle)
        self.con.expect('descriptor: .* \r')
        after = self.con.after
        rval = after.split()[1:]
        return [long(float.fromhex(n)) for n in rval]

    # Notification handle = 0x0025 value: 9b ff 54 07
    def notification_loop( self ):
        while True:
            self.con.expect('Notification handle = .* \r')
            hxstr = self.con.after.split()[3:]
            #print hxstr[0],  [long(float.fromhex(n)) for n in hxstr[2:]]
            handle = long(float.fromhex(hxstr[0]))
            try:
                self.cb[handle]([long(float.fromhex(n)) for n in hxstr[2:]])
            except: 
                print "Error in callback for %x" % handle
                print sys.argv[1]
            pass
        pass
    
    def register_cb( self, handle, fn ):
        self.cb[handle]=fn;
        return


data = {}
datalog = sys.stdout

##### IR SENSOR #####
def tmp006(v):
    objT = (v[1]<<8)+v[0]
    ambT = (v[3]<<8)+v[2]

    targetT = calcTmpTarget(objT, ambT)

    data['IR Temp'] = targetT
    print "IR Temp:  %.1f" % targetT

##### ACCELEROMETER #####
def accel(v):
    (xyz,mag) = calcAccel(v[0],v[1],v[2])

    data['Acceleration (X,Y,Z): '] = xyz
    print "Acceleration (X,Y,Z): ", xyz

##### MAGNETOMETER #####
def magnet(v):
    magn = calcMagn(v[0])

    print "Magnetometer Value: ", magn
    data['Magnetometer Value: '] = magn

##### GYROSCOPE #####
def gyro(v):
    rot = calcGyro(v[0])

    print "Gyro Rotation: ", rot
    data['Gyro Rotation: '] = rot
						
    datalog.write(json.dumps(data) + "\n")	## Dump data to file
    datalog.flush()


######################################### MAIN #################################################################

def main():

    path_to_gatttool = "/home/pi/sensortag/bluez-5.3/attrib/"		### Full path to the edited gatttool
    global datalog

    bluetooth_adr = sys.argv[1]						## Bluetooth addr. taken from argument specified
    if len(sys.argv) > 2:
        datalog = open(sys.argv[2], 'w')


    tag = sensorTag(bluetooth_adr, path_to_gatttool)

    # enable IR sensor
    tag.register_cb(0x25,tmp006)			## data handle
    tag.char_write_cmd(0x29,0x01)			## data enabled
    tag.char_write_cmd(0x26,0x0100)			## data notification

    # enable accelerometer
    tag.register_cb(0x2d,accel)
    tag.char_write_cmd(0x31,0x01)
    tag.char_write_cmd(0x2e,0x0100)

    # enable magnetometer
    tag.register_cb(0x40,magnet)
    tag.char_write_cmd(0x44,0x01)
    tag.char_write_cmd(0x41,0x0100)

    # enable gyroscope
    tag.register_cb(0x57,gyro)
    tag.char_write_cmd(0x5B,0x07)
    tag.char_write_cmd(0x58,0x0100)

   # datalog.close()								## This enables data to be overwritten in file
    tag.notification_loop()
    

if __name__ == "__main__":
    main()
