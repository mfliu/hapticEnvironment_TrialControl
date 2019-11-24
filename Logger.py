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
from datetime import date 
import struct 
sys.path.append("utils/")
import msgUtils 
import itertools 
import pymongo 

def loggerFunction(saveInfo, emgRecord, mocapRecord, sessionInfo):
  client = Globals.getClient() 
  client.call("addModule", 3, Globals.LOGGER_IP, Globals.LOGGER_PORT)
  client.call("subscribeTo", 3, 999)
  saveFilePrefix = saveInfo["saveFilePrefix"]
  
  ## MDF Integration
  pymongoClient = pymongo.MongoClient(Globals.PYMONGO_IP, Globals.PYMONGO_PORT)
  database = pymongoClient[Globals.PYMONGO_DATABASE]
  collection = database[Globals.PYMONGO_COLLECTION]
  saveTypes = list(itertools.chain.from_iterable(list(saveInfo.values())))
  ## 

  if mocapRecord == True:
    mocapClient, mocapSocket = Globals.getMocapClient()
  if emgRecord == True:
    emgCommandSocket = Globals.getEMGCommand()
    emgStreamSocket = Globals.getEMGStream()
    emgCommandSocket.sendall(b'TRIGGER START\r\n\r\n')
  
  running = True
  logging = False
  msgsReceived = 0
  trialNum = 1
  while running == True:
    data, addr = Globals.getLoggerSocket().recvfrom(md.MAX_PACKET_LENGTH)
    header = md.MSG_HEADER()
    MR.readMessage(data, header)      
    if header.msg_type == md.TRIAL_START:
      trialStartMsg = md.M_TRIAL_START()
      MR.readMessage(data, trialStartMsg)
      trialNum = trialStartMsg.trialNum
      subjectName = sessionInfo["subjectName"]
      sessionNum = sessionInfo["sessionNum"]
      taskName = sessionInfo["taskName"]
      experimentDate = date.today().strftime("%m-%d-%Y")
      ## MDF Integration
      hapticDataDoc = {"subjectName": subjectName,\
                       "experimentDate": experimentDate,\
                       "sessionNum": sessionNum,\
                       "taskName": taskName,\
                       "trialNum": trialNum,\
                       "posX": [], "posY": [], "posZ": [], \
                       "velX": [], "velY": [], "velZ": [], \
                       "forceX": [], "forceY": [], "forceZ": [],\
                       "time":[], "serial_no":[]}
      if md.CST_DATA in saveTypes:
        cstDataDoc = {"subjectName": subjectName,\
                       "experimentDate": experimentDate,\
                       "sessionNum": sessionNum, \
                       "taskName": taskName,\
                       "trialNum": trialNum,\
                       "cursorX": [], "cursorY": [], "cursorZ": [], \
                       "time":[], "serial_no":[]}
      ### 

      saveConfig = {}
      filePtrs = []
      for fileToSave in saveInfo.keys():
        if fileToSave != "saveFilePrefix":
          fullFilePath = saveFilePrefix + "_" + fileToSave + "_Trial{:03d}".format(trialNum) + ".data"
          if not os.path.isfile(fullFilePath):
            f = open(fullFilePath, 'ab')
          for msgType in saveInfo[fileToSave]:
            saveConfig[msgType] = f
            filePtrs.append(f) 
      if mocapRecord == True:
        mocapFile = saveFilePrefix + "_mocap_Trial{:03d}".format(trialNum) 
        mocapClient.sendCommand(2, "SetRecordTakeName " + mocapFile, mocapSocket, (Globals.MOCAP_IP, Globals.MOCAP_PORT))
        mocapClient.sendCommand(2, "StartRecording", mocapSocket, (Globals.MOCAP_IP, Globals.MOCAP_PORT))
      if emgRecord == True:
        ## MDF Integration
        emgDicts = [{"emgChannel": x+1, "emgData":[]} for x in range(0, 10)]
        ##

        emgFile = saveFilePrefix + "_emg_Trial{:03d}".format(trialNum)
        emgFilePtr = open(emgFile, 'ab')
      logging = True
      print("LOGGER: Starting Recording")
    if header.msg_type == md.TRIAL_END:
      ## MDF Integration
      collection.insert_one(hapticDataDoc)
      if md.CST_DATA in saveTypes: 
        collection.insert_one(cstDataDoc)
      ## 

      if mocapRecord == True:
        mocapClient.sendCommand(2, "StopRecording", mocapSocket, (Globals.MOCAP_IP, Globals.MOCAP_PORT))
      if emgRecord == True:
        ## MDF Integration 
        for emgChannel in emgDicts:
          emgChannel["subjectName"] = subjectName
          emgChannel["experimentDate"] = experimentDate
          emgChannel["sessionNum"] = sessionNum
          emgChannel["taskName"] = taskName
          emgChannel["trialNum"] = trialNum
          collection.insert_one(emgChannel)
        ## 

        emgFilePtr.flush()
        emgFilePtr.close()
      logging = False
      #trialNum = trialNum + 1
      print("LOGGER: Stopping Recording")
    elif header.msg_type == md.SESSION_END:
      logging = False
      running = False
      if emgRecord == True:
        emgCommandSocket = Globals.getEMGCommand()
        emgCommandSocket.sendall(b'TRIGGER STOP\r\n\r\n')
    elif header.msg_type == md.PAUSE_RECORDING:
      logging = False
    elif header.msg_type == md.RESUME_RECORDING:
      logging = True 
    elif header.msg_type == md.STOP_RECORDING:
      logging = False
      running = False
    if logging == True and header.msg_type in saveConfig.keys():
      ## MDF Integration 
      if header.msg_type == md.HAPTIC_DATA_STREAM:
        hapticDataDoc["time"].append(header.timestamp)
        hapticDataDoc["serial_no"].append(header.serial_no)
        hapticData = md.M_HAPTIC_DATA_STREAM()
        MR.readMessage(data, hapticData)
        hapticDataDoc["posX"].append(hapticData.posX)
        hapticDataDoc["posY"].append(hapticData.posY)
        hapticDataDoc["posZ"].append(hapticData.posZ) 
        hapticDataDoc["velX"].append(hapticData.velX) 
        hapticDataDoc["velY"].append(hapticData.velY) 
        hapticDataDoc["velZ"].append(hapticData.velZ)
        hapticDataDoc["forceX"].append(hapticData.forceX)
        hapticDataDoc["forceY"].append(hapticData.forceY)
        hapticDataDoc["forceZ"].append(hapticData.forceZ)
      elif header.msg_type == md.CST_DATA:
        cstDataDoc["time"].append(header.timestamp)
        cstDataDoc["serial_no"].append(header.serial_no)
        cstData = md.M_CST_DATA()
        MR.readMessage(data, cstData)
        cstDataDoc["cursorX"].append(cstData.cursorX)
        cstDataDoc["cursorY"].append(cstData.cursorY)
        cstDataDoc["cursorZ"].append(cstData.cursorZ)
      else:
        msgDict = msgUtils.messageToDict(data) 
        msgDict["subjectName"] = subjectName
        msgDict["experimentDate"] = experimentDate
        msgDict["taskName"] = taskName
        msgDict["sessionNum"] = sessionNum
        msgDict["trialNum"] = trialNum
        collection.insert_one(msgDict)
      ## 

      filePtr = saveConfig[header.msg_type]
      filePtr.write(data)
      if emgRecord == True:
        emgData = emgStreamSocket.recv(64)
        emgFilePtr.write(emgData)
        ## MDF Integration 
        emgArray = struct.unpack("<16f", emgData)
        for eIdx in range(0, len(emgDicts)):
          emgDicts[eIdx]["emgData"].append(emgArray[eIdx])
        ## 
      msgsReceived = msgsReceived + 1
    if msgsReceived > 100:
      for f in filePtrs:
        f.flush()
      msgsReceived = 0
    #time.sleep(0.001)
  print("Stopped Recording")
  for f in filePtrs:
    for f in filePtrs:
      if f.closed == False:
        f.flush()
        f.close()
  print("Files closed")

#if __name__ == "__main__":
#  config = json.load(open("/home/mfl24/Documents/chaiProjects/hapticEnvironment_TrialControl/trialConfig/cstConfig.json"))
#  saveConfig = config["save_params"]
#  saveConfig["saveFilePrefix"] = "/home/mfl24/data/RnelShare/users/mfl24/Test/JunkTest/test1"
#  myLogger = Logger(Globals.LOGGER_IP, Globals.LOGGER_PORT, saveConfig)
#  myLogger.logThread.start()

