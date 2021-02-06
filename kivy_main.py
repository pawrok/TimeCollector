import datetime
from functools import partial

from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, Rectangle, Canvas, ClearBuffers, ClearColor
from kivy.uix.scrollview import ScrollView
from kivy.uix.recycleview import RecycleView 
from kivy.properties import ListProperty, StringProperty, ObjectProperty, \
        NumericProperty, BooleanProperty, AliasProperty
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.config import Config
from kivy.clock import Clock

import kivy

Config.set('graphics', 'width', '200')
Config.set('graphics', 'height', '650')

# kivy.require('1.9.0')

class RootLayout(BoxLayout):
    pass

class TrackerContainer(BoxLayout):
    ID = NumericProperty(0)
    has_timer = NumericProperty(0)
    name = StringProperty('')
    timer_event = None
    total_duration = NumericProperty(0)
    current_duration = NumericProperty(0)
    
class PlayButton(Button):
    btn_source = StringProperty('play-button.png')

class TimeTracker(App):
    def build(self):
        self.trackers_count = -1
        #TODO: dictionary of ids and corresponding indices
        Builder.load_file('root.kv')
        self.root = RootLayout()
        return self.root

    def find_tracker_index(self, timer_id):
        for i in range(len(self.root.ids['box'].children)):
            if self.root.ids['box'].children[i].ID == timer_id:
                index = i
        return index

    def start_timer(self, timer_id):
        timer_index = self.find_tracker_index(timer_id)
        
        now = datetime.datetime.now()
        event = Clock.schedule_interval(partial(self.update_label, start_time=now, timer_id=timer_index), 0.1)
        return event

    def stop_timer(self, timer, timer_id):
        timer_index = self.find_tracker_index(timer_id)
        
        self.root.ids['box'].children[timer_index].total_duration += self.root.ids['box'].children[timer_index].current_duration
        timer.cancel()

    def update_label(self, dt, start_time, timer_id):
        diff = datetime.datetime.now() - start_time
        self.root.ids['box'].children[timer_id].current_duration = diff.total_seconds()
        
        total = self.root.ids['box'].children[timer_id].current_duration + self.root.ids['box'].children[timer_id].total_duration
        self.root.ids['box'].children[timer_id].ids['time'].text = str(datetime.timedelta(seconds=total)).split('.')[0]

    def create_new_tracker(self, new_name):
        self.trackers_count += 1
        new_id = self.trackers_count
        self.root.ids['box'].add_widget(TrackerContainer(ID=new_id, name=new_name))
        self.root.ids['box'].height += TrackerContainer.height.defaultvalue

if __name__ == '__main__':
    TimeTracker().run()
