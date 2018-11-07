import netCDF4
import numpy as np
from datetime import datetime, timedelta
import glob

# Setting some paths
meteo_path = '/data/data_hatpro/jue/cloudnet/juelich/processed/categorize/'
# '/data/data_hatpro/jue/cloudnet/juelich/processed/categorize/2018/20181103_juelich_categorize.nc'
mira36_path = '/data/hatpro/jue/data/mmclx/incoming/'
# '/data/hatpro/jue/data/mmclx/incoming/20181103_1200.znc'
mira10_path = '/data/obs/site/jue/joyrad10/####DUNNO####'


def getMeteoData(start, stop):
  files = glob.glob(meteo_path+str(start.year-1)+'/*_juelich_categorize.nc')
  files = files + glob.glob(meteo_path+str(start.year)+'/*_juelich_categorize.nc')
  files = files + glob.glob(meteo_path+str(start.year+1)+'/*_juelich_categorize.nc')
  datetimes = [datetime.strptime(i[-30:-22],'%Y%m%d') for i in files]
  datetimes = [i for i in datetimes if i >= start-timedelta(days=1) and i <= stop]
  ms_dt = []
  ms_ts = []
  ms_uwind = []
  ms_vwind = []
  for dt in datetimes:
    meteo_filename = meteo_path + dt.strftime('%Y/')  + dt.strftime('%Y%m%d') + '_juelich_categorize.nc'
    print(meteo_filename)
    model_height, meteo_dt, meteo_ts, uwind, vwind = openMeteo(meteo_filename)
    ms_dt.append(meteo_dt)
    ms_ts.append(meteo_ts)
    ms_uwind.append(uwind)
    ms_vwind.append(vwind)
    print(dt, uwind.shape)
  return model_height, np.hstack(ms_dt), np.hstack(ms_ts), np.hstack(ms_uwind), np.hstack(ms_vwind)


def getRadarData(start, stop, radar='mira36'):
  if radar == 'mira36':
    radar_path = mira36_path
  elif radar == 'mira10':
    radar_path = mira10_path
  else:
    raise ValueError('Unrecognized radar name {}'.format(radar))
  files = glob.glob(radar_path+str(start.year-1)+'*.znc')
  files = files + glob.glob(radar_path+str(start.year)+'*.znc')
  files = files + glob.glob(radar_path+str(start.year+1)+'*.znc')
  files = [i for i in files if 'solscan' not in i]
  datetimes = [datetime.strptime(i[-17:-4],'%Y%m%d_%H%M') for i in files]
  datetimes = [i for i in datetimes if i >= start and i <= stop]
  rs_dt = []
  rs_ts = []
  rs_azimuth = []
  rs_elevation = []
  rs_velg = []
  for dt in datetimes:
    radar_filename = radar_path + dt.strftime('%Y%m%d_%H%M') + '.znc'
    print(radar_filename)
    r_rng, r_dt, r_ts, r_azimuth, r_elevation, r_velg = openRadar(radar_filename)
    rs_dt.append(r_dt)
    rs_ts.append(r_ts)
    rs_azimuth.append(r_azimuth)
    rs_elevation.append(r_elevation)
    rs_velg.append(r_velg)
    print(dt, r_velg.shape)
  return r_rng, np.hstack(rs_dt), np.hstack(rs_ts), np.hstack(rs_azimuth), np.hstack(rs_elevation), np.hstack(rs_velg)


def openMeteo(meteo_filename):
  # Unpacking weather model file
  meteo_nc = netCDF4.Dataset(meteo_filename,"r")
  meteo_vars = meteo_nc.variables
  model_height = meteo_vars['model_height'][:]
  uwind = meteo_vars['uwind'][:].T
  vwind = meteo_vars['vwind'][:].T
  meteo_dt = netCDF4.num2date(meteo_vars['time'][:], meteo_vars['time'].units)
  meteo_ts = netCDF4.date2num(meteo_dt, 'seconds since 1970-01-01 00:00:00')
  meteo_nc.close()

  return model_height, meteo_dt, meteo_ts, uwind, vwind


def openRadar(radar_filename):
  # Unpacking Mira-36 file
  radar_nc = netCDF4.Dataset(radar_filename,"r")
  altitude = float(radar_nc.Altitude.split()[0])
  radar_vars = radar_nc.variables
  radar_dt = netCDF4.num2date(radar_vars['time'][:], 'seconds since 1970-01-01 00:00:00')
  radar_ts = netCDF4.date2num(radar_dt, 'seconds since 1970-01-01 00:00:00')
  radar_range = radar_vars['range'][:] + altitude
  radar_azimuth = radar_vars['azi'][:]
  radar_elevation = radar_vars['elv'][:]
  if 'VELg' in radar_vars.keys():
    radar_vel = radar_vars['VELg'][:].T
  else:
    radar_vel = radar_vars['VELgc'][:].T
  # I have the feeling that even though the declared fill value is 9.9692099e36
  # the used number is -4.22687562e5
  radar_vel[radar_vel < -11] = np.nan
  radar_vel[:,np.abs(radar_elevation-90.0) > 0.1] = np.nan
  radar_nc.close()

  return radar_range, radar_dt, radar_ts, radar_azimuth, radar_elevation, radar_vel