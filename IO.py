import netCDF4
import numpy as np
from datetime import datetime, timedelta
import glob

# Setting some paths
radar_root = '/data/optimice/tripex-pol/'
meteo_path = '/data/data_hatpro/jue/cloudnet/juelich/processed/categorize/'
meteo_time = '%Y%m%d'

mira36_path = radar_root + 'joyrad35/resampled/'
mira10_path = radar_root + 'joyrad10/resampled/'
radar_time = '%Y%m%d'


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
  dt = np.hstack(ms_dt)
  mask = (dt>=start)*(dt<=stop)
  dt = dt[mask]
  ts = np.hstack(ms_ts)[mask]
  uwind=np.hstack(ms_uwind)[:,mask]
  vwind=np.hstack(ms_vwind)[:,mask]
  return model_height, dt, ts, uwind, vwind


def getRadarData(start, stop, radar='joyrad35'):
  def radar_subpath(dt,radar):
    return dt.strftime('%Y%m%d')+'_mon_'+radar+'.nc'
  if radar == 'joyrad35':
    radar_path = mira36_path
    radar_endpath = '*_mon_joyrad35.nc'
  elif radar == 'joyrad10':
    radar_path = mira10_path
    radar_endpath = '*_mon_joyrad10.nc'
  else:
    raise ValueError('Unrecognized radar name {}'.format(radar))
  files = glob.glob(radar_path+radar_endpath, recursive=True)
  datetimes = [datetime.strptime(i[-24:-16], radar_time) for i in files]
  datetimes = [i for i in datetimes if i.date() >= start.date() and i <= stop]
  rs_dt = []
  rs_ts = []
  rs_velg = []
  rs_Z = []
  for dt in datetimes:
    radar_filename = radar_path + radar_subpath(dt, radar)
    r_rng, r_dt, r_ts, r_velg, r_Z = openRadar(radar_filename)
    rs_dt.append(r_dt)
    rs_ts.append(r_ts)
    rs_velg.append(r_velg)
    rs_Z.append(r_Z)
    print(dt, r_velg.shape, r_Z.shape)
  dt = np.hstack(rs_dt)
  mask = (dt>=start)*(dt<=stop)
  dt = dt[mask]
  ts = np.hstack(rs_ts)[mask]
  vel = np.hstack(rs_velg)[:,mask]
  Z = np.hstack(rs_Z)[:,mask]

  return r_rng, dt, ts, vel, Z


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
  # Unpacking radar file
  print(radar_filename)
  radar_nc = netCDF4.Dataset(radar_filename,"r")
  altitude = 111.0 #float(radar_nc.Altitude.split()[0])
  radar_vars = radar_nc.variables
  radar_dt = netCDF4.num2date(radar_vars['time'][:], radar_vars['time'].units)
  radar_ts = netCDF4.date2num(radar_dt, 'seconds since 1970-01-01 00:00:00')
  radar_range = radar_vars['range'][:] + altitude
  radar_reflectivity = radar_vars['Zg'][:].T
  radar_vel = radar_vars['VELg'][:].T
  yrange = radar_vars['VELg'].yrange
  radar_vel[radar_vel < yrange[0]] = np.nan
  radar_vel[radar_vel > yrange[1]] = np.nan
  radar_nc.close()

  return radar_range, radar_dt, radar_ts, radar_vel, radar_reflectivity