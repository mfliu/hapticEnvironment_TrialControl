import sys
from multiprocessing import Queue
import json
import os 
import inspect

import kivy
kivy.require("1.9.1")
from kivy import Config 
Config.set('graphics', 'multisamples', '0')
Config.set('graphics', 'width', 1200)
Config.set('graphics', 'height', 900)
Config.set('graphics', 'resizable', False)
from kivy.app import App
from kivy.graphics import *
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button 
from kivy.uix.treeview import TreeView, TreeViewNode, TreeViewLabel
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.label import Label
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.spinner import Spinner 
from kivy.uix.scrollview import ScrollView 
from kivy.uix.colorpicker import ColorPicker

import messageDefinitions as md 
import State

MSG_TYPES = [x[0][2:] for x in inspect.getmembers(md) if x[0].find("M_")==0]
STATE_TYPES = [m[0] for m in inspect.getmembers(State, inspect.isclass) if m[0].find("State") > 0]
class TrialBuilder(BoxLayout):
  def __init__(self, **kwargs):
    super(TrialBuilder, self).__init__(**kwargs)
    self.sessionConfig = {}
    
    self.canvas.add(Color(0.3, 0.3, 0.3))
    self.canvas.add(Rectangle(size=(1200, 900), position=self.pos))
    self.orientation = "horizontal"
    self.padding = 10
    self.spacing = 10 

    self.displayPane = DisplayPane()
    self.controlPane = ControlPane()
    self.add_widget(self.displayPane)
    self.add_widget(self.controlPane)
    
class DisplayPane(BoxLayout):
  def __init__(self, **kwargs):
    super(DisplayPane, self).__init__(**kwargs)
    self.size_hint_x = 0.6

class ControlPane(TabbedPanel):
  def __init__(self, **kwargs):
    super(ControlPane, self).__init__(**kwargs)
    self.tab_width=150
    self.trialTab = TrialTab()
    self.stateTab = StateTab()
    self.setupTab = SetupTab()
    self.taskVarTab = TaskVariableTab()

    self.add_widget(self.trialTab)
    self.add_widget(self.stateTab)
    self.add_widget(self.setupTab)
    self.add_widget(self.taskVarTab)

    self.default_tab = self.trialTab

class TrialTab(TabbedPanelItem):
  def __init__(self, **kwargs):
    super(TrialTab, self).__init__(**kwargs)
    self.text = "Create Trial"
    self.trialTab = BoxLayout(orientation='vertical')
    self.createTrialLayout()
    self.trialTab.add_widget(self.trialPanel)
    self.add_widget(self.trialTab)
  
  def createTrialLayout(self):
    self.trialPanel = BoxLayout(orientation='vertical', padding=50, spacing=50) 
    self.trialName = TextInput(hint_text="Trial Name (e.g. CST)", multiline=False,\
                               on_text_validate=self.setName, size_hint_y=0.1, size_hint_x=0.5,\
                               pos_hint = {'center_x':0.5, 'center_y':0.5}, padding=50)
    stateNameInfo = BoxLayout(orientation='horizontal', size_hint_y=0.1)
    stateNameLabel = Label(text="Add states to trial:", size_hint_y=0.1, pos_hint={'center_y':0.5})
    self.stateName = TextInput(hint_text="State Name (e.g. start)", multiline=False,
                               on_text_validate=self.setStateName)
    self.addStateButton = Button(text="Add State", on_release=self.addState)
    stateNameInfo.add_widget(stateNameLabel)
    stateNameInfo.add_widget(self.stateName)
    stateNameInfo.add_widget(self.addStateButton)
    self.addStateButton.disabled = True
    
    startStateSelection = BoxLayout(orientation="horizontal", size_hint_y=0.1, spacing=50,\
                                    padding=50)
    selectStartLabel = Label(text="Select start state:")
    self.startStateName = Spinner(values=[])
    self.startStateName.bind(text=self.setStartState)
    startStateSelection.add_widget(selectStartLabel)
    startStateSelection.add_widget(self.startStateName)
    
    self.trialPanel.add_widget(self.trialName)
    self.trialPanel.add_widget(stateNameInfo)
    self.trialPanel.add_widget(startStateSelection)
  
  def setName(self, textObj):
    app = App.get_running_app()
    app.root.sessionConfig["name"] = self.trialName.text
  
  def setStateName(self, textObj):
    if self.stateName.text != '':
      self.addStateButton.disabled = False 
    app = App.get_running_app()
    app.root.sessionConfig[self.stateName.text] = {}
  
  def addState(self, stateName):
    app = App.get_running_app()
    if "states" not in app.root.sessionConfig.keys():
      app.root.sessionConfig["states"] = []
    app.root.sessionConfig["states"].append(self.stateName.text)
    self.startStateName.values.append(self.stateName.text)
    app.root.controlPane.stateTab.selectStateList.values.append(self.stateName.text)
    app.root.controlPane.stateTab.nextState.values.append(self.stateName.text)
    self.stateName.text = ''
    self.addStateButton.disabled = True
  
  def setStartState(self, spinnerObj, startStateVal):
    app = App.get_running_app()
    app.root.sessionConfig["startState"] = startStateVal 

