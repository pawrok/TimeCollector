import datetime
from functools import partial
from tinydb import TinyDB, Query
import matplotlib.pyplot as plt
import matplotlib as mpl

from kivy.config import Config
Config.set('graphics', 'width', '300')
Config.set('graphics', 'height', '650')

from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.dropdown import DropDown
from kivy.properties import StringProperty, NumericProperty, DictProperty
from kivy.clock import Clock
import kivy


class RootLayout(BoxLayout):
    pass

class RenamePopup(Popup):
    tr_id = NumericProperty(0)
    def __init__(self, ID, **kwargs): 
        super(RenamePopup, self).__init__(**kwargs)
        self.tr_id = ID

class TrackerContainer(BoxLayout):
    ID = NumericProperty(0)
    timer_on = NumericProperty(0)
    name = StringProperty('')
    timer_event = None

    # time saved only in db needed to load tracker with last time
    total_duration = NumericProperty(0.001)
    # current time based on current time and tracker start time diff
    current_duration = NumericProperty(0.001)
    # time stored after refresh
    refresh_time = NumericProperty(0.001)
    
class TimeTracker(App):
    def build(self):
        self.title = 'Time Collector'
        self.icon = 'icons/hourglass.png'
        self.trackers_indices = {}
        self.db = TinyDB('db.json')

        Builder.load_file('root.kv')
        self.root = RootLayout()
        self.load_trackers()
        self.reset_stats_at_new_day()
        return self.root

    def match_ids_to_indices(self):
        self.trackers_indices = {}
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
        tracker = self.root.ids['box'].children[timer_index]
        if not tracker.timer_on:
            tracker.timer_event = self.start_timer(timer_id)
        else:
            self.stop_timer(timer_id)

    def stop_timer(self, timer_id):
        timer_index = self.trackers_indices.get(timer_id)
        tracker = self.root.ids['box'].children[timer_index]
        tracker.timer_on = 0
        tracker.ids['img'].source = 'icons/play.png'
        tracker.timer_event.cancel()
        tracker.total_duration += tracker.current_duration
        tracker.refresh_time += tracker.current_duration

    def stop_all_timers(self):
        for id, index in self.trackers_indices.items():
            if self.root.ids['box'].children[index].timer_on == 1:
                self.stop_timer(id)

    def update_label(self, dt, start_time, timer_id):
        timer_index = self.trackers_indices.get(timer_id)
        tracker = self.root.ids['box'].children[timer_index]

        diff = datetime.datetime.now() - start_time
        tracker.current_duration = diff.total_seconds()
        
        total = tracker.current_duration + tracker.refresh_time
        t = str(datetime.timedelta(seconds=total)).split('.')
        tracker.ids['time'].text = t[0] + '.' + t[1][0:2]

    def create_new_tracker(self, new_name, id=-1, total_time=0.001, refresh_time=0.001):
        if id == -1:
            if self.db.all():
                max_id = sorted(self.db.all(), key=lambda k: k['tracker_id'])[-1]['tracker_id']
            else:
                max_id = -1
            new_id = max_id + 1
            self.db.insert({'tracker_name': new_name, 'tracker_id': new_id, 'total_time': total_time, 'refresh_time': refresh_time, 'past_data': {} })
        else:
            new_id = id

        self.root.ids['box'].add_widget(TrackerContainer(ID=new_id, name=new_name, total_duration=total_time,
            refresh_time=refresh_time))
        self.root.ids['box'].height += TrackerContainer.height.defaultvalue * 1.2   # 1.2 == padding

        self.match_ids_to_indices()
        timer_index = self.trackers_indices.get(new_id)
        t = str(datetime.timedelta(seconds=total_time)).split('.')
        self.root.ids['box'].children[timer_index].ids['time'].text = t[0] + '.' + t[1][0:2]

    def refresh_tracker_time(self, timer_id):
        timer_index = self.trackers_indices.get(timer_id)
        tracker = self.root.ids['box'].children[timer_index]

        tracker.refresh_time = 0.001

        zero_time = str(datetime.timedelta(seconds=0.001)).split('.')
        tracker.ids['time'].text = zero_time[0] + '.' + zero_time[1][0:2]
        
        if tracker.timer_on == 1:
            self.stop_timer(timer_id)

    def delete_tracker(self, timer_id):
        timer_index = self.trackers_indices.get(timer_id)
        tracker = self.root.ids['box'].children[timer_index]
        if tracker.timer_on == 1:
            self.stop_timer(timer_id)
        self.root.ids['box'].remove_widget(tracker)
        self.match_ids_to_indices()
        self.root.ids['box'].height -= TrackerContainer.height.defaultvalue
        self.db.remove(Query().tracker_id == timer_id)

    def rename_tracker(self, timer_id, new_name):
        timer_index = self.trackers_indices.get(timer_id)
        tracker = self.root.ids['box'].children[timer_index]
        tracker.name = new_name
        self.db.update({'tracker_name': new_name}, Query().tracker_id == timer_id)

    def load_trackers(self):
        for item in self.db:
            self.create_new_tracker(item['tracker_name'], item['tracker_id'], item['total_time'], item['refresh_time'])

    def on_stop(self):
        " saves all timer's time when exiting the app "

        self.stop_all_timers()

        trackers = self.root.ids['box'].children

        for index in range(len(trackers)):
            id = trackers[index].ID
            total_time = trackers[index].total_duration
            refresh_time = trackers[index].refresh_time

            self.db.update({'total_time': total_time, 'refresh_time': refresh_time}, Query().tracker_id == id)
            self.save_day_data(id, total_time)

    def save_day_data(self, tracker_id, time):
        today = datetime.date.today().strftime("%d/%m/%y")
        past_data = self.db.search(Query().tracker_id == tracker_id)[0]['past_data']
        if past_data == {}:
            past_data[today] = 0
        past_data[today] += time
        self.db.upsert({'past_data': past_data}, Query().tracker_id == tracker_id)

    def reset_stats_at_new_day(self):
        today = datetime.date.today().strftime("%d/%m/%y")
        trackers = self.root.ids['box'].children
        
        for index in range(len(trackers)):
            tracker_id = trackers[index].ID
            past_data = self.db.search(Query().tracker_id == tracker_id)[0]['past_data']
            if today not in past_data:
                self.refresh_tracker_time(tracker_id)

    def plot_past_data(self):
        all_data = self.db.all()
        # plt.xkcd()
        mpl.rcParams.update({'font.size': 17})
        plt.style.use('dark_background')

        ' linear, every tracker '
        for item in all_data:
            plot_date = []
            plot_duration = []
            for key, value in item['past_data'].items():
                plot_date.append(key.split('/')[0])
                plot_duration.append(value/3600)
            plt.plot(plot_date, plot_duration)

        plt.title('Time spent each day', fontsize=22)
        plt.xlabel('Day', fontsize=18)
        plt.ylabel('Time (h)', fontsize=18)
        plt.gcf().subplots_adjust(bottom=0.15)
        plt.gcf().subplots_adjust(left=0.15)
        plt.savefig("linear.png")

        ' pie '
        labels = []
        durations = []
        for item in all_data:
            labels.append(item['tracker_name'])
            sum_h = 0
            for key, value in item['past_data'].items():
                sum_h += value
            durations.append(sum_h/3600)

        def func(pct, allvals):
            absolute = int(pct/100.*sum(allvals))
            if pct < 3:
                return ""
            else:
                return "{:.1f}%\n({:d} h)".format(pct, absolute)
        
        fig1, ax1 = plt.subplots()
        explode = len(all_data) * (0.05,)
        patches, texts, autotexts = ax1.pie(durations, labels=labels,
            autopct=lambda pct: func(pct, durations), startangle=90, pctdistance=0.72, explode=explode)
        
        
        for text in texts:
            text.set_color('white')
            text.set_fontsize(12)

        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_fontsize(12)

        # draw circle
        centre_circle = plt.Circle((0,0),0.5,fc='black')
        fig = plt.gcf()
        fig.gca().add_artist(centre_circle)

        plt.title('Total time comparison', fontsize=18)
        plt.savefig("pie.png", bbox_inches = 'tight',
            pad_inches = 0)


if __name__ == '__main__':
    TimeTracker().run()

# TODO: 
#       (export to excel)
#       (smaller miliseconds)
#       (shortcuts)