#!/usr/bin/env python3

#import schedule
#import cherrypy
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.storage.jsonstore import JsonStore
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.uix.slider import Slider
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.button import Button
from kivy.app import App
import threading
import math
import os
import os.path
import sys
import time
from datetime import datetime
from urllib.request import urlopen
import json
import random
import socket
import re
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.lang import Builder
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup


##############################################################################
#                                                                            #
#       Kivy UI Imports                                                      #
#                                                                            #
##############################################################################

import kivy
kivy.require('1.11.1')  # replace with your current kivy version !

##############################################################################
#                                                                            #
#       GPIO & Simulation Imports                                            #
#                                                                            #
##############################################################################

class ToggleTemp(ToggleButton):
    def __init__(self, temp, lomax, himax, label, **kvargs):
        self.temp = temp
        self.rng = range(lomax, himax+1)
        self.label = label
        super().__init__(text=self.get_text(),
#                         group='heat/cool',
                         background_color=(0,0,0,0),
                         markup=True,
                         **kvargs)

    def set_text(self):
        self.text = self.get_text()

    def get_text(self):
        text = '%s to\n[size=30]%d[sup]o[/sup][/size]' % (self.label, self.temp)
        if self.state == 'down':
            color = '1c6ed4' if self.label == 'Cool' else 'cf1943'
            text = '[color=#%s]%s[/color]' % (color, text)
        return text


class DateTime(Label):
    def __init__(self, fmt, align, seconds, **kvargs):
        self.fmt = fmt
        self.align = align
        self.seconds = seconds
        super().__init__(text=self.get_text(),
                         markup=True,
                         **kvargs)
        Clock.schedule_once(self.update, seconds)

    def get_text(self):
        text = datetime.today().strftime(self.fmt).lstrip('0')
        return '[size=30]%s[/size]' % text

    def update(self, wtf):
        self.text = self.get_text()
        Clock.schedule_once(self.update, self.seconds)


class WiFiButton(Button):
    def __init__(self, **kvargs):
        super().__init__(**kvargs)
        self.ssid = ''
        self.passwd = ''
        self.bind(on_press=self.get_info)

    def get_info(self, wtf):
        print("HOLA")
        ssid = TextInput(text='ssid')
        passwd = TextInput(text='passwd')
        box = BoxLayout(orientation='vertical')
        box.add_widget(ssid)
        box.add_widget(passwd)
        popup = Popup(title='LAN login',
                      context=box)
        popup.open()


class ThermostatApp(App):

    def build(self):
        # Set up the thermostat UI layout:
        self.thermostatUI = BoxLayout(orientation='vertical', size=(800, 480))

        # Make the background black:
        with self.thermostatUI.canvas.before:
            Color(45.0/255.0, 100.0/255.0, 189.0/255.0, .5)
            self.rect = Rectangle(size=(800, 480), pos=self.thermostatUI.pos)

        # Create the rest of the UI objects ( and bind them to
        # callbacks, if necessary ):

        datebox = BoxLayout(orientation='horizontal', size_hint=(1, .1))
        self.datelabel = DateTime(fmt='%a, %b %d', align='left', seconds=60)
        self.timelabel = DateTime(fmt='%I:%M %p', align='middle', seconds=5)
        self.wifibutton = WiFiButton()
        datebox.add_widget(self.datelabel)
        datebox.add_widget(self.timelabel)
        datebox.add_widget(self.wifibutton)

        weatherbox = BoxLayout(orientation='vertical', size_hint=(.3, .9))
        self.weatherlabel = Label(text='Today')
        self.statuslabel = Label(text='Status')
        weatherbox.add_widget(self.weatherlabel)
        weatherbox.add_widget(self.statuslabel)

        ctrlbox = BoxLayout(orientation='vertical', size_hint=(.2, .9))
        self.upbutton = Button(text='Up')
        self.upbutton.increment = 1
        self.dnbutton = Button(text='Down')
        self.dnbutton.increment = -1
        self.coolbtn = ToggleTemp(70, 55, 90, 'Cool')
        self.heatbtn = ToggleTemp(70, 55, 90, 'Heat')
        ctrlbox.add_widget(self.upbutton)
        ctrlbox.add_widget(self.heatbtn)
        ctrlbox.add_widget(self.coolbtn)
        ctrlbox.add_widget(self.dnbutton)

        tempbox = BoxLayout(orientation='vertical', size_hint=(.5, .9))
        self.templabel = Label(text='[size=70]74[sup]o[/sup][/size]', markup=True)
        self.systemlabel = Label(text=self.system_text(), markup=True)
        tempbox.add_widget(self.templabel)
        tempbox.add_widget(self.systemlabel)

        mainbox = BoxLayout(orientation='horizontal')
        mainbox.add_widget(weatherbox)
        mainbox.add_widget(tempbox)
        mainbox.add_widget(ctrlbox)

        self.thermostatUI.add_widget(datebox)
        self.thermostatUI.add_widget(mainbox)

        self.upbutton.bind(on_press=self.heat_cool_control_callback)
        self.dnbutton.bind(on_press=self.heat_cool_control_callback)
        self.coolbtn.bind(on_press=self.heat_cool_control_callback)
        self.heatbtn.bind(on_press=self.heat_cool_control_callback)

        return self.thermostatUI

    def heat_cool_control_callback(self, control):
        if control in [self.upbutton, self.dnbutton]:
            targets = [v for v in [self.coolbtn, self.heatbtn]
                       if v.state == 'down']
            if not targets:
                targets = [self.coolbtn, self.heatbtn]
            for target in targets:
                if target.temp + control.increment in target.rng:
                    target.temp += control.increment

            if self.coolbtn.temp < self.heatbtn.temp:
                if self.heatbtn in targets:
                    self.coolbtn.temp = self.heatbtn.temp
                elif self.coolbtn in targets:
                    self.heatbtn.temp = self.coolbtn.temp

        self.coolbtn.set_text()
        self.heatbtn.set_text()

        #print('\n'.join(dir(control)))
        return

    def system_text(self):
        heat = "[color=00ff00][b]On[/b][/color]" if self.heatbtn.state == 'down' else 'Off'
        cool = "[color=00ff00][b]On[/b][/color]" if self.coolbtn.state == 'down' else 'Off'
        return ('[b]System:[/b]\n' +
                "  Heat:     %s\n" % heat +
                "  Cool:     %s\n" % cool
        )

if __name__ == '__main__':
    try:
        ThermostatApp().run()
    except KeyboardInterrupt:
        pass