class StateTab(TabbedPanelItem):
  def __init__(self, **kwargs):
    super(StateTab, self).__init__(**kwargs)
    self.text = "State Details" 
    self.stateTab = BoxLayout(orientation='vertical')
    self.createSelectStatePanel()
    self.createStateTypePanel()
    self.createTransitionPanel()
    self.createGraphicsPanel()
    self.createHapticsPanel()
    makeStateButton = Button(text="Create State", on_release=self.makeState, size_hint_y=0.1)
    self.stateTab.add_widget(self.selectStatePanel)
    self.stateTab.add_widget(self.stateTypePanel)
    self.stateTab.add_widget(self.transitionPanel)
    self.stateTab.add_widget(self.graphicsPanel)
    self.stateTab.add_widget(self.hapticsPanel)
    self.stateTab.add_widget(makeStateButton)
    self.add_widget(self.stateTab)

    self.stateDict = {}
  
  def createSelectStatePanel(self):
    self.selectStatePanel = BoxLayout(orientation='horizontal', size_hint_y=0.1)
    selectLabel = Label(text="Select State:")
    self.selectStateList = Spinner(values=[])
    self.selectStatePanel.add_widget(selectLabel)
    self.selectStatePanel.add_widget(self.selectStateList)

  def createStateTypePanel(self):
    self.stateTypePanel = BoxLayout(orientation="horizontal", size_hint_y=0.1)
    stateTypeLabel = Label(text="Select state type", padding=(20,20))
    self.stateTypeSpinner = Spinner(values=STATE_TYPES)
    self.stateTypeSpinner.bind(text=self.getStateTypeParams)
    self.stateTypeParams = TreeView(hide_root=True)
    self.stateTypePanel.add_widget(stateTypeLabel)
    self.stateTypePanel.add_widget(self.stateTypeSpinner)
    self.stateTypePanel.add_widget(self.stateTypeParams)
  
  def createTransitionPanel(self):
    self.transitionPanel = BoxLayout(orientation='horizontal', size_hint_y=0.1)
    self.transitionSymbol = TextInput(hint_text="Transition symbol (e.g. success)", multiline=False)
    self.nextState = Spinner(values = self.selectStateList.values)
    addTransitionButton = Button(text="Add Transition", on_release=self.addTransition)
    self.transitionPanel.add_widget(self.transitionSymbol)
    self.transitionPanel.add_widget(self.nextState)
    self.transitionPanel.add_widget(addTransitionButton)
  
  def createGraphicsPanel(self):
    self.graphicsPanel = BoxLayout(orientation='vertical', size_hint_y=0.6)
    
    graphicsIntro = BoxLayout(orientation='horizontal', size_hint_y=0.15)
    graphicsLabel = Label(text="Graphics")
    self.graphicsName = TextInput(hint_text="Object Name (e.g. center)", multiline=False)
    graphicsIntro.add_widget(graphicsLabel)
    graphicsIntro.add_widget(self.graphicsName)

    graphicsShape = BoxLayout(orientation='horizontal', size_hint_y=0.15)
    shapeLabel = Label(text="Shape")
    self.shapeSpinner = Spinner(values=["circle", "box", "arrow"])
    graphicsShape.add_widget(shapeLabel)
    graphicsShape.add_widget(self.shapeSpinner)

    graphicsColor = BoxLayout(orientation='horizontal')
    self.colorPicker = ColorPicker()
    graphicsColor.add_widget(self.colorPicker)

    graphicsSize = BoxLayout(orientation='horizontal', size_hint_y=0.15)
    self.sizeX = TextInput(hint_text="Size X", multiline=False, input_filter="float")
    self.sizeY = TextInput(hint_text="Size Y", multiline=False, input_filter="float")
    self.sizeZ = TextInput(hint_text="Size Z", multiline=False, input_filter="float")
    graphicsSize.add_widget(self.sizeX)
    graphicsSize.add_widget(self.sizeY)
    graphicsSize.add_widget(self.sizeZ)

    graphicsPosition = BoxLayout(orientation='horizontal', size_hint_y=0.15)
    self.posX = TextInput(hint_text="Pos X", multiline=False, input_filter="float")
    self.posY = TextInput(hint_text="Pos Y", multiline=False, input_filter="float")
    self.posZ = TextInput(hint_text="Pos Z", multiline=False, input_filter="float")
    graphicsSize.add_widget(self.posX)
    graphicsSize.add_widget(self.posY)
    graphicsSize.add_widget(self.posZ)
    
    graphicsButton = Button(text="Add Graphics Object to State", on_release=self.addGraphics,\
                            size_hint_y=0.15)
    self.graphicsPanel.add_widget(graphicsIntro)
    self.graphicsPanel.add_widget(graphicsShape)
    self.graphicsPanel.add_widget(graphicsColor)
    self.graphicsPanel.add_widget(graphicsSize)
    self.graphicsPanel.add_widget(graphicsPosition)
    self.graphicsPanel.add_widget(graphicsButton)

  def createHapticsPanel(self):
    self.hapticsPanel = BoxLayout(orientation='vertical', size_hint_y=0.4) 
    
    hapticIntro = BoxLayout(orientation='horizontal', size_hint_y=0.1)
    hapticLabel = Label(text="Haptics")
    self.hapticEffectName = TextInput(hint_text="Effect Name (e.g. viscousField)", multiline=False)
    hapticIntro.add_widget(hapticLabel)
    hapticIntro.add_widget(self.hapticEffectName)

    hapticType = BoxLayout(orientation='horizontal', size_hint_y=0.1)
    hapticTypeLabel = Label(text="Effect Type:")
    self.hapticTypeSpinner = Spinner(values=["stiffness", "bounding plane", "constant force field",\
                                             "viscosity", "freeze"])
    self.hapticTypeSpinner.bind(text=self.getHapticParameters)
    hapticType.add_widget(hapticTypeLabel)
    hapticType.add_widget(self.hapticTypeSpinner)
    
    hapticParams = BoxLayout(orientation='horizontal', size_hint_y=0.3)
    hapticParamLabel = Label(text="Haptic Parameters")
    self.hapticEffectParams = TreeView(hide_root=True)
    hapticParams.add_widget(hapticParamLabel)
    hapticParams.add_widget(self.hapticEffectParams)
    
    self.hapticsPanel.add_widget(hapticIntro)
    self.hapticsPanel.add_widget(hapticType)
    self.hapticsPanel.add_widget(hapticParams)
  
  def makeState(self, buttonObj):
    stateName = self.selectStateList.text
    stateType = self.stateTypeSpinner.text
    self.stateDict["type"] = stateType 
    app = App.get_running_app()
    app.root.sessionConfig[stateName] = self.stateDict 
    self.stateDict = {}
    print(app.root.sessionConfig)

  def addTransition(self, addTransitionButton):
    if "transitions" not in self.stateDict.keys():
      self.stateDict["transitions"] = {}
    if self.transitionSymbol not in self.stateDict["transitions"].keys():
      self.stateDict["transitions"][self.transitionSymbol.text] = [self.nextState.text]
    elif self.stateTypeSpinner.value not in self.stateDict["transitions"][self.transitionSymbol]:
      self.stateDict["transitions"][self.transitionSymbol.text].append(self.nextState.text)

  def getStateTypeParams(self, spinnerObj, spinnerVal):
    stateType = spinnerVal
    if stateType == "ReachState":
      statePopup =  MsgInfoPopup(fieldList=["timeLimit"], fieldTypes=["float"], caller="stateType")
      statePopup.open()
    elif stateType == "ReachHoldState":
      statePopup =  MsgInfoPopup(fieldList=["timeLimit", "holdLength"],\
                                 fieldTypes=["float", "float"], caller="stateType")
      statePopup.open()
    elif stateType == "CSTRunningState":
      pass
  
  def addGraphics(self, buttonObj):
    if "graphics" not in self.stateDict.keys():
      self.stateDict["graphics"] = {}
    objectDict = {}
    objectDict["shape"] = self.shapeSpinner.text 
    objectDict["color"] = self.colorPicker.color
    objectDict["size"] = [float(self.sizeX.text), float(self.sizeY.text), float(self.sizeZ.text)]
    objectDict["position"] = [float(self.posX.text), float(self.posY.text), float(self.posZ.text)]
    self.stateDict["graphics"][self.graphicsName.text] = objectDict 
  
  def getHapticParameters(self, spinnerObj, spinnerVal):
    print(spinnerVal)

