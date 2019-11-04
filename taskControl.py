import sys
from statemachine import *
from multiprocessing import Queue
import json
import Globals
sys.path.append(Globals.HOME_PATH)
import messageDefinitions as md
import Messenger as MR
from Logger import loggerFunction
import multiprocessing as mp
import ctypes
from threading import Thread 
import os 
import kivy
kivy.require("1.9.1")
from kivy import Config 
Config.set('graphics', 'multisamples', '0')
Config.set('graphics', 'width', 900)
Config.set('graphics', 'height', 700)
Config.set('graphics', 'resizable', False)
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button 
from kivy.uix.treeview import TreeView, TreeViewLabel
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.label import Label
from functools import partial
from kivy.properties import BooleanProperty

class TaskControl(BoxLayout):
  def __init__(self, **kwargs):
    super(TaskControl, self).__init__(**kwargs)
    self.sessionInfo = {}
    self.state = "running"
    self.sm = None 
    client = Globals.getClient()
    client.call("addModule", 2, Globals.IPADDR, Globals.PORT)
    client.call("subscribeTo", 2, 1)
    
    self.listenerThread = Thread(target=self.listener)
    self.listenerThread.daemon = True
    
    self.messageThread = Thread(target=self.messageListener)
    self.messageThread.daemon = True
    
    self.listenerThread.start()
    time.sleep(1.0)
    self.messageThread.start()
    time.sleep(1.0)

  def setSubjectName(self, text):
    self.sessionInfo["subjectName"] = text 
  
  def initializeTreeView(self):
    self.tv = self.get_root_window().children[-1].ids["experimentRecords"]
    self.tv.bind(minimum_height=self.tv.setter('height'))
    self.treeviewInitialized = True

  def addNode(self):
    trialNum = self.sm.taskVars["trialNum"]
    trialNode = self.tv.add_node(TreeViewLabel(text="Trial " + str(trialNum)))
    for k in self.sm.taskVars["GUITree"]:
      if k not in self.sm.taskVars.keys():
        self.sm.taskVars[k] = "None"
      infoNode = self.tv.add_node(TreeViewLabel(text=k + ": " + str(self.sm.taskVars[k])), trialNode)
  
  def chooseSaveDir(self):
    filePopup = FilePopup(titleText="Choose Save Directory", canBeDir=True, buttonText="Select Folder")
    filePopup.open()
  
  def chooseConfigFile(self):
    filePopup = FilePopup(titleText="Choose Configuration File", canBeDir=False, buttonText="Select Configuration File")
    filePopup.open()

  def listener(self):
    print("Listener thread started")
    while self.state == "running":
      data, addr = Globals.getListenerSocket().recvfrom(md.MAX_PACKET_LENGTH)
      header = md.MSG_HEADER()
      MR.readMessage(data, header)
      if header.msg_type == md.HAPTIC_DATA_STREAM:
        msg_data = md.M_HAPTIC_DATA_STREAM()
        MR.readMessage(data, msg_data)
        Globals.CHAI_DATA = msg_data
      time.sleep(0.0001)
  
  def messageListener(self):
    print("Messaging thread started")
    while self.state == "running":
      data, addr = Globals.getListenerSocket().recvfrom(md.MAX_PACKET_LENGTH)
      header = md.MSG_HEADER()
      MR.readMessage(data, header)
      if header.msg_type == md.CST_DATA and self.sm.paused == False:
        cstData = md.M_CST_DATA()
        MR.readMessage(data, cstData)
        if np.abs(cstData.cursorY) > 120 and self.sm.taskVars["running"] == 1:
          self.sm.taskVars["trialSucceeded"] = 0
      time.sleep(0.0001)

  def startSM(self):
    self.initializeTreeView()
    if "saveDir" not in self.sessionInfo.keys():
      self.sessionInfo["saveDir"] = self.get_root_window().children[-1].ids["saveDirText"].text
    if "subjectName" not in self.sessionInfo.keys():
      self.sessionInfo["subjectName"] = self.get_root_window().children[-1].ids["subjectName"].text

    saveFilePrefix = os.path.join(self.sessionInfo["saveDir"], self.sessionInfo["subjectName"] + "-" +\
                                  self.sessionInfo["taskName"] + "_" +\
                                  time.ctime(time.time()).replace(" ", "_").replace(":", "-"))
    
    taskSM = StateMachine(self.sessionInfo["configFile"], saveFilePrefix)
    self.sm = taskSM
    self.sm.taskVars["taskControl"] = self
    
    saveConfig = {"saveFilePrefix": saveFilePrefix}
    saveParams = self.sm.config["save_params"]
    for fileName in saveParams.keys():
      saveConfig[fileName] = [getattr(md, x) for x in saveParams[fileName]]
    self.loggingProcess = mp.Process(target=loggerFunction, args=(saveConfig,))
    self.loggingProcess.start()
    time.sleep(1)

    shouldRecord = self.get_root_window().children[-1].ids["recordData"].active
    if shouldRecord == True:
      mocapRecord = self.get_root_window().children[-1].ids["mocapData"].active 
      emgRecord = self.get_root_window().children[-1].ids["emgData"].active 
      
      startRecording = md.M_START_RECORDING()
      startRecording.header.msg_type = c_int(md.START_RECORDING)
      fileName = create_string_buffer(str.encode(saveFilePrefix+"_trial.data"), md.MAX_STRING_LENGTH)
      fileNamePtr = (c_char_p) (addressof(fileName))
      startRecording.filename = fileNamePtr.value
      packet = MR.makeMessage(startRecording)
      MR.sendMessage(packet)
      
      if mocapRecord == True:
        mocapClient, mocapSocket = Globals.getMocapClient()
        mocapClient.sendCommand(2, "StartRecording", mocapSocket, Globals.MOCAP_IP,\
                                Globals.MOCAP_PORT)
      if emgRecord == True:
        emgCommandSocket = Globals.getEMGCommand()
        emgStreamSocket = Globals.getEMGStream()
        emgCommandSocket.sendall(b'TRIGGER START\r\n\r\n')
    
    self.get_root_window().children[-1].ids["pauseButton"].disabled = False
    self.smThread = Thread(target=self.sm.run)
    self.smThread.daemon = True
    self.smThread.start()
    self.get_root_window().children[-1].ids["startButton"].disabled = True
    self.get_root_window().children[-1].ids["stopButton"].disabled = False 

  def pauseResumeSM(self):
    pauseButton = self.get_root_window().children[-1].ids["pauseButton"]
    if self.sm.paused == False and pauseButton.text == "Pause":
      pauseRecording = md.M_PAUSE_RECORDING()
      pauseRecording.header.msg_type = c_int(md.PAUSE_RECORDING)
      packet = MR.makeMessage(pauseRecording)
      MR.sendMessage(packet)
      self.sm.paused = True 
      pauseButton.text = "Resume"
    elif self.sm.paused == True and pauseButton.text == "Resume":
      resumeRecording = md.M_RESUME_RECORDING()
      resumeRecording.header.msg_type = c_int(md.RESUME_RECORDING)
      packet = MR.makeMessage(resumeRecording)
      MR.sendMessage(packet)
      self.sm.paused = False
      pauseButton.text = "Pause"

  def stopSM(self):
    self.sm.running = False
    while self.sm.stopped != True:
      time.sleep(0.5)
     
    shouldRecord = self.get_root_window().children[-1].ids["recordData"].active
    if shouldRecord == True:
      mocapRecord = self.get_root_window().children[-1].ids["mocapData"].active 
      emgRecord = self.get_root_window().children[-1].ids["emgData"].active 
      
      stopRecording = md.M_STOP_RECORDING()
      stopRecording.header.msg_type = c_int(md.STOP_RECORDING)
      packet = MR.makeMessage(stopRecording)
      MR.sendMessage(packet)
      time.sleep(0.5)
      if mocapRecord == True:
        mocapClient, mocapSocket = Globals.getMocapClient()
        mocapClient.sendCommand(2, "StopRecording", mocapSocket, Globals.MOCAP_IP,\
                                Globals.MOCAP_PORT)
      if emgRecord == True:
        emgCommandSocket = Globals.getEMGCommand()
        emgStreamSocket = Globals.getEMGStream()
        emgCommandSocket.sendall(b'TRIGGER STOP\r\n\r\n')
    self.loggingProcess.join()
    self.sessionInfo = {}
    resetWorld = md.M_RESET_WORLD()
    resetWorld.header.msg_type = md.RESET_WORLD
    packet = MR.makeMessage(resetWorld)
    MR.sendMessage(packet)
    self.get_root_window().children[-1].ids["startButton"].disabled = False
    self.get_root_window().children[-1].ids["stopButton"].disabled = True 
    
