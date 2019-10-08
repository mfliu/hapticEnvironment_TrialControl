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
    self.size_hint_x = 0.4

class ControlPane(TabbedPanel):
  def __init__(self, **kwargs):
    super(ControlPane, self).__init__(**kwargs)
    self.trialTab = TrialTab()
    self.stateTab = StateTab()
    self.setupTab = SetupTab()
    
    self.add_widget(self.trialTab)
    self.add_widget(self.stateTab)
    self.add_widget(self.setupTab)
    
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
    self.trialPanel = BoxLayout(orientation='vertical') 
    self.trialName = TextInput(hint_text="Trial Name (e.g. CST)", multiline=False,\
                               on_text_validate=self.setName, size_hint_y=0.2)
    stateNameInfo = BoxLayout(orientation='horizontal', size_hint_y=0.2)
    stateNameLabel = Label(text="Add states to trial:")
    self.stateName = TextInput(hint_text="State Name (e.g. start)", multiline=False)
    self.addStateButton = Button(text="Add State", on_release=self.addState)
    stateNameInfo.add_widget(stateNameLabel)
    stateNameInfo.add_widget(self.stateName)
    stateNameInfo.add_widget(self.addStateButton)

    startStateSelection = BoxLayout(orientation="horizontal", size_hint_y=0.2)
    selectStartLabel = Label(text="Select start state:")
    self.startStateName = Spinner(values=[])
    startStateSelection.add_widget(selectStartLabel)
    startStateSelection.add_widget(self.startStateName)
    
    self.trialPanel.add_widget(self.trialName)
    self.trialPanel.add_widget(stateNameInfo)
    self.trialPanel.add_widget(startStateSelection)
  
  def setName(self, textObj):
    app = App.get_running_app()
    app.root.sessionConfig["name"] = self.trialName.text
  
  def addState(self, stateName):
    app = App.get_running_app()
    if "states" not in app.root.sessionConfig.keys():
      app.root.sessionConfig["states"] = []
    app.root.sessionConfig["states"].append(self.stateName.text)
    self.startStateName.values.append(self.stateName.text)
    app.root.controlPane.stateTab.selectStateList.values.append(self.stateName.text)
    app.root.controlPane.stateTab.nextState.values.append(self.stateName.text)
    self.stateName.text = ''

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
    stateTypes = [m[0] for m in inspect.getmembers(State, inspect.isclass) if m[0].find("State") > 0]
    stateTypeLabel = Label(text="Select state type")
    self.stateTypeSpinner = Spinner(values=stateTypes)# on_release=self.getStateTypeParams)
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
  
  def makeState(self):
    stateName = self.selectStateList.value
    stateType = self.stateTypeSpinner.value
    self.stateDict["name"] = stateName
    self.stateDict["type"] = stateType 
    
  def addTransition(self, addTransitionButton):
    if "transitions" not in self.stateDict.keys():
      self.stateDict["transitions"] = {}
    if self.transitionSymbol not in self.stateDict["transitions"].keys():
      self.stateDict["transitions"][self.transitionSymbol.text] = [self.stateTypeSpinner.text]
    elif self.stateTypeSpinner.value not in self.stateDict["transitions"][self.transitionSymbol]:
      self.stateDict["transitions"][self.transitionSymbol.text].append(self.stateTypeSpinner.text)
  
  def getStateTypeParams(self, spinnerObj, spinnerVal):
    stateType = spinnerVal
    if stateType == "ReachState":
      statePopup =  MsgInfoPopup(fieldList=["timeLimit"], fieldTypes=["float"])
      statePopup.open()
    elif stateType == "ReachHoldState":
      statePopup =  MsgInfoPopup(fieldList=["timeLimit", "holdLength"], fieldTypes=["float", "float"])
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
    self.text = "Setup"
    self.setupTab = BoxLayout(orientation='vertical')
    self.createSavePanel()
    self.createSetupMsgPanel()
    self.makeSetupMsgPanel()
    self.setupTab.add_widget(self.savePanel)
    self.setupTab.add_widget(self.setupMsgPanel)
    self.setupTab.add_widget(self.makeMsgPanel)
    self.add_widget(self.setupTab)
    
  def createSavePanel(self):
    self.savePanel = BoxLayout(orientation='vertical')
    saveLabel = Label(text="Save parameters")
    saveLayout = BoxLayout(orientation='horizontal')
    self.fileName = TextInput(hint_text="File name (e.g. msgLog.log)", multiline=False)
    self.saveMsg = Spinner(values=["Msg1", "Msg2", "Msg3"])
    self.addMsgToFile = Button(text="Add message to file")
    saveLayout.add_widget(self.fileName)
    saveLayout.add_widget(self.saveMsg)
    self.savePanel.add_widget(saveLabel)
    self.savePanel.add_widget(saveLayout)
  
  def createSetupMsgPanel(self):
    self.setupMsgPanel = BoxLayout(orientation='vertical')
    startMsgLabel = Label(text="Session Start Messages")
    self.startUpMsgScroll = ScrollView(do_scroll_y=True, scroll_y=0,\
                                       scroll_type=['bars','content'],\
                                       bar_width=15, pos=[0,0])
    self.startMsgs = TreeView(hide_root=True)
    self.setupMsgPanel.add_widget(startMsgLabel)
    self.setupMsgPanel.add_widget(self.startUpMsgScroll)
    self.setupMsgPanel.add_widget(self.startMsgs)
  
  def makeSetupMsgPanel(self):
    self.makeMsgPanel = BoxLayout(orientation='horizontal')
    msgTypelabel = Label(text="Choose message type:")
    self.msgTypeSpinner = Spinner(values=["msg1", "msg2", "msg3"])
    msgLayout = BoxLayout(orientation='vertical')
    msgInfoLabel = Label(text="Enter message information")
    self.makeMsgPanel.add_widget(msgInfoLabel)
    self.makeMsgPanel.add_widget(msgTypelabel)
    self.makeMsgPanel.add_widget(self.msgTypeSpinner)
    self.makeMsgPanel.add_widget(msgLayout)

## Accessory classes
class MsgInfoPopup(Popup):
  def __init__(self, **kwargs):
    myLayout = BoxLayout(orientation='vertical')
    self.fieldList = kwargs.pop('fieldList')
    fieldTypes= kwargs.pop('fieldTypes')
    self.textInputs = [] 
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
    self.dismiss()

class TrialBuilderApp(App):
  def __init__(self, **kwargs):
    super(TrialBuilderApp, self).__init__(**kwargs)
  
  def build(self,):
    return TrialBuilder()

if __name__ == "__main__":
  TrialBuilderApp().run()

