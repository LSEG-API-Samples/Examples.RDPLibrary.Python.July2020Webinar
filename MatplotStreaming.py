# -*- coding: utf-8 -*-
"""
Created on Mon Jun 15 13:21:21 2020

@author: umern
"""

from itertools import count
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.animation import FuncAnimation
import time
import refinitiv.dataplatform as rdp
import configparser as cp

config = cp.ConfigParser()
config.read("config.cfg")
rdp.open_platform_session(
    config['session']['app_key'],
    rdp.GrantPassword(
        username=config['session']['user'],
        password=config['session']['password']
    )
)

# Back fill tick history
global bid_list, ask_list
ric = 'EUR='
ticks = 100
df = rdp.get_historical_price_events(ric, fields=['BID', 'ASK'], count=ticks)
bid_list = pd.to_numeric(df['BID']).to_list()
ask_list = pd.to_numeric(df['ASK']).to_list()
bid_list.reverse()
ask_list.reverse()

# Live prices
streaming_prices = rdp.StreamingPrices(
    universe=[ric],
    fields=['BID', 'ASK']
)
streaming_prices.open()

def animate(i):
    bid = streaming_prices[ric]['BID']
    ask = streaming_prices[ric]['ASK']
    re_plot = False
    if bid != bid_list[ticks - 1] or ask != ask_list[ticks - 1]:
        bid_list.pop(0)
        bid_list.append(streaming_prices[ric]['BID'])
        ask_list.pop(0)
        ask_list.append(streaming_prices[ric]['ASK'])
        re_plot = True

    if re_plot:
        lower_y = min(bid_list) * 0.9995
        upper_y = max(ask_list) * 1.0005
        plt.cla()
        plt.ylim(lower_y, upper_y)
        plt.plot(bid_list, label='Bid', )
        plt.plot(ask_list, label='Ask')
        plt.legend(loc='upper left')
        plt.title(f"Streaming Prices for : {ric}",color='b')
        plt.tight_layout()

# Wait for connecton to server, request to be processed etc.
time.sleep(1)

fig = plt.gcf()
fig.canvas.set_window_title('Streaming with Matplotlib')
ani = FuncAnimation(fig, animate, interval=300)

plt.tight_layout()
plt.show()