class SetupTab(TabbedPanelItem):
  def __init__(self, **kwargs):
    super(SetupTab, self).__init__(**kwargs)
    self.text = "Setup Info"
    self.setupTab = BoxLayout(orientation='vertical')
    self.createSavePanel()
    self.createSetupMsgPanel()
    self.makeSetupMsgPanel()
    self.createBreakdownMsgPanel()
    self.makeBreakdownMsgPanel()
    self.setupTab.add_widget(self.savePanel)
    self.setupTab.add_widget(self.setupMsgPanel)
    self.setupTab.add_widget(self.makeSetupPanel)
    self.setupTab.add_widget(self.breakdownMsgPanel)
    self.setupTab.add_widget(self.makeBreakdownPanel)
    self.add_widget(self.setupTab)
    
  def createSavePanel(self):
    self.savePanel = BoxLayout(orientation='vertical')
    saveLabel = Label(text="Save parameters")
    saveLayout = BoxLayout(orientation='horizontal')
    self.fileName = TextInput(hint_text="File name (e.g. msgLog.log)", multiline=False)
    self.saveMsg = Spinner(values=MSG_TYPES)
    self.addMsgToFile = Button(text="Add message to file")
    saveLayout.add_widget(self.fileName)
    saveLayout.add_widget(self.saveMsg)
    self.savePanel.add_widget(saveLabel)
    self.savePanel.add_widget(saveLayout)
  
  def createSetupMsgPanel(self):
    self.setupMsgPanel = BoxLayout(orientation='vertical')
    startMsgLabel = Label(text="Session Start Messages", size_hint_y=0.1)
    self.startUpMsgScroll = ScrollView(do_scroll_y=True, scroll_y=0,\
                                       scroll_type=['bars','content'],\
                                       bar_width=15, pos=[0,0])
    self.startMsgs = TreeView(hide_root=True)
    self.startUpMsgScroll.add_widget(self.startMsgs)
    self.setupMsgPanel.add_widget(startMsgLabel)
    self.setupMsgPanel.add_widget(self.startUpMsgScroll)
  
  def makeSetupMsgPanel(self):
    self.makeSetupPanel = BoxLayout(orientation='horizontal')
    msgTypelabel = Label(text="Choose message type:")
    msgTypes = inspect.getmembers(md)
    self.startupMsgTypeSpinner = Spinner(values=MSG_TYPES)
    self.startupMsgTypeSpinner.bind(text=self.makeSetupMessage)
    self.makeSetupPanel.add_widget(msgTypelabel)
    self.makeSetupPanel.add_widget(self.startupMsgTypeSpinner)
  
  def makeSetupMessage(self, spinnerObj, spinnerVal):
    app = App.get_running_app()
    msgType = getattr(md, spinnerVal)
    msgStruct = getattr(md, "M_"+spinnerVal)
    if "setup_msg" not in app.root.sessionConfig.keys():
      app.root.sessionConfig["setup_msg"] = []
    msgFields = [f[0] for f in msgStruct.__dict__['_fields_'] if f[0] != "header"]
    msgFieldTypes = [str(f[1]).split(".")[-1].split("'")[0] for f in getattr(md, "M_CST_CREATE").__dict__['_fields_'] if f[0] != "header"]
    msgFieldTypes = [None if x.find("char_Array") > 0 else "float" if x.split("_")[-1] == 'double'\
                     else x.split("_")[-1] for x in msgFieldTypes]
    msgPopup = MsgInfoPopup(fieldList = msgFields, fieldTypes=msgFieldTypes, caller="setup_msg",\
                            msgName=spinnerVal)
    msgPopup.open()
  
  def createBreakdownMsgPanel(self):
    self.breakdownMsgPanel = BoxLayout(orientation='vertical')
    endMsgLabel = Label(text="Session End Messages", size_hint_y=0.1)
    self.breakdownMsgScroll = ScrollView(do_scroll_y=True, scroll_y=0,\
                                       scroll_type=['bars','content'],\
                                       bar_width=15, pos=[0,0])
    self.endMsgs = TreeView(hide_root=True)
    self.breakdownMsgScroll.add_widget(self.endMsgs)
    self.breakdownMsgPanel.add_widget(endMsgLabel)
    self.breakdownMsgPanel.add_widget(self.breakdownMsgScroll)
  
  def makeBreakdownMsgPanel(self):
    self.makeBreakdownPanel = BoxLayout(orientation='horizontal')
    msgTypelabel = Label(text="Choose message type:")
    msgTypes = inspect.getmembers(md)
    self.breakdownMsgTypeSpinner = Spinner(values=MSG_TYPES)
    self.breakdownMsgTypeSpinner.bind(text=self.makeBreakdownMessage)
    self.makeBreakdownPanel.add_widget(msgTypelabel)
    self.makeBreakdownPanel.add_widget(self.breakdownMsgTypeSpinner)
  
  def makeBreakdownMessage(self, spinnerObj, spinnerVal):
    app = App.get_running_app()
    msgType = getattr(md, spinnerVal)
    msgStruct = getattr(md, "M_"+spinnerVal)
    if "end_msg" not in app.root.sessionConfig.keys():
      app.root.sessionConfig["end_msg"] = []
    msgFields = [f[0] for f in msgStruct.__dict__['_fields_'] if f[0] != "header"]
    msgFieldTypes = [str(f[1]).split(".")[-1].split("'")[0] for f in msgStruct.__dict__['_fields_'] if f[0] != "header"]
    msgFieldTypes = [None if x.find("char_Array") > 0 else "float" if x.split("_")[-1] == 'double'\
                     else x.split("_")[-1] for x in msgFieldTypes]
    msgPopup = MsgInfoPopup(fieldList = msgFields, fieldTypes=msgFieldTypes, caller="end_msg",\
                            msgName=spinnerVal)
    msgPopup.open()

