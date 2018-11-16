import numpy as np

from scipy.interpolate import interp2d
from numpy.random import normal

import matplotlib.pyplot as plt
plt.close('all')
import matplotlib.dates as md
xfmt = md.DateFormatter('%H:%M')

import importlib
import IO
import plotter
importlib.reload(IO)
importlib.reload(plotter)

from datetime import datetime
import glob

start = datetime(2018, 11, 6, 1, 0, 0)
stop = datetime(2018, 11, 13, 23, 0, 0)

# The code will return error if within the time range the number of range gates change.
# But if the ranges change while the number is kept constant it will not give any alert

# Unpacking weather model file
model_height, meteo_dt, meteo_ts, uwind, vwind = IO.getMeteoData(start, stop)
meteo_wind_speed = np.hypot(uwind, vwind)
meteo_wind_alpha = np.arctan2(uwind, vwind)
plotter.plot_wind_polar(meteo_dt, model_height, meteo_wind_speed, meteo_wind_alpha*180.0/np.pi, title='model wind speed and direction')

# Unpacking radar file
m10_range, m10_dt, m10_ts, m10_velg, m10_Z = IO.getRadarData(start, stop, 'joyrad10')
m36_range, m36_dt, m36_ts, m36_velg, m36_Z = IO.getRadarData(start, stop, 'joyrad35')

plotter.plot_radar_vel(m36_dt, m36_range, m36_velg, minmax=[-2,1], colorlabel='Measured MDV mira-36 [m/s]')
plotter.plot_radar_vel(m10_dt, m10_range, m10_velg, minmax=[-2,1], colorlabel='Measured MDV mira-10 [m/s]')

#def find_nearest(array, value):
#    # TODO limit the distance
#    return (np.abs(array - value)).argmin()
#vfind_nearest = np.vectorize(find_nearest, otypes=[np.int], excluded=['array'])

mira_ddv = m10_velg - m36_velg
plotter.plot_ddv(m36_dt, m36_range, mira_ddv, colorlabel='DDV [m/s] m10-m36',minmax=[-0.1,0.1])

# Create a map of doppler shift due to horizontal wind
# TODO: Check if this returns nan outside boundaries
windUInterpolator = interp2d(x=meteo_ts, y=model_height, z=uwind)
windVInterpolator = interp2d(x=meteo_ts, y=model_height, z=vwind)

iU = windUInterpolator(m36_ts, m36_range)
iV = windVInterpolator(m36_ts, m36_range)
int_wind_speed = np.hypot(iU, iV)
int_wind_alpha = np.arctan2(iU, iV)

plotter.plot_wind_polar(m36_dt, m36_range, int_wind_speed, int_wind_alpha*180.0/np.pi, title='interpolated wind speed and direction')
mask = int_wind_speed > 10.0 # we just want significant winds otherwise it is noisy
mask = mask*(np.abs(mira_ddv)<0.5)
mask = mask*(10.0*np.log10(m36_Z) > -20)
mask = mask*(10.0*np.log10(m36_Z) < -5)
mask[m36_range > 4000.0,:] = False

fig, ax = plt.subplots(1,1)
ax.hexbin(int_wind_alpha[mask].flatten()*180.0/np.pi,
          (mira_ddv[mask].flatten()/int_wind_speed[mask]).flatten(), bins='log')
ax.set_title("Fitting")
ax.set_xlabel('azimuth [deg]')
ax.set_ylabel('DDV/U')
ax.grid()
#plt.show()
plt.show(block=False)