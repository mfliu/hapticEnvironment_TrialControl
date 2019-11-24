from abc import ABC, abstractmethod, abstractproperty
from ctypes import *
import struct 
import time
import sys
import numpy as np 
import math 

import Globals 
import messageDefinitions as md
import Messenger as MR
sys.path.append(Globals.UTILS_PATH)
import haptics
import graphics

class State(ABC):
  @abstractmethod
  def __init__(self, name, transitions, graphicObjs, hapticObjs):
    self.name = name 
    self.transitions = transitions 
    self.graphicObjs = graphicObjs
    self.hapticObjs = hapticObjs

  @abstractmethod
  def entry(self):
    pass
  
  def enableStateObjs(self, sm):
    for gKey in self.graphicObjs:
      graphics.enableGraphics(gKey, 1)
    for hKey in self.hapticObjs:
      haptics.enableHaptics(hKey, self.hapticObjs[hKey], 1, sm)

  def disableStateObjs(self, sm):
    for gKey in self.graphicObjs:
      graphics.enableGraphics(gKey, 0)
    for hKey in self.hapticObjs:
      haptics.enableHaptics(hKey, self.hapticObjs[hKey], 0, sm)

class EmptyState(State):
  def __init__(self, name, transitions, graphicObjs, hapticObjs):
    super(EmptyState, self).__init__(name, transitions, graphicObjs, hapticObjs)

  def entry(self, name, sm):
    waitTime = sm.config[name]["waitTime"]
    start = time.time()
    while (time.time() - start) <= waitTime:
      continue
    return "done"

class ReachState(State):
  def __init__(self, name, transitions, graphicObjs, hapticObjs):
    super(ReachState, self).__init__(name, transitions, graphicObjs, hapticObjs)

  def entry(self, name, sm):
    self.enableStateObjs(sm)
    startTime = time.time()
    timeLimit = sm.config[name]["timeLimit"]
    while (time.time() - startTime) < timeLimit:
      if haptics.collidingWith(self.name) == True:
        self.disableStateObjs
        if sm.taskVars["updateState"] == name:
          sm.taskVars["taskControl"].addNode()
        return "success"
    graphics.changeColor(self.name, 1.0, 0.0,0.0, 1.0)
    self.disableStateObjs(sm)
    return "fail"

class ReachHoldState(State):
  def __init__(self, name, transitions, graphicObjs, hapticObjs):
    super(ReachHoldState, self).__init__(name, transitions, graphicObjs, hapticObjs)

  def entry(self, name, sm):
    self.enableStateObjs(sm)
    startTime = time.time()
    holdLength = sm.config[name]["holdLength"]
    timeLimit = sm.config[name]["timeLimit"]
    objectName = sm.config[name]["targetObjectName"]
    objectDict = sm.config[name]["graphics"][objectName]
    objectColor = objectDict["color"]
    graphics.changeColor(objectName, objectColor[0], objectColor[1], objectColor[2], objectColor[3])
    while haptics.collide2D(objectDict) == False:
      if time.time()-startTime > timeLimit:
        graphics.changeColor(objectName, 1.0, 0.0, 0.0, 1.0)
        time.sleep(0.1)
        if sm.taskVars["updateState"] == name:
          sm.taskVars["taskControl"].addNode()
        self.disableStateObjs(sm)
        return "fail"
    holdStart = time.time()
    while time.time()-holdStart < holdLength:
      if not haptics.collide2D(objectDict):
        graphics.changeColor(objectName, 1.0, 0.0, 0.0, 1.0)
        time.sleep(0.1)
        if sm.taskVars["updateState"] == name:
          sm.taskVars["taskControl"].addNode()
        self.disableStateObjs(sm)
        return "fail"
    time.sleep(0.1)
    if sm.taskVars["updateState"] == name:
      sm.taskVars["taskControl"].addNode()
    self.disableStateObjs(sm)
    return "success"

