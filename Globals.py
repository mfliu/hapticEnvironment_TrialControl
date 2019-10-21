import messageDefinitions as md
import msgpackrpc
import socket 
import sys 
import platform

MODULE_NUM = 2
HOME_PATH = "/home/mfl24/Documents/chaiProjects/hapticEnvironment_TrialControl/"
UTILS_PATH = "/home/mfl24/Documents/chaiProjects/hapticEnvironment_TrialControl/utils/"
NATNET_PATH = "/home/mfl24/Documents/chaiProjects/NatNetSDK/Samples/PythonClient/"
sys.path.append(NATNET_PATH)

CHAI_DATA = md.M_HAPTIC_DATA_STREAM() 


IPADDR = "127.0.0.1"
PORT = 9000

LOGGER_IP = "127.0.0.1"
LOGGER_PORT = 10000 

RPC_IP = "127.0.0.1"
RPC_PORT = 8080

MOCAP_IP = "127.0.0.1"
MOCAP_PORT = 1510

EMG_COMMAND_IP = "127.0.0.1"
EMG_COMMAND_PORT = 50040

EMG_STREAM_IP = "127.0.0.1"
EMG_STREAM_PORT = 50041

client = None 
def getClient():
  global client 
  if client == None:
    client = msgpackrpc.Client(msgpackrpc.Address(RPC_IP, RPC_PORT))
  return client

listenerSocket = None 
def getListenerSocket():
  global listenerSocket
  if listenerSocket == None:
    listenerSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    listenerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if platform.system() == "Linux":
      listenerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    listenerSocket.bind((IPADDR, PORT))
  return listenerSocket 

def getMocapClient():
  from NatNetClient import NatNetClient 
  global mocapClient, mocapSocket
  if mocapClient == None or mocapSocket == None:
    mocapClient = NatNetClient() 
    mocapSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  return (mocapClient, mocapSocket)
 
def getEMGCommand():
  global emgCommandSocket
  if emgCommandSocket == None:
    emgCommandSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    emgCommandSocket.connect((EMG_COMMAND_IP, EMG_COMMAND_PORT))
    emgCommandSocket.sendall(b'START')
  return emgCommandSocket

def getEMGStream():
  global emgStreamSocket
  if emgStreamSocket == None:
    emgStreamSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    emgStreamSocket.connect((EMG_STREAM_IP, EMG_STREAM_PORT))
  return emgStreamSocket 


