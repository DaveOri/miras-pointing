# THIS IS AN OLD SCRIPT THAT DOES NOT WORK ANYMORE
import numpy as np

from scipy.interpolate import interp2d
from numpy.random import normal

import matplotlib.pyplot as plt
import matplotlib.dates as md
xfmt = md.DateFormatter('%H:%M')

from IO import openMeteo, openRadar, getRadarData, getMeteoData
from plotter import plot_ddv, plot_radar_vel, scatterplot, plot_wind_polar

from datetime import datetime
import glob

start = datetime(2018, 11, 1)
stop = datetime(2018, 11, 2)

# The code will return error if within the time range the number of range gates change.
# But if the ranges change while the number is kept constant it will not give any alert

# Unpacking weather model file
model_height, meteo_dt, meteo_ts, uwind, vwind = getMeteoData(start, stop)
meteo_wind_speed = np.hypot(uwind, vwind)
meteo_wind_alpha = np.arctan2(uwind, vwind)
plot_wind_polar(meteo_dt, model_height, meteo_wind_speed, meteo_wind_alpha*180.0/np.pi, title='model wind speed and direction')

# Unpacking radar file
#m10_range, m10_dt, m10_ts, m10_azimuth, m10_elevation, m10_velg, m10_Z = getRadarData(start, stop, 'joyrad10')
#m36_range, m36_dt, m36_ts, m36_azimuth, m36_elevation, m36_velg, m36_Z = getRadarData(start, stop, 'joyrad35')
m10_range, m10_dt, m10_ts, m10_velg, m10_Z = getRadarData(start, stop, 'joyrad10')
m36_range, m36_dt, m36_ts, m36_velg, m36_Z = getRadarData(start, stop, 'joyrad35')

plot_radar_vel(m36_dt, m36_range, m36_velg, minmax=[-2,1], colorlabel='Measured MDV mira-36 [m/s]')
plot_radar_vel(m10_dt, m10_range, m10_velg, minmax=[-2,1], colorlabel='Measured MDV mira-10 [m/s]')

def find_nearest(array, value):
    # TODO limit the distance
    return (np.abs(array - value)).argmin()
vfind_nearest = np.vectorize(find_nearest, otypes=[np.int], excluded=['array'])

time_idx = np.unique(vfind_nearest(array=m10_ts,value=m36_ts))
hgt_idx = np.unique(vfind_nearest(array=m10_range, value=m36_range))
time_mesh, hgt_mesh = np.meshgrid(time_idx,hgt_idx)
m10_velg_grid36 = m10_velg[hgt_mesh,time_mesh]
m10_Z_grid36 = m10_Z[hgt_mesh,time_mesh]
m10_dt_grid36 = m10_dt[time_idx]
m10_ts_grid36 = m10_ts[time_idx]
m10_range_grid36 = m10_range[hgt_idx]
plot_radar_vel(m10_dt_grid36, m10_range_grid36, m10_velg_grid36, minmax=[-2,1], colorlabel='Regridded MDV mira-10 [m/s]')

time_idx = (vfind_nearest(array=m36_ts,value=m10_ts_grid36))
hgt_idx = (vfind_nearest(array=m36_range, value=m10_range_grid36))
time_mesh, hgt_mesh = np.meshgrid(time_idx,hgt_idx)
m36_velg_grid = m36_velg[hgt_mesh,time_mesh]
m36_Z_grid = m36_Z[hgt_mesh,time_mesh]
m36_dt_grid = m36_dt[time_idx]
m36_ts_grid = m36_ts[time_idx]
m36_range_grid = m36_range[hgt_idx]
plot_radar_vel(m36_dt_grid, m36_range_grid, m36_velg_grid, minmax=[-2,1], colorlabel='Regridded MDV mira-36 [m/s]')

mira_ddv = m10_velg_grid36 - m36_velg_grid
plot_ddv(m36_dt_grid, m36_range_grid, mira_ddv, colorlabel='DDV [m/s] m10-m36',minmax=[-0.1,0.1])

# Create a map of doppler shift due to horizontal wind
# TODO: Check if this returns nan outside boundaries
windUInterpolator = interp2d(y=model_height, x=meteo_ts, z=uwind)
windVInterpolator = interp2d(y=model_height, x=meteo_ts, z=vwind)

iU = windUInterpolator(m36_ts_grid, m36_range_grid)
iV = windVInterpolator(m36_ts_grid, m36_range_grid)
int_wind_speed = np.hypot(iU, iV)
int_wind_alpha = np.arctan2(iU, iV)

plot_wind_polar(m36_dt_grid, m36_range_grid, int_wind_speed, int_wind_alpha*180.0/np.pi, title='interpolated wind speed and direction')
mask = int_wind_speed > 10.0 # we just want significant winds otherwise it is noisy
mask = mask*(np.abs(mira_ddv)<0.5)
mask = mask*(10.0*np.log10(m36_Z_grid) > -20)
mask = mask*(10.0*np.log10(m36_Z_grid) < -5)
mask[m36_range_grid > 4000.0,:] = False
ax = scatterplot(int_wind_alpha[mask].flatten()*180.0/np.pi,
                (mira_ddv[mask]/int_wind_speed[mask]).flatten())
ax.set_title("Fitting")
ax.set_xlabel('azimuth [deg]')
ax.set_ylabel('DDV [m/s]')

fig, ax = plt.subplots(1,1)
ax.hexbin(int_wind_alpha[mask].flatten()*180.0/np.pi,
          (mira_ddv[mask].flatten()/int_wind_speed[mask]).flatten(), bins='log')
ax.set_title("Fitting")
ax.set_xlabel('azimuth [deg]')
ax.set_ylabel('DDV/U')
ax.grid()
plt.show(block=False)

