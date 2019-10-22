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

class Logger:
  def __init__(self, SET_IPADDR, SET_PORT, saveInfo):
    self.client = msgpackrpc.Client(msgpackrpc.Address(Globals.RPC_IP, Globals.RPC_PORT))
    self.IPADDR = SET_IPADDR 
    self.PORT = SET_PORT
    self.client.call("addModule", 3, self.IPADDR, self.PORT)
    self.client.call("subscribeTo", 3, 999)

    self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if platform.system() == "Linux":
      self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    self.socket.bind((self.IPADDR, self.PORT))
    self.running = True
    self.logging = False 
    self.logThread = Thread(target = self.loggerThread)
    self.logThread.daemon = True
    
    self.saveFilePrefix = saveInfo["saveFilePrefix"]
    self.saveConfig = {}
    self.filePtrs = []
    for fileToSave in saveInfo.keys():
      if fileToSave != "saveFilePrefix":
        fullFilePath = self.saveFilePrefix + "_" + fileToSave
        if not os.path.isfile(fullFilePath):
          f = open(fullFilePath, 'ab')
          for msgType in saveInfo[fileToSave]:
            self.saveConfig[msgType] = f
            self.filePtrs.append(f) 

  def addMsgSave(self, msgType, filePath):
    fullFilePath = self.saveFilePrefix + "_" + filePath
    for f in self.filePtrs:
      if f.name == fullFilePath:
        self.saveConfig[msgType] = f
        return 
    f = open(fullFilePath, 'ab')
    self.filePtrs.append(f)
    self.saveConfig[msgType] = f
    return 
    
  def startLogging(self):
    self.running = True 
    self.logThread.start()

  def loggerThread(self):
    self.running = True
    msgsReceived = 0
    while self.running == True:
      data, addr = self.socket.recvfrom(md.MAX_PACKET_LENGTH)
      header = md.MSG_HEADER()
      MR.readMessage(data, header)
      msgsReceived = msgsReceived + 1
      if header.msg_type == md.START_RECORDING:
        self.logging = True
      elif header.msg_type == md.STOP_RECORDING:
        self.logging = False
      elif header.msg_type == md.SESSION_END:
        self.running = False
        for f in self.filePtrs:
          f.close()
      if self.logging == True and header.msg_type in self.saveConfig.keys():
        filePtr = self.saveConfig[header.msg_type]
        filePtr.write(data)
      if msgsReceived > 100:
        for f in self.filePtrs:
          f.flush()
        msgsReceived = 0
      time.sleep(0.001)

#if __name__ == "__main__":
#  config = json.load(open("/home/mfl24/Documents/chaiProjects/hapticEnvironment_TrialControl/trialConfig/cstConfig.json"))
#  saveConfig = config["save_params"]
#  saveConfig["saveFilePrefix"] = "/home/mfl24/data/RnelShare/users/mfl24/Test/JunkTest/test1"
#  myLogger = Logger(Globals.LOGGER_IP, Globals.LOGGER_PORT, saveConfig)
#  myLogger.logThread.start()

