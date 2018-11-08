import numpy as np

from scipy.interpolate import RectBivariateSpline as interp
from numpy.random import normal

import matplotlib.pyplot as plt
import matplotlib.dates as md
xfmt = md.DateFormatter('%H:%M')

from IO import openMeteo, openRadar, getRadarData, getMeteoData
from plotter import plot_ddv, plot_radar_vel, scatterplot, plot_wind_polar

from datetime import datetime
import glob

start = datetime(2018, 11, 1, 0, 0, 0)
stop = datetime(2018, 11, 1, 22, 0, 0)

# The code will return error if within the time range the number of range gates change.
# But if the ranges change while the number is kept constant it will not give any alert

# Unpacking weather model file
model_height, meteo_dt, meteo_ts, uwind, vwind = getMeteoData(start, stop)
meteo_wind_speed = np.hypot(uwind, vwind)
meteo_wind_alpha = np.arctan2(uwind, vwind)
plot_wind_polar(meteo_dt, model_height, meteo_wind_speed, meteo_wind_alpha*180.0/np.pi, title='model wind speed and direction')

# Unpacking radar file
m10_range, m10_dt, m10_ts, m10_azimuth, m10_elevation, m10_velg = getRadarData(start, stop, 'mira10')
m36_range, m36_dt, m36_ts, m36_azimuth, m36_elevation, m36_velg = getRadarData(start, stop, 'mira36')

plot_radar_vel(m36_dt, m36_range, m36_velg, minmax=[-2,1], colorlabel='Measured MDV mira-36 [m/s]')
plot_radar_vel(m10_dt, m10_range, m10_velg, minmax=[-2,1], colorlabel='Measured MDV mira-10 [m/s]')

# HERE WE NEED SOME PROCEDURE TO SELECT ICE CLOUDS.
# POSSIBLE CHOICES INCLUDE DWR

# HERE WE NEED FILTERS TO SELECT APPROPRIATE DATA

##############
##############
# SIMULATION #
##############
##############

# Set mispointing direction
theta = 0.5*np.pi/180.0
phi = 30*np.pi/180.0

# Compute the wind component parallel to the meridional mispointing plane
wind_parallel = meteo_wind_speed*np.cos(meteo_wind_alpha-phi)
dual_doppler_velocity = wind_parallel*np.sin(theta)

plot_ddv(meteo_dt, model_height, dual_doppler_velocity, colorlabel='Simulated DDV [m/s]')
ax = scatterplot(meteo_wind_alpha.flatten()*180.0/np.pi,
                 (dual_doppler_velocity/meteo_wind_speed).flatten())
ax.set_title("Ideal data from the whole domain")
ax.set_xlabel('azimuth [deg]')
ax.set_ylabel('DDV [m/s]')
# HERE it would be nice to have some ideal sinusoids that are function of theta and phi deviations from the vertical

# Create a map of doppler shift due to horizontal wind
# TODO: avoid interpolation when outside grid boundaries
windUInterpolator = interp(x=model_height, y=meteo_ts, z=uwind)
windVInterpolator = interp(x=model_height, y=meteo_ts, z=vwind)

iU = windUInterpolator(m36_range, m36_ts)
iV = windVInterpolator(m36_range, m36_ts)

int_wind_speed = np.hypot(iU, iV)
int_wind_alpha = np.arctan2(iU, iV)

plot_wind_polar(m36_dt, m36_range, int_wind_speed, int_wind_alpha*180.0/np.pi, title='interpolated wind speed and direction')

# OK, that is done.
# Now I should add some noise to the wind data and maybe also to the pointing data and then run the forward simulation
#

stdev = 3 # m/s
realU = iU + normal(loc=0.0, scale=stdev, size=iU.shape)
realV = iV + normal(loc=0.0, scale=stdev, size=iV.shape)
real_wind_speed = np.hypot(realU, realV)
real_wind_alpha = np.arctan2(realU, realV)
plot_wind_polar(m36_dt, m36_range, real_wind_speed, real_wind_alpha*180.0/np.pi, title='simulated wind with gaussian noise')

real_wind_parallel = real_wind_speed*np.cos(real_wind_alpha-phi)
real_ddv = real_wind_parallel*np.sin(theta)

mask = int_wind_speed > 10.0 # we just want significant winds otherwise it is noisy
plot_ddv(m36_dt, m36_range, real_ddv)
ax = scatterplot(int_wind_alpha[mask].flatten()*180.0/np.pi,
                 (real_ddv[mask]/int_wind_speed[mask]).flatten())
ax.set_title("All potential points from wind")
ax.set_xlabel('azimuth [deg]')
ax.set_ylabel('DDV [m/s]')


m10_velg = m36_velg + real_ddv
plot_radar_vel(m36_dt, m36_range, m10_velg, minmax=[-2,1], colorlabel='Simulated MDV mira-10 [m/s]')

measured_ddv = m10_velg - m36_velg
plot_ddv(m36_dt, m36_range, measured_ddv)
ax =scatterplot(int_wind_alpha[mask].flatten()*180.0/np.pi,
                (measured_ddv[mask]/int_wind_speed[mask]).flatten())
ax.set_title("Synthetic measured data")
ax.set_xlabel('azimuth [deg]')
ax.set_ylabel('DDV [m/s]')
