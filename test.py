from tinydb import TinyDB, Query
import matplotlib.pyplot as plt
import numpy as np

def plot_past_data():
    db = TinyDB('db.json')
    all_data = db.all()
    plt.xkcd()
    # for item in all_data:
    #     plot_date = []
    #     plot_duration = []
    #     for key, value in item['past_data'].items():
    #         plot_date.append(key)
    #         plot_duration.append(value)

    #     # plt.xkcd()
    #     plt.plot(plot_date, plot_duration)
    # plt.show()

    ' pie '
    labels = []
    durations = []
    for item in all_data:
        labels.append(item['tracker_name'])
        sum_h = 0
        for key, value in item['past_data'].items():
            sum_h += value
        durations.append(sum_h)

    def func(pct, allvals):
        absolute = int(pct/100.*np.sum(allvals))
        return "{:.1f}%\n({:d} h)".format(pct, absolute)
    
    fig1, ax1 = plt.subplots()
    ax1.pie(durations, labels=labels, autopct=lambda pct: func(pct, durations),
        startangle=90)
    ax1.axis('equal')
    plt.show()

plot_past_data()