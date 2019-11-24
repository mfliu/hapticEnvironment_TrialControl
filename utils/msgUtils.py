import sys 
import numpy as np
import Globals 
sys.path.append(Globals.HOME_PATH)
import messageDefinitions as md
from ctypes import *
import Messenger as MR
import struct 
import inspect 

allMD = inspect.getmembers(md)
mdKeys = [x[0] for x in allMD]
mdVals = [x[1] for x in allMD]

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

def messageToDict(packet):
  msgHeader = md.MSG_HEADER() 
  MR.readMessage(packet, msgHeader)
  msgNum = msgHeader.serial_no
  msgTime = msgHeader.timestamp
  msgType = msgHeader.msg_type
  msgName = "M_" + mdKeys[mdVals.index(msgType)]
  msgStruct = getattr(md, msgName)()
  MR.readMessage(packet, msgStruct)
  msgDict = {"msgTime": msgTime, "msgNum":msgNum, "msgType":mdKeys[mdVals.index(msgType)]}
  for key in msgStruct.__slots__:
    if key != "header":
      fieldObj = getattr(msgStruct, key)
      fieldType = str(type(fieldObj))
      if fieldType.find("c_char_Array") > -1:
        byteString = getattr(msgStruct, key)
        unpacked = struct.unpack(str(md.MAX_STRING_LENGTH) + "s", byteString)
        msgDict[key] = unpacked[0].decode("utf-8")
      elif fieldType.find("c_float_Array") > -1:
        arrayLen = fieldType.split("c_float_Array")[-1].split("_")[-1].split("'")[0]
        floatArray = list(struct.unpack(arrayLen + "f", fieldObj))
        msgDict[key] = floatArray
      elif fieldType.find("c_double_Array") > -1:
        arrayLen = fieldType.split("c_double_Array")[-1].split("_")[-1].split("'")[0]
        doubleArray = list(struct.unpack(arrayLen + "d", fieldObj))
        msgDict[key] = doubleArray
      elif fieldType.find("c_int_Array") > -1:
        arrayLen = fieldType.split("c_int_Array")[-1].split("_")[-1].split("'")[0]
        intArray = list(struct.unpack(arrayLen + "i", fieldObj))
        msgDict[key] = intArray
      else:
        msgDict[key] = getattr(msgStruct, key)
  return msgDict

