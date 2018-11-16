import matplotlib.pyplot as plt
import matplotlib.dates as md
import numpy as np
import cmocean

xfmt = md.DateFormatter('%m%d-%H')

## BASE PLOTS ##

def scatterplot(x, y, ax=None, **kwargs):
  if ax is None:
      fig, ax = plt.subplots(1,1)

  ax.scatter(x, y, **kwargs)
  ax.grid()
  plt.show(block=False)
  return ax

def plot_timeheight(time, hgt, values, cmap='viridis', minmax=None, ax=None, colorlabel=None):
  if cmap is None:
    cmap = 'viridis'

  if minmax is None:
    absmax = np.nanmax(np.abs(real_ddv))
    minmax = [-absmax, absmax]

  if ax is None:
    fig, ax = plt.subplots(1,1)
  
  mesh = ax.pcolormesh(time, hgt, values, cmap=cmap, vmin=minmax[0], vmax=minmax[1])
  plt.colorbar(mesh, ax=ax, label=colorlabel)
  ax.xaxis.set_major_formatter(xfmt)
  plt.show(block=False)
  return ax


## EVOLVED PLOTS ##


def plot_ddv(time, hgt, ddv, cmap='Spectral', minmax=None, ax=None, **kwargs):
  if minmax is None:
    absmax = np.nanmax(np.abs(ddv))
    minmax = [-absmax, absmax]

  if ax is None:
    fig, ax = plt.subplots(1,1)
  
  plot_timeheight(time, hgt, ddv, cmap, minmax, ax, **kwargs)
  return ax

def plot_radar_vel(time, hgt, vel, cmap='viridis', minmax=None, ax=None, **kwargs):
  if minmax is None:
    absmax = np.nanmax(np.abs(vel))
    minmax = [-absmax, absmax]

  if ax is None:
    fig, ax = plt.subplots(1,1)
  
  plot_timeheight(time, hgt, vel, cmap, minmax, ax, **kwargs)
  return ax


def plot_wind_polar(time, hgt, wind_s, wind_a, minmax=None, axs=None, title=None, **kwargs):
  if minmax is None:
    minmax=[[0,40],[-180,180]]

  if axs is None:
    fig, axs = plt.subplots(2, 1, sharex=True)

  plot_timeheight(time, hgt, wind_s, minmax=minmax[0], ax=axs[0],
                  colorlabel='Wind speed [m/s]', **kwargs)
  
  plot_timeheight(time, hgt, wind_a, minmax=minmax[1], ax=axs[1],
                  colorlabel='Wind direction [deg]', cmap='hsv')
  
  if title is not None:
    fig.suptitle(title)
  plt.tight_layout()
  plt.show(block=False)
  return fig, axs