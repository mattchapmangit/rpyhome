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
from kivy.uix.gridlayout import GridLayout
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
import requests
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
    def __init__(self, temp, lomax, himax, label, **kwargs):
        self.temp = temp
        self.rng = range(lomax, himax+1)
        self.label = label
        super().__init__(text=self.get_text(),
#                         group='heat/cool',
                         background_color=(0,0,0,0),
                         markup=True,
                         **kwargs)

    def set_text(self):
        self.text = self.get_text()

    def get_text(self):
        text = '%s to\n[size=30]%d[sup]o[/sup][/size]' % (self.label, self.temp)
        if self.state == 'down':
            color = '1c6ed4' if self.label == 'Cool' else 'cf1943'
            text = '[color=#%s]%s[/color]' % (color, text)
        return text


class DateTime(Label):
    def __init__(self, fmt, align, seconds, **kwargs):
        self.fmt = fmt
        self.align = align
        self.seconds = seconds
        super().__init__(text=self.get_text(),
                         markup=True,
                         **kwargs)
        Clock.schedule_once(self.update, seconds)

    def get_text(self):
        text = datetime.today().strftime(self.fmt).lstrip('0')
        return '[size=30]%s[/size]' % text

    def update(self, wtf):
        self.text = self.get_text()
        Clock.schedule_once(self.update, self.seconds)


class Forecast(GridLayout):
#    _alignment = dict(halign='left', size_hint=(None, None))
    _alignment = {}

    def __init__(self, **kwargs):
        super().__init__(cols=2, **kwargs)
        self.summaryimg = Image()
        self.summarylabel = Label(markup=True, **self._alignment)
        self.templabel = Label(**self._alignment)
        self.windlabel = Label(**self._alignment)

        self.add_widget(Label(text='[b]Today:[/b]', markup=True, **self._alignment))
        self.add_widget(Label(text='', **self._alignment))

        self.add_widget(self.summaryimg)
        self.add_widget(self.summarylabel)

        self.add_widget(Label(text='High:', **self._alignment))
        self.add_widget(self.templabel)

        self.add_widget(Label(text='Wind:', **self._alignment))
        self.add_widget(self.windlabel)
        Clock.schedule_once(self.update, 5)

    def update(self, wtf):
        try:
            self._update()
        except Exception as e:
            print('weather fail', e)

        # update once an hour
        Clock.schedule_once(self.update, 60 * 60)

    def _update(self):

        session = requests.Session()
        session.headers.update({'User-Agent': 'matt.chapman.us@gmail.com'})
        r = session.get('https://api.weather.gov/points/35.0517,-120.5494')
        if not r:
            return self
        addr = r.json().get('properties', {}).get('forecast', {})
        if not addr:
            return self
        forecast = session.get(addr)
        if not forecast:
            return self
        periods = forecast.json().get('properties', {}).get('periods', [])
        if len(periods) < 1:
            return self
        today = periods[0]

        icon = today['icon']
        fields = icon.split('/')
        fname = fields[-1].replace('medium', 'small')
        localfile = 'web/images/%s' % fname
        if not os.path.exists(localfile):
            addr = '/'.join(fields[:-1] + [fname])
            r = session.get(addr)
            print('update image %s' % localfile)
            with open(localfile, 'wb') as fp:
                fp.write(r.content)
            
        self.summaryimg.source = localfile
        self.summarylabel.text = '[b]%s[/b]' % today['shortForecast']
        self.templabel.text = str(today['temperature'])
        self.windlabel.text = today['windSpeed'] + ' ' + today['windDirection']


class HouseStatus(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(cols=2, **kwargs)
        self.garagelabel = Label(markup=True)

        self.add_widget(Label(text='[b]House:[/b]', markup=True))
        self.add_widget(Label(text=''))

        self.add_widget(Label(text='Garage:'))
        self.add_widget(self.garagelabel)
        Clock.schedule_once(self.update, 5)

    def update(self, wtf):
        if 'Open' in self.garagelabel.text:
            self.garagelabel.text = 'Closed'
        else:
            color = 'cf1943'
            text = '[b][color=#%s]Open[/color][/b]' % color
            self.garagelabel.text = text
        Clock.schedule_once(self.update, 5)


class WiFiButton(Button):
    def __init__(self, **kwargs):
        super().__init__(text='dont touch', **kwargs)
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

"""
591 Woodgreen Way
Nipomo, CA 93444
35.051686, -120.549374
"""

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
        self.weatherlabel = Forecast()
        self.statuslabel = HouseStatus()
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
