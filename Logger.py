import messageDefinitions as md
import msgpackrpc
import socket 
import Globals 
import Messenger as MR 
import os 
from threading import Thread
import time 
import json 
import platform 
import sys 

def loggerFunction(saveInfo):
  client = Globals.getClient() 
  client.call("addModule", 3, Globals.LOGGER_IP, Globals.LOGGER_PORT)
  client.call("subscribeTo", 3, 999)
  saveFilePrefix = saveInfo["saveFilePrefix"]
  saveConfig = {}
  filePtrs = []
  for fileToSave in saveInfo.keys():
    if fileToSave != "saveFilePrefix":
      fullFilePath = saveFilePrefix + "_" + fileToSave
      if not os.path.isfile(fullFilePath):
        f = open(fullFilePath, 'ab')
        for msgType in saveInfo[fileToSave]:
          saveConfig[msgType] = f
          filePtrs.append(f) 


  running = True
  logging = False
  msgsReceived = 0
  while running == True:
    data, addr = Globals.getLoggerSocket().recvfrom(md.MAX_PACKET_LENGTH)
    header = md.MSG_HEADER()
    MR.readMessage(data, header)
    if header.msg_type == md.START_RECORDING:
      print("Starting Recording")
      logging = True
    elif header.msg_type == md.STOP_RECORDING:
      logging = False
      running = False
      print("Stopping Recording")
    elif header.msg_type == md.PAUSE_RECORDING:
      logging = False
    elif header.msg_type == md.RESUME_RECORDING:
      logging = True 
    
    if logging == True and header.msg_type in saveConfig.keys():
      filePtr = saveConfig[header.msg_type]
      filePtr.write(data)
      msgsReceived = msgsReceived + 1
    if msgsReceived > 100:
      for f in filePtrs:
        f.flush()
      msgsReceived = 0
    time.sleep(0.0001)
  for f in filePtrs:
    for f in filePtrs:
      if f.closed == False:
        f.flush()
        f.close()

#if __name__ == "__main__":
#  config = json.load(open("/home/mfl24/Documents/chaiProjects/hapticEnvironment_TrialControl/trialConfig/cstConfig.json"))
#  saveConfig = config["save_params"]
#  saveConfig["saveFilePrefix"] = "/home/mfl24/data/RnelShare/users/mfl24/Test/JunkTest/test1"
#  myLogger = Logger(Globals.LOGGER_IP, Globals.LOGGER_PORT, saveConfig)
#  myLogger.logThread.start()

