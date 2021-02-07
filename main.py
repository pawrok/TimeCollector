import datetime
from functools import partial
from tinydb import TinyDB, Query

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

Config.set('graphics', 'width', '180')
Config.set('graphics', 'height', '650')

class RootLayout(BoxLayout):
    pass

class TrackerContainer(BoxLayout):
    ID = NumericProperty(0)
    timer_on = NumericProperty(0)
    name = StringProperty('')
    timer_event = None
    total_duration = NumericProperty(0.001)
    current_duration = NumericProperty(0.001)
    
class TimeTracker(App):
    def build(self):
        self.title = 'Time Tracker'
        # self.icon = 'myicon.png'
        self.trackers_indices = {}
        self.db = TinyDB('db.json')

        Builder.load_file('root.kv')
        self.root = RootLayout()
        self.load_trackers()
        return self.root

    def match_ids_to_indices(self):
        for index in range(len(self.root.ids['box'].children)):
            id = self.root.ids['box'].children[index].ID
            self.trackers_indices[id] = index

    def start_timer(self, timer_id):
        self.stop_all_timers()
        now = datetime.datetime.now()
        event = Clock.schedule_interval(partial(self.update_label, start_time=now, timer_id=timer_id), 0.06)

        timer_index = self.trackers_indices.get(timer_id)
        self.root.ids['box'].children[timer_index].timer_on = 1
        self.root.ids['box'].children[timer_index].ids['img'].source = 'icons/pause.png'

        return event

    def start_stop_timer(self, timer_id):
        timer_index = self.trackers_indices.get(timer_id)
        if not self.root.ids['box'].children[timer_index].timer_on:
            self.root.ids['box'].children[timer_index].timer_event = self.start_timer(timer_id)
        else:
            self.stop_timer(timer_id)



    def stop_timer(self, timer_id):
        timer_index = self.trackers_indices.get(timer_id)
        self.root.ids['box'].children[timer_index].timer_on = 0
        self.root.ids['box'].children[timer_index].ids['img'].source = 'icons/play-button.png'
        self.root.ids['box'].children[timer_index].timer_event.cancel()
        self.root.ids['box'].children[timer_index].total_duration += self.root.ids['box'].children[timer_index].current_duration

    def stop_all_timers(self):
        for id, index in self.trackers_indices.items():
            if self.root.ids['box'].children[index].timer_on == 1:
                self.stop_timer(id)

    def update_label(self, dt, start_time, timer_id):
        timer_index = self.trackers_indices.get(timer_id)

        diff = datetime.datetime.now() - start_time
        self.root.ids['box'].children[timer_index].current_duration = diff.total_seconds()
        
        total = self.root.ids['box'].children[timer_index].current_duration + self.root.ids['box'].children[timer_index].total_duration
        t = str(datetime.timedelta(seconds=total)).split('.')
        self.root.ids['box'].children[timer_index].ids['time'].text = t[0] + '.' + t[1][0:2]

    def create_new_tracker(self, new_name, id=-1, total_time=0.001):
        if id == -1:
            if self.db.all():
                max_id = sorted(self.db.all(), key=lambda k: k['tracker_id'])[-1]['tracker_id']
            else:
                max_id = -1
            new_id = max_id + 1
            self.db.insert({'tracker_name': new_name, 'tracker_id': new_id, 'total_time': total_time, 'past_data': {} })
        else:
            new_id = id

        self.root.ids['box'].add_widget(TrackerContainer(ID=new_id, name=new_name, total_duration=total_time))
        self.root.ids['box'].height += TrackerContainer.height.defaultvalue

        self.match_ids_to_indices()
        timer_index = self.trackers_indices.get(new_id)
        t = str(datetime.timedelta(seconds=total_time)).split('.')
        print(t, total_time)
        self.root.ids['box'].children[timer_index].ids['time'].text = t[0] + '.' + t[1][0:2]

    def load_trackers(self):
        for item in self.db:
            print(item)
            self.create_new_tracker(item['tracker_name'], item['tracker_id'], item['total_time'])

    def on_stop(self):
        " saves all timer's time when exiting the app "

        self.stop_all_timers()

        q = Query()

        for index in range(len(self.root.ids['box'].children)):
            id = self.root.ids['box'].children[index].ID
            total_time = self.root.ids['box'].children[index].total_duration
            self.db.update({'total_time': total_time}, q.tracker_id == id)


if __name__ == '__main__':
    TimeTracker().run()

# TODO: stop tracker when another is started
#       reset button
#       event saving statistics from a day to db (add and update)
#       matplotlib creating plots and loading them to kivy