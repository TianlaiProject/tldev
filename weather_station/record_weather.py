#import h5py
#import matplotlib.pyplot as plt
import numpy as np
import time
import os
import tlweather
import air_conditioner

output_dir = './data/'
localIP = '192.168.1.11'
interval = 60 # seconds; Do not modify this value!!!
header_str = '#Time\tSeconds1970\tRoomT\tRoomH\tSiteT\tDewpoint\tHumid\tPrecip\tWindDirec\tWindSpeed0m\tWindSpeed2m\tWindSpeed10m\tPressure\n'

no_data = {'temperature': -10000.0, 'dew_point': -10000.0, 'humidity': -10000.0,
           'precipitation': -10000.0, 'wind_direction': -10000.0, 'windspeed_current': -10000.0,
           'windspeed_2minaverage': -10000.0, 'windspeed_10minaverage': -10000.0, 'pressure': -10000.0}


with open('.proc_pid.txt', 'w') as pypid:
    pypid.write(str(os.getpid()) + '\n')

ws = tlweather.WeatherStation(localIP)
ac = air_conditioner.AirConditioner()

while 1:
    time.sleep(interval - int(time.strftime('%S')) - 5)
    while 1:
        now_sec = time.time()
        if time.strftime('%S', time.localtime(now_sec)) != '00':
            time.sleep(0.05)
        else:
            break
# Analog Room Temperature.
    try:
        ac_data = ac.getData()
        RoomT = ac_data['room_temperature']
        RoomH = ac_data['room_humidity']
    except:
        RoomT = -10000.0
        RoomH = -10000.0
# Weather Data.
    try:
        wd = ws.getData()
    except:
        wd = no_data

    today_str = time.strftime('%Y%m%d', time.localtime(now_sec))
    if not os.path.exists('%s%s' % (output_dir, today_str[:4])):
        os.mkdir('%s%s' % (output_dir, today_str[:4]))
    if not os.path.exists('%s%s/%s.txt' % (output_dir, today_str[:4], today_str)):
        with open('%s%s/%s.txt' % (output_dir, today_str[:4], today_str), 'a') as df:
            df.write(header_str)
        time.sleep(2)
        try:
            ws.setDevTime()
        except:
            pass

    data_str = '%.1f\t%.1f\t%.1f\t%.2f\t%.1f\t%.1f\t%.0f\t%.1f\t%.1f\t%.1f\t%.1f' % (RoomT, RoomH, wd['temperature'], wd['dew_point'], wd['humidity'], wd['precipitation'], wd['wind_direction'], wd['windspeed_current'], wd['windspeed_2minaverage'], wd['windspeed_10minaverage'], wd['pressure'])
    with open('%s%s/%s.txt' % (output_dir, today_str[:4], today_str), 'a') as df:
        df.write(time.strftime('%H%M%S', time.localtime(now_sec)))
        df.write('\t%.1f\t' % now_sec)
        df.write(data_str)
        df.write('\n')
    with open('%s%s' % ('./share/', 'newest_weather_data.txt'), 'w') as df:
        df.write(header_str)
        df.write(time.strftime('%Y%m%d%H%M%S', time.localtime(now_sec)))
        df.write('\t%.1f\t' % now_sec)
        df.write(data_str)
        df.write('\n')