class FilePopup(Popup):
  def __init__(self, **kwargs):
    super(FilePopup, self).__init__()
    titleText = kwargs['titleText']
    dirTrue = kwargs['canBeDir']
    buttonText = kwargs['buttonText']
    if buttonText == "Select Folder":
      self.choice = "saveDir"
    elif buttonText == "Select Configuration File":
      self.choice = "configFile"
    content = BoxLayout(orientation='vertical')
    chooseButton = Button(text=buttonText, size_hint=(1, 0.2))
    fileChooser = FileChooserIconView()
    fileChooser.dirselect = BooleanProperty(dirTrue)
    fileChooser.bind(selection=self.selectingFolder)
    chooseButton.bind(on_release=self.chooseFile)
    content.add_widget(fileChooser)
    content.add_widget(chooseButton)
    self.title = titleText
    self.canvas.opacity = 0.8
    self.background_color = 1,1,1,1
    self.content = content
    self.size_hint = (0.8, 0.8)
     
  def selectingFolder(self, path, selection):
    self.selectedFolder = selection[0]
  
  def chooseFile(self, obj):
    self.get_root_window().children[-1].sessionInfo[self.choice] = self.selectedFolder
    if self.choice == "configFile":
      self.sessionInfo = {}
      self.get_root_window().children[-1].ids["configFileText"].text = self.selectedFolder
      configData = json.load(open(self.selectedFolder))
      self.get_root_window().children[-1].ids["taskName"].text = configData["name"] 
      self.get_root_window().children[-1].sessionInfo["taskName"] = configData["name"]
    elif self.choice == "saveDir":
      self.get_root_window().children[-1].ids["saveDirText"].text = self.selectedFolder
    self.dismiss()

class TaskControlApp(App):
  def __init__(self, **kwargs):
    super(TaskControlApp, self).__init__(**kwargs)

  def build(self,):
    return TaskControl()
  
  def on_start(self):
    sessionStart = md.M_SESSION_START()
    sessionStart.header.msg_type = c_int(md.SESSION_START)
    packet = MR.makeMessage(sessionStart)
    MR.sendMessage(packet)
  
  def on_stop(self):
    sessionStop = md.M_SESSION_END()
    sessionStop.header.msg_type = c_int(md.SESSION_END)
    packet = MR.makeMessage(sessionStop)
    MR.sendMessage(packet)
    self.state = "stopping"


if __name__ == "__main__":
  TaskControlApp().run()
