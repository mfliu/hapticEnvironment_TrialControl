import messageDefinitions as md
import msgpackrpc
import socket 

MODULE_NUM = 2

IPADDR = "127.0.0.1"
PORT = 9000

LOGGER_IP = "127.0.0.1"
LOGGER_PORT = 10000 

RPC_IP = "127.0.0.1"
RPC_PORT = 8080

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
    listenerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    listenerSocket.bind((IPADDR, PORT))
  return listenerSocket 


HOME_PATH = "/home/mfl24/Documents/chaiProjects/trialControl/"
UTILS_PATH = "/home/mfl24/Documents/chaiProjects/trialControl/utils/"
FUNCTIONS_PATH = "/home/mfl24/Documents/chaiProjects/trialControl/trialControl/"

CHAI_DATA = md.M_HAPTIC_DATA_STREAM() 