class TaskVariableTab(TabbedPanelItem):
  def __init__(self, **kwargs):
    super(TaskVariableTab, self).__init__(**kwargs)
    self.text = "Task Variables"
    self.taskVarsTab = BoxLayout(orientation='vertical')
    self.createTaskVarsPanel()
    self.add_widget(self.taskVarsPanel)

  def createTaskVarsPanel(self):
    self.taskVarsPanel = BoxLayout(orientation='vertical')
    self.taskVarsScroll = ScrollView(do_scroll_y=True, scroll_y=0,\
                                       scroll_type=['bars','content'],\
                                       bar_width=15, pos=[0,0])
    self.taskVarsTreeView = TreeView(hide_root=True)
    self.taskVarsScroll.add_widget(self.taskVarsTreeView)
    addTaskVarButton = Button(text="Add Task Variable", on_release=self.getTaskVarInfo)
    self.taskVarsPanel.add_widget(self.taskVarsScroll)
    self.taskVarsPanel.add_widget(addTaskVarButton)

  def getTaskVarInfo(self, button):
    self.taskVarPopup = Popup(title="Task Variable Information:")
    taskVarLayout = BoxLayout(orientation='vertical')
    self.taskVarName = TextInput(hint_text="Task Variable Name", multiline=False)
    self.taskVarValue = TextInput(hint_text="Task Variable Starting Value", multiline=False)
    taskVarAdd = Button(text="Add", on_release=self.addTaskVar)
    taskVarLayout.add_widget(self.taskVarName)
    taskVarLayout.add_widget(self.taskVarValue)
    taskVarLayout.add_widget(taskVarAdd)
    self.taskVarPopup.add_widget(taskVarLayout)
    self.taskVarPopup.open()

  def addTaskVar(self, button):
    app = App.get_running_app()
    if "taskVars" not in app.root.sessionConfig.keys():
      app.root.sessionConfig["taskVars"] = {}
    app.root.sessionConfig["taskVars"][self.taskVarName.text] = self.taskVarValue.text
    self.taskVarPopup.dismiss()