class CSTRunningState(State):
  def __init__(self, name, transitions, graphicObjs, hapticObjs):
    super(CSTRunningState, self).__init__(name, transitions, graphicObjs, hapticObjs)
  
  def startCST(self):
    cstStart = md.M_CST_START()
    cstStart.header.msg_type = md.CST_START 
    name = create_string_buffer(b"cst", md.MAX_STRING_LENGTH)
    namePtr = (c_char_p) (addressof(name))
    cstStart.cstName = namePtr.value
    packet = MR.makeMessage(cstStart)
    MR.sendMessage(packet)

  def stopCST(self):
    cstStop = md.M_CST_STOP()
    cstStop.header.msg_type = md.CST_STOP 
    name = create_string_buffer(b"cst", md.MAX_STRING_LENGTH)
    namePtr = (c_char_p) (addressof(name))
    cstStop.cstName = namePtr.value
    packet = MR.makeMessage(cstStop)
    MR.sendMessage(packet)

  def setLambda(self, lambdaVal):
    cst = md.M_CST_SET_LAMBDA()
    cst.header.msg_type = md.CST_SET_LAMBDA 
    name = create_string_buffer(b"cst", md.MAX_STRING_LENGTH)
    namePtr = (c_char_p) (addressof(name))
    cst.cstName = namePtr.value
    cst.lambdaVal = lambdaVal
    packet = MR.makeMessage(cst)
    MR.sendMessage(packet)

  def entry(self, name, sm):
    graphics.changeColor("center", 0.83, 0.83, 0.83, 1.0)

    sm.taskVars["trialNum"] = sm.taskVars["trialNum"] + 1   
    sm.taskVars["running"] = 1
    sm.taskVars["trialSucceeded"] = 1
    
    self.startCST()  
    startTime = time.time()
    while (time.time() - startTime) <= 6.0:
      if sm.taskVars["trialSucceeded"] == 0:
        break
      time.sleep(0.001)
    self.stopCST()
    
    if sm.taskVars["trialSucceeded"] == 0:  
      graphics.changeColor("center", 1.0, 0.0, 0.0, 1.0)
      sm.taskVars["total_success"].append(0)
    elif sm.taskVars["trialSucceeded"] == 1:
      sm.taskVars["total_success"].append(1)

    prevSuccess = float(sum(sm.taskVars["total_success"][-100:])/len(sm.taskVars["total_success"][-100:]))
    sm.taskVars["proportionSuccess"] = round(prevSuccess, 2)
    if prevSuccess >= 0.8:
      sm.taskVars["lambda"] = round(sm.taskVars["lambda"] + 0.1, 2)
      sm.taskVars["total_success"] = []
    if sm.taskVars["updateState"] == name:
      sm.taskVars["taskControl"].addNode()
    time.sleep(0.1)
    return "next"

class PassivePerturbationState(State):
  def __init__(self, name, transitions, graphicObjs, hapticObjs):
    super(PassivePerturbationState, self).__init__(name, transitions, graphicObjs, hapticObjs)

  def entry(self, name, sm):
    self.enableStateObjs(sm)
    forceFieldName = list(sm.config[name]["haptics"].keys())[0]
    if sm.taskVars[forceFieldName] == 0:
      if forceFieldName == "field1Force":
        timeToBump = np.sqrt(2*sm.taskVars["bumpDistance"]/sm.taskVars["field2Force"])
      elif forceFieldName == "field2Force":
        timeToBump = np.sqrt(2*sm.taskVars["bumpDistance"]/sm.taskVars["field1Force"])
    else:
      timeToBump = np.sqrt(2*sm.taskVars["bumpDistance"]/sm.taskVars[forceFieldName])
    timeToBump = round(timeToBump, 2)
    time.sleep(math.ceil(timeToBump))
    self.disableStateObjs(sm)
    return "done"

class DecisionState(State):
  def __init__(self, name, transitions, graphicObjs, hapticObjs):
    super(DecisionState, self).__init__(name, transitions, graphicObjs, hapticObjs)

  def entry(self, name, sm):
    self.enableStateObjs(sm)
    object1Name = sm.config[name]["object1Name"]
    object2Name = sm.config[name]["object2Name"]
    object1Dict = sm.config[name]["graphics"][object1Name]
    object2Dict = sm.config[name]["graphics"][object2Name]
    decisionMade = False
    while decisionMade == False:
      if haptics.collide2D(object1Dict) == True:
        decisionMade = True 
        decision = object1Name 
        sm.taskVars["decision"] = 1
      if haptics.collide2D(object2Dict) == True:
        decisionMade = True 
        decision = object2Name 
        sm.taskVars["decision"] = 2
    if sm.taskVars["updateState"] == name:
      sm.taskVars["trialNum"] = sm.taskVars["trialNum"] + 1
      sm.taskVars["taskControl"].addNode()
    self.disableStateObjs(sm)
    return decision
