## State machine for task control
import importlib.util
import warnings  
import socket
import time
import messageDefinitions as md
import Messenger as MR
from ctypes import *
from threading import Thread
import struct 
import json
import Globals
import os 
from multiprocessing import Process 
import random 
from State import *
import sys  
sys.path.append(Globals.UTILS_PATH)
import haptics
import graphics
import msgUtils 

class StateMachine(object):
  def __init__(self, configFile, saveFilePrefix):
    config = json.load(open(configFile))
    self.running = False 
    self.stopped = True
    self.build(config, saveFilePrefix)
    
  # Build should return the start state of the StateMachine
  def build(self, config, saveFilePrefix):
    self.name = config["name"]
    self.stateNameList = config["states"]
    self.taskVars = config["taskVars"]
    del config["taskVars"]
    self.config = config
    self.transitionTable = {}
    self.states = {}
    self.currentState = self.config["startState"]
    
    for startupMsgs in self.config["setup_msg"]:
      msgUtils.makeMessage(startupMsgs)  

    for stateName in self.stateNameList:
      stateDict = config[stateName]
      stateType = stateDict["type"]
      stateTransitions = stateDict["transitions"]
      stateGraphics = stateDict["graphics"]
      stateHaptics = stateDict["haptics"]
      StateConstructor = getattr(sys.modules[__name__], stateType)
      state = StateConstructor(stateName, stateTransitions, stateGraphics, stateHaptics)
      for g in stateGraphics.keys():
        objectDict = stateGraphics[g]
        graphics.makeObject(g, objectDict["shape"], objectDict["size"],\
                            objectDict["color"], objectDict["position"])
      for transitionSymbol in stateTransitions.keys():
        self.transitionTable[(stateName, transitionSymbol)] = stateTransitions[transitionSymbol]
      self.states[stateName] = state
    time.sleep(0.5)

  def run(self):
    self.running = True
    self.stopped = False
    self.paused = False
    while self.currentState != "end" and self.running == True:
      if self.paused == True:
        continue
      currentState = self.states[self.currentState]
      transition = currentState.entry(self.currentState, self)
      #print(self.currentState, transition)
      nextStates = self.transitionTable[(self.currentState, transition)]
      if len(nextStates) > 1:
        nextState = random.choice(nextStates)
      else:
        nextState = nextStates[0]
      if nextState == "end":
        return transition
      self.currentState = nextState
    for endMessages in self.config["end_msg"]:
      msgUtils.makeMessage(endMessages)
    self.stopped = True
    return "done"
  

if __name__ == "__main__":
  taskConfig = sys.argv[1]
  taskSM = StateMachine(taskConfig, "")
  taskSM.run()

