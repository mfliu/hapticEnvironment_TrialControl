import sys 
import numpy as np
import messageDefinitions as md
from ctypes import *
import Messenger as MR
import Globals 
sys.path.append(Globals.HOME_PATH)
import struct 

def enableHaptics(effectName, effectDetails, setVal, sm):
  effectType = effectDetails["effectType"]
  effectFunction = effectDetails["function"]
  isGlobalEffect = effectDetails["globalEffect"]
  if setVal == 1 and isGlobalEffect == False:
    makeEffect(effectName, effectType, effectFunction, sm) 
  if setVal == 0 and isGlobalEffect == False:
    removeEffect(effectName)

def makeEffect(effectName, effectType, effectFunction, sm):
  if effectType == "viscousField":
    globals()[effectFunction](effectName, sm)
    viscosityMatrix = [0.0, 0.0, 0.0,\
                      0.0, sm.taskVars[effectName], 0.0,\
                      0.0, 0.0, 0.0]
    viscousField(effectName, viscosityMatrix)
  elif effectType == "constantForceField":
    globals()[effectFunction](effectName, sm)
    magnitude = sm.taskVars[effectName]
    direction = sm.taskVars["direction"]
    constantForceField(effectName, direction, magnitude)
    
def enableEffect(effectName, setEnabled):
  effect = md.M_HAPTICS_SET_ENABLED_WORLD()
  effect.header.msg_type = c_int(md.HAPTICS_SET_ENABLED_WORLD)
  name = create_string_buffer(bytes(effectName, 'utf-8'), md.MAX_STRING_LENGTH)
  namePtr = (c_char_p) (addressof(name))
  effect.effectName = namePtr.value 
  effect.enabled = setEnabled
  packet = MR.makeMessage(effect)
  MR.sendMessage(packet)
  return packet

def removeEffect(effectName):
  rmField = md.M_HAPTICS_REMOVE_WORLD_EFFECT()
  rmField.header.msg_type = c_int(md.HAPTICS_REMOVE_WORLD_EFFECT)
  name = create_string_buffer(bytes(effectName, 'utf-8'), md.MAX_STRING_LENGTH)
  namePtr = (c_char_p) (addressof(name))
  rmField.effectName = namePtr.value
  packet = MR.makeMessage(rmField)
  MR.sendMessage(packet)  
  return packet 

def chooseForceJND(effectName, sm):
  if effectName == "field2Force":
    return
  
  baseForce = np.array(sm.taskVars["baseForce"])
  prevDiff = sm.taskVars["field1Force"] - sm.taskVars["field2Force"]
  prevDecision = sm.taskVars["decision"]
  
  if prevDecision == -1:
    newDiff = 0.5 # start at a 0.5 difference in viscosities
  elif (prevDecision == 2 and prevDiff < 0) or (prevDecision == 1 and prevDiff > 0) :
    # Correct 
    newDiff = np.abs(prevDiff) - 0.1 # Compute new difference 
    if newDiff < 0: # Let's make 0.1 the smallest difference if nonzero
      newDiff = 0.1
  else:
    # Wrong
    newDiff = np.abs(prevDiff) + 0.1 
  
  addOrSubtract = np.random.choice(["add", "subtract"])
  if addOrSubtract == "add":
    force1 = np.random.choice(baseForce)
    force2 = force1 + newDiff 
  elif addOrSubtract == "subtract":
    # never let any viscosity be less than 0
    force1 = np.random.choice(baseForce[np.where(baseForce-newDiff >= 0)])
    force2 = force1 - newDiff 
  forceArray = [round(force1, 2), round(force2, 2)]
  np.random.shuffle(forceArray)
  sm.taskVars["field1Force"] = forceArray[0] 
  sm.taskVars["field2Force"] = forceArray[1]
  sm.taskVars["direction"] = np.random.choice(sm.taskVars["possibleDirections"])

def freezeTool(name):
  freeze = md.M_HAPTICS_FREEZE_EFFECT()
  freeze.header.msg_type = c_int(md.HAPTICS_FREEZE_EFFECT)
  freezeName = create_string_buffer(bytes(name, 'utf-8'), md.MAX_STRING_LENGTH)
  freezeNamePtr = (c_char_p) (addressof(freezeName))
  freeze.effectName = freezeNamePtr.value
  packet = MR.makeMessage(freeze)
  MR.sendMessage(packet)
  return packet 

def unfreezeTool(name):
  unfreeze = md.M_HAPTICS_REMOVE_WORLD_EFFECT()
  unfreeze.header.msg_type = c_int(md.HAPTICS_REMOVE_WORLD_EFFECT)
  freezeName = create_string_buffer(bytes(name, 'utf-8'), md.MAX_STRING_LENGTH)
  freezeNamePtr = (c_char_p) (addressof(freezeName))
  unfreeze.effectName = freezeNamePtr.value 
  packet = MR.makeMessage(unfreeze)
  MR.sendMessage(packet)
  return packet

def constantForceField(name, direction, magnitude):
  field = md.M_HAPTICS_CONSTANT_FORCE_FIELD()
  field.header.msg_type = c_int(md.HAPTICS_CONSTANT_FORCE_FIELD)
  fieldName = create_string_buffer(bytes(name, 'utf-8'), md.MAX_STRING_LENGTH)
  fieldNamePtr = (c_char_p) (addressof(fieldName))
  field.effectName = fieldNamePtr.value 
  field.direction = c_double(direction)
  field.magnitude = c_double(magnitude) 
  packet = MR.makeMessage(field)
  MR.sendMessage(packet)
  return packet 

def viscousField(name, viscMatrix):
  field = md.M_HAPTICS_VISCOSITY_FIELD()
  field.header.msg_type = c_int(md.HAPTICS_VISCOSITY_FIELD)
  fieldName = create_string_buffer(bytes(name, 'utf-8'), md.MAX_STRING_LENGTH)
  fieldNamePtr = (c_char_p) (addressof(fieldName))
  field.effectName = fieldNamePtr.value 
  field.viscosityMatrix = (c_double * 9) (viscMatrix[0], viscMatrix[1], viscMatrix[2],\
                                          viscMatrix[3], viscMatrix[4], viscMatrix[5],\
                                          viscMatrix[6], viscMatrix[7], viscMatrix[8])
  packet = MR.makeMessage(field)
  MR.sendMessage(packet)
  return packet

def collidingWith(objectName):
  for i in range(0, len(Globals.CHAI_DATA.collisions)):
    collision = c_char_p(addressof(Globals.CHAI_DATA.collisions[i]))
    collisionName = struct.unpack(str(len(collision.value)) + 's', collision.value)
    collisionName = str(collisionName).split("\'")[1]
    if collisionName == objectName:
      return True 
  return False

def collide2D(objectDict):
  objY = objectDict["position"][1]
  objZ = objectDict["position"][2]
  if objectDict["shape"] != "circle":
    objYSize = objectDict["size"][1]
    objZSize = objectDict["size"][2]
  elif objectDict["shape"] == "circle": #circle object 
    objYSize = objectDict["size"]
    objZSize = objectDict["size"]
  if float(objY - objYSize/2)-10 <= Globals.CHAI_DATA.posY <= float(objY + objYSize/2)+10 and\
      float(objZ - objZSize/2)-10 <= Globals.CHAI_DATA.posZ <= float(objZ + objZSize/2)+10:
    return True

  return False
