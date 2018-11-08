import netCDF4
import numpy as np
from datetime import datetime, timedelta
import glob

# Setting some paths
meteo_path = '/data/data_hatpro/jue/cloudnet/juelich/processed/categorize/'
meteo_time = '%Y%m%d'
# '/data/data_hatpro/jue/cloudnet/juelich/processed/categorize/2018/20181103_juelich_categorize.nc'
mira36_path = '/data/hatpro/jue/data/mmclx/incoming/'
mira36_time = '%Y%m%d_%H%M'
# '/data/hatpro/jue/data/mmclx/incoming/20181103_1200.znc'
mira10_path = '/data/obs/site/jue/joyrad10/'
mira10_time = '%Y%m%d_%H%M%S'
# '/data/obs/site/jue/joyrad10/2018/11/08/20181108_020012.znc'


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


def getRadarData(start, stop, radar='mira36'):
  def radar_subpath(dt,radar):
    if radar == 'mira36':
      return dt.strftime(mira36_time) + '.znc'
    elif radar == 'mira10':
      return dt.strftime('%Y/%m/%d/'+mira10_time) + '.znc'
    else:
      raise ValueError('Unrecognized radar name {}'.format(radar))
  if radar == 'mira36':
    radar_path = mira36_path
    radar_time = mira36_time
    radar_endpath = '*.znc'
    chk_elv = True
  elif radar == 'mira10':
    radar_path = mira10_path
    radar_time = mira10_time
    radar_endpath = '/**/*.znc'
    chk_elv = False
  else:
    raise ValueError('Unrecognized radar name {}'.format(radar))
  files = glob.glob(radar_path+str(start.year-1)+radar_endpath, recursive=True)
  files = files + glob.glob(radar_path+str(start.year)+radar_endpath, recursive=True)
  files = files + glob.glob(radar_path+str(start.year+1)+radar_endpath, recursive=True)
  files = [i for i in files if 'solscan' not in i]
  datetimes = [datetime.strptime(i[(-len(radar_time)-6):-4],radar_time) for i in files]
  datetimes = [i for i in datetimes if i >= start and i <= stop]

  rs_dt = []
  rs_ts = []
  rs_azimuth = []
  rs_elevation = []
  rs_velg = []
  for dt in datetimes:
    radar_filename = radar_path + radar_subpath(dt, radar)
    print(radar_filename)
    try:
      r_rng, r_dt, r_ts, r_azimuth, r_elevation, r_velg = openRadar(radar_filename, check_elevation=chk_elv)
      rs_dt.append(r_dt)
      rs_ts.append(r_ts)
      rs_azimuth.append(r_azimuth)
      rs_elevation.append(r_elevation)
      rs_velg.append(r_velg)
    except:
      pass
    print(dt, r_velg.shape)
  dt = np.hstack(rs_dt)
  mask = (dt>=start)*(dt<=stop)
  dt = dt[mask]
  ts = np.hstack(rs_ts)[mask]
  azi = np.hstack(rs_azimuth)[mask]
  elv = np.hstack(rs_elevation)[mask]
  vel = np.hstack(rs_velg)[:,mask]
  return r_rng, dt, ts, azi, elv, vel


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


def openRadar(radar_filename, check_elevation=True):
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
    yrange = radar_vars['VELg'].yrange
  else:
    radar_vel = radar_vars['VELgc'][:].T
    yrange = radar_vars['VELgc'].yrange
  # I have the feeling that even though the declared fill value is 9.9692099e36
  # the used number is -4.22687562e5
  radar_vel[radar_vel < yrange[0]] = np.nan
  radar_vel[radar_vel > yrange[1]] = np.nan
  if check_elevation:
    radar_vel[:,np.abs(radar_elevation-90.0) > 0.1] = np.nan
  radar_nc.close()

  return radar_range, radar_dt, radar_ts, radar_azimuth, radar_elevation, radar_vel