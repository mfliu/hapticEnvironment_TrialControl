import sys
import json
import os 
import inspect
from threading import Thread 
import Globals 
import struct 
import numpy as np 
from collections import deque 
import time 
import math

import kivy
kivy.require("1.9.1")
from kivy import Config 
Config.set('graphics', 'multisamples', '0')
Config.set('graphics', 'width', 900)
Config.set('graphics', 'height', 950)
Config.set('graphics', 'resizable', False)
from kivy.app import App
from kivy.graphics import *
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button 
from kivy.uix.label import Label
from kivy.uix.slider import Slider 
import matplotlib 
matplotlib.use('module://kivy.garden.matplotlib.backend_kivy')
import matplotlib.pyplot as plt 
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvas 
from kivy.core.window import Window
Window.clearcolor=(0.3, 0.3, 0.3, 1.0)
from kivy.clock import Clock
Clock.max_iteration = 40

class EMGPlotter(BoxLayout):
  def __init__(self, **kwargs):
    super(EMGPlotter, self).__init__(**kwargs)
    self.orientation='vertical'
    self.emgPlots = EMGPlots()
    self.timeSlider = Slider(min=1, max=5, value=1, step=1, on_touch_up=self.emgPlots.adjustAxes)
    self.ySlider = Slider(min=0.5, max=5, value=1, step=0.1, on_touch_up=self.emgPlots.adjustAxes)
    self.timeLabel = Label(text="Time: " + str(self.timeSlider.value))
    self.yLabel = Label(text="Range (+/-): " + str(self.ySlider.value))
    self.add_widget(self.emgPlots)

    timeLayout = BoxLayout(orientation='horizontal', size_hint_y=0.05)
    timeLayout.add_widget(self.timeLabel)
    timeLayout.add_widget(self.timeSlider)

    yLayout = BoxLayout(orientation='horizontal', size_hint_y=0.05)
    yLayout.add_widget(self.yLabel)
    yLayout.add_widget(self.ySlider)
    self.add_widget(timeLayout)
    self.add_widget(yLayout)

    self.emgBuffer = deque(maxlen=10000) #np.zeros((10000, 16)) # 5s buffer, 16 channels

    self.listener = Thread(target=self.emgListener)
    self.listener.daemon = True 


    self.plotter = Thread(target=self.emgPlotter)
    self.plotter.daemon = True
    

    self.listener.start()
    time.sleep(5)
    self.plotter.start()

  def emgListener(self):
    while App.get_running_app().running == True:
      emgByteData = App.get_running_app().emgStreamSocket.recv(64)
      emgData = struct.unpack('<16f', emgByteData)
      self.emgBuffer.append(emgData)
    
  def emgPlotter(self):
    Clock.schedule_interval(lambda dt: self.emgPlots.updatePlots(self.emgBuffer), 0.001)

class EMGPlots(GridLayout):
  def __init__(self, **kwargs):
    super(EMGPlots, self).__init__(**kwargs)
    self.cols = 2
    self.plotHandle = []
    self.timescale = 1
    
    self.initializePlots() 

  def initializePlots(self):
    for m in range(0, 10):
      muscle = plt.figure(facecolor=(0.3, 0.3, 0.3))
      plt.subplots_adjust(top=0.85, bottom=0.1, left=0.1, right=0.9)
      ax  = muscle.add_subplot(1, 1, 1)
      ax.spines['bottom'].set_color('white')
      ax.spines['top'].set_color('white')
      ax.spines['left'].set_color('white')
      ax.spines['right'].set_color('white')
      ax.tick_params(length=0, color='white', labelsize=8, labelcolor='white')
      ax.set_title("Trigno Sensor " + str(m+1), color='white')
      ax.set_xlim([0, self.timescale * 2000])
      ax.set_ylim([-0.1, 0.1])
      ax.set_facecolor((0.3, 0.3, 0.3))
      ax.set_xticks([])
      ax.set_yticks([])
      ax.set_xticklabels([])
      ax.set_yticklabels([])
      ax.plot([], linewidth=1)[0]
      muscle_handle = FigureCanvas(muscle)
      muscle_handle.blit()
      self.add_widget(muscle_handle)
      self.plotHandle.append(muscle_handle)
  
  def updatePlots(self, emgBuffer):
    plotData = np.squeeze(np.array(list(emgBuffer))) * 1000
    for m in range(0, 10):
      fig = self.plotHandle[m]
      ax = fig.figure.axes[0]
      lines = ax.lines
      lines[0].set_xdata(np.arange(0, self.timescale * 2000))
      lines[0].set_ydata(plotData[math.floor(-self.timescale*2000):, m])
      ax.draw_artist(lines[0])
      fig.draw()
  
  def adjustAxes(self, slider, mouseEvent):
    self.timescale = round(App.get_running_app().emgPlotter.timeSlider.value, 2)
    App.get_running_app().emgPlotter.timeLabel.text = "Time: " + str(self.timescale)
    yLim = App.get_running_app().emgPlotter.ySlider.value
    App.get_running_app().emgPlotter.yLabel.text = "Range(+/-): " + str(yLim)
    for fig in self.plotHandle:
      ax = fig.figure.axes[0]
      ax.set_xlim([0, self.timescale * 2000])
      ax.set_ylim([-yLim, yLim])
      fig.blit()
      fig.draw()



class EMGPlotterApp(App):
  def __init__(self, **kwargs):
    super(EMGPlotterApp, self).__init__(**kwargs)

  def build(self):
    self.emgCommandSocket = Globals.getEMGCommand()
    self.emgStreamSocket = Globals.getEMGStream()
    self.emgCommandSocket.sendall(b'TRIGGER START\r\n\r\n')
    self.running = True
    self.emgPlotter = EMGPlotter()
    return self.emgPlotter
  
  def on_stop(self):
    self.running = False 
    self.emgCommandSocket.sendall(b'TRIGGER STOP\r\n\r\n')

if __name__ == "__main__":
  EMGPlotterApp().run()
