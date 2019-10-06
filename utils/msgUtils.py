import sys 
sys.path.append("/home/mfl24/Documents/chaiProjects/trialControl/python/")
import numpy as np
import messageDefinitions as md
from ctypes import *
import Messenger as MR
import Globals 
import struct 
import inspect 

def makeMessage(msgParams):
  name = next(iter(msgParams)) #.keys()[0]
  msgInfo = msgParams[name]
  msgHeader = md.MSG_HEADER()
  msgHeader.msg_type = getattr(md, name)
  msgType = "M_" + name
  msgStructType = getattr(md, msgType)
  msgStruct = msgStructType()
  msgStructMembers = inspect.getmembers(msgStruct)
  msgStructFields = [item for item in msgStructMembers if item[0] == "_fields_"][0][1]
  msgStruct.header = msgHeader
  for pair in msgStructFields:
    if pair[0] != "header":
      propertyName = pair[0]
      propertyType = pair[1].__name__ 
      if propertyType.find("char_Array") > 0:
        stringVal = msgInfo[propertyName]
        stringValBuffer = create_string_buffer(bytes(stringVal, 'utf-8'), md.MAX_STRING_LENGTH)
        stringValPtr = (c_char_p) (addressof(stringValBuffer))
        setattr(msgStruct, propertyName, stringValPtr.value)
      else:
        propertyVal = (pair[1])(msgInfo[propertyName])
        setattr(msgStruct, propertyName, propertyVal)
  packet = MR.makeMessage(msgStruct)
  MR.sendMessage(packet)
  return packet
