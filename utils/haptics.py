import sys 
sys.path.append("/home/mfl24/Documents/chaiProjects/trialControl/python/")
import numpy as np
import messageDefinitions as md
from ctypes import *
import Messenger as MR
import Globals 
import struct 

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
  objYSize = objectDict["size"][1]
  objZSize = objectDict["size"][2]
  if float(objY - objYSize/2) <= Globals.CHAI_DATA.posY <= float(objY + objYSize/2) and\
      float(objZ - objZSize/2) <= Globals.CHAI_DATA.posZ <= float(objZ + objZSize/2): 
        return True
  return False