## Accessory classes
class MsgInfoPopup(Popup):
  def __init__(self, **kwargs):
    myLayout = BoxLayout(orientation='vertical')
    self.fieldList = kwargs.pop('fieldList')
    fieldTypes= kwargs.pop('fieldTypes')
    self.caller = kwargs.pop('caller')
    self.textInputs = [] 
    if self.caller == "setup_msg" or self.caller == "end_msg":
      self.msgName = kwargs.pop('msgName')
    for fIdx in range(0, len(self.fieldList)):
      f = self.fieldList[fIdx]
      fieldLabel = Label(text=f)
      textInput = TextInput(hint_text=f, multiline=False, input_filter=fieldTypes[fIdx])
      self.textInputs.append(textInput)
      myLayout.add_widget(fieldLabel)
      myLayout.add_widget(textInput)
    super(MsgInfoPopup, self).__init__(**kwargs)
    enterParamsButton = Button(text="Save State Type Params", on_release=self.saveParams)
    myLayout.add_widget(enterParamsButton)
    self.add_widget(myLayout)
    self.title = "Enter Information"
  
  def saveParams(self, button):
    app = App.get_running_app()
    if self.caller == "stateType":
      it = app.root.controlPane.stateTab.stateTypeParams.iterate_all_nodes()
      try:
        while True:
          node = it.__next__()
          app.root.controlPane.stateTab.stateTypeParams.remove_node(node)
      except StopIteration:
        pass
      for fIdx in range(0, len(self.fieldList)):
        fieldName = self.fieldList[fIdx]
        fieldValue = self.textInputs[fIdx].text
        app.root.controlPane.stateTab.stateDict[fieldName] = fieldValue
        app.root.controlPane.stateTab.stateTypeParams.add_node(\
                            TreeViewLabel(text=fieldName + ": " + str(fieldValue)))
    elif self.caller == "setup_msg":
      msgDict = {self.msgName:{}} 
      for fIdx in range(0, len(self.fieldList)):
        fieldName = self.fieldList[fIdx]
        fieldValue = self.textInputs[fIdx].text 
        msgDict[self.msgName][fieldName] = fieldValue
      app.root.sessionConfig["setup_msg"].append(msgDict)
    elif self.caller == "end_msg":
      msgDict = {self.msgName:{}} 
      for fIdx in range(0, len(self.fieldList)):
        fieldName = self.fieldList[fIdx]
        fieldValue = self.textInputs[fIdx].text 
        msgDict[self.msgName][fieldName] = fieldValue
      app.root.sessionConfig["end_msg"].append(msgDict)
    self.dismiss()

class TrialBuilderApp(App):
  def __init__(self, **kwargs):
    super(TrialBuilderApp, self).__init__(**kwargs)
  
  def build(self,):
    return TrialBuilder()

if __name__ == "__main__":
  TrialBuilderApp().run()

