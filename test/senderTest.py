import socket
import time
import struct
import sys 
sys.path.append("/home/mfl24/Documents/RNEL_GIT/haptic_environment_task_control")
import messageDefinitions as md
import Messenger as MR
from ctypes import * 
import msgpackrpc
import Globals
import numpy as np
from threading import Thread 
"""
trialFailed = False
def listener():
  print("Listener thread started")
  while True:
    data, addr = Globals.getListenerSocket().recvfrom(md.MAX_PACKET_LENGTH)
    header = md.MSG_HEADER()
    MR.readMessage(data, header)
    if header.msg_type == md.HAPTIC_DATA_STREAM:
      msg_data = md.M_HAPTIC_DATA_STREAM()
      MR.readMessage(data, msg_data)
      Globals.CHAI_DATA = msg_data
    time.sleep(0.0001)

def ballPosListener():
  print("ball thread started")
  while True:
    data, addr = Globals.getListenerSocket().recvfrom(md.MAX_PACKET_LENGTH)
    header = md.MSG_HEADER()
    MR.readMessage(data, header)
    if header.msg_type == md.CUPS_DATA:
      msg_data = md.M_CUPS_DATA()
      MR.readMessage(data, msg_data)
      if msg_data.ballPos > 45 or msg_data.ballPos < -45:
        global trialFailed
        trialFailed = True
    time.sleep(0.0001)


def collideWith(xMin, xMax, yMin, yMax):
  if xMin <= Globals.CHAI_DATA.posY <= xMax and yMin <= Globals.CHAI_DATA.posZ <= yMax:
    return True 
  return False
"""
client = Globals.getClient()
client.call("addModule", 2, "127.0.0.1", Globals.PORT)
client.call("subscribeTo", 2, 1)
time.sleep(10)

#listenerThread = Thread(target=listener)
#listenerThread.daemon = True
#listenerThread.start()
#time.sleep(10)
#ballThread = Thread(target=ballPosListener)
#ballThread.daemon = True 
#ballThread.start()
#time.sleep(10)
#testPacket = md.M_TEST_PACKET()
#testPacket.header.msg_type = md.TEST_PACKET
#testPacket.a = c_int(10)
#testPacket.b = c_int(-1)
#print(testPacket.header.msg_type)
#testPacket = bytes(MR.makeMessage(testPacket))
#print(len(testPacket))
#client.call("sendMessage", testPacket, len(testPacket), 1)


cups = md.M_CUPS_CREATE()
cups.header.msg_type = md.CUPS_CREATE
name = create_string_buffer(b"cups", md.MAX_STRING_LENGTH)
namePtr = (c_char_p) (addressof(name))
cups.cupsName = namePtr.value
cups.escapeAngle = c_double(35)
cups.pendulumLength = c_double(10.0)
cups.ballMass = c_double(1)
cups.cartMass = c_double(1)
packet = MR.makeMessage(cups)
MR.sendMessage(packet)

time.sleep(10)

cupsStart = md.M_CUPS_START()
cupsStart.header.msg_type = md.CUPS_START 
name = create_string_buffer(b"cups", md.MAX_STRING_LENGTH)
namePtr = (c_char_p) (addressof(name))
cupsStart.cupsName = namePtr.value
packet = MR.makeMessage(cupsStart)
MR.sendMessage(packet)

"""
#ballThread.start()
trialNum = 1
minTimes = []
while trialNum <= 100:
  trialFailed = False
  print(trialNum, trialFailed) 
  # Move to start area
  while collideWith(-120, -80, -10, 10) == False:
    continue

  startTime = time.time()
  cupsStart = md.M_CUPS_START()
  cupsStart.header.msg_type = md.CUPS_START 
  name = create_string_buffer(b"cups", md.MAX_STRING_LENGTH)
  namePtr = (c_char_p) (addressof(name))
  cupsStart.cupsName = namePtr.value
  packet = MR.makeMessage(cupsStart)
  MR.sendMessage(packet)

  while collideWith(70, 130, -10, 10) == False:
    if trialFailed == True:
      print("trialFailed")
      break
    continue 
  
  stopTime = time.time()
  if trialFailed == False:
    trialNum = trialNum + 1
    minTimes.append(stopTime-startTime)
    print("Trial succeeded", stopTime-startTime)
  cupsStop = md.M_CUPS_STOP()
  cupsStop.header.msg_type = md.CUPS_STOP 
  name = create_string_buffer(b"cups", md.MAX_STRING_LENGTH)
  namePtr = (c_char_p) (addressof(name))
  cupsStop.cupsName = namePtr.value 
  packet = MR.makeMessage(cupsStop)
  MR.sendMessage(packet)

testCrap = np.save("/home/mfl24/Documents/cupsTest.npy", minTimes)
"""
