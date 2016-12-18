#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : check_overlaps
Description          : Check overlaps inside shapefile
Arguments            : Geojson

                       -------------------
begin                : 2016-12-17
copyright            : (C) 2016 by Luiz Motta
email                : motta dot luiz at gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import multiprocessing as mp
from osgeo import gdal, ogr, osr
import os, sys, argparse
sys.modules['osgeo'].gdal.UseExceptions()
sys.modules['osgeo'].gdal.PushErrorHandler('CPLQuietErrorHandler')

class TemporaryLayer(object):
  def __init__(self):
    self.srcFile, self.lyrFile = None, None
    self.srcMem, self.lyrMem = None, None

  def __del__(self):
    self.srcFile, self.lyrFile = None, None
    self.srcMem, self.lyrMem = None, None
    
  def init(self, pathfile):
    def createMemLayer(lyrSource):
      nameDrv, nameLyr = 'memData', 'pipes'
      drv = ogr.GetDriverByName('MEMORY')
      src = drv.CreateDataSource( nameDrv )
      temp = drv.Open( nameDrv, 1 )
      lyr = src.CopyLayer( lyrSource, nameLyr, ['OVERWRITE=YES'] )
      return src, lyr

    if not os.path.isfile( pathfile ):
      msg = "File '{f}' not found.".format( f=pathfile)
      return { 'isOk':False, 'msg': msg }

    self.srcFile = ogr.Open( pathfile )
    self.lyrFile = self.srcFile.GetLayerByIndex(0)
    self.srcMem, self.lyrMem = createMemLayer( self.lyrFile )

    return { 'isOk': True }

  def getFidGeoms(self):
    fids_geom, fids_empty, fids_invalid = [], [], []
    for feat in self.lyrMem:
      fid = feat.GetFID()
      geom = feat.GetGeometryRef()
      if geom.IsEmpty():
        fids_empty.append( { '1_fid': fid } )
        continue
      if not geom.IsValid():
        fids_invalid.append( { '1_fid': fid, '2_wkt': geom.ExportToWkt() } )
        continue
      fids_geom.append( { 'fid': fid, 'geom': geom.Clone() } )
    feat = None
    return {
      'fids_geom': fids_geom,
      'fids_invalid': fids_invalid,
      'fids_empty': fids_empty
    }

  def getLayerTemp(self):
    return self.lyrMem

class Overlaps(object):
  def __init__(self, params):
    """
    params = {
      'lyr',           # for single processing
      'pathfile',      # for multi processing
      'overlaps_fids',
      'cpu_count',     # for multi processing
      'total'
    }
    """
    self.src, self.lyr = None, None
    if params.has_key('lyr'):
      self.lyr = params['lyr']
    else:
      self.src = ogr.Open( params['pathfile'] )
      self.lyr = self.src.GetLayerByIndex(0)
      
    self.sr5880 = osr.SpatialReference()
    self.sr5880.ImportFromEPSG(5880)
    self.overlaps_fids = params['overlaps_fids']
    self.cpu_count = params['cpu_count'] if params.has_key('cpu_count') else 1
      
    self.total = params['total']
    
  def __del__(self):
    self.sr5880 = None
    if not self.src is None:
      self.src, self.lyr = None, None

  def getResult(self, fids_geom):
    def status(c_status):
      c = c_status * self.cpu_count
      p = float( c ) / self.total * 100
      p = int( p )
      if p % 5 > 1:
        return
      fmsg = "Processing (processors = {proc}): {c}/{t} ({perc}%)"
      msg = fmsg.format( proc=self.cpu_count, c=c, t=self.total, perc=p )
      sys.stdout.write( "\r{s:<80}".format( s=msg ) )
      sys.stdout.flush()

    def getFidGeomsFilter(geomFilter):
      self.lyr.SetSpatialFilter( None ) # Clear
      self.lyr.SetSpatialFilter( geomFilter )
      return [ { 'fid': feat.GetFID(), 'geom': feat.GetGeometryRef().Clone() } for feat in self.lyr ]

    def getArea5880(geom):
      geom5880 = geom.Clone()
      geom5880.TransformTo( self.sr5880 )
      return geom5880.GetArea()

    def addPolygons(fid1, fid2, geomCollection):
      for id in xrange( geomCollection.GetGeometryCount() ):
        g = geomCollection.GetGeometryRef( id )
        if ogr.wkbPolygon == g.GetGeometryType():
          wkt = g.ExportToWkt()
          dataOverlaps = {
            '1_fid1': fid1, '2_fid2': fid2,
            '3_area5880': getArea5880( g ), '4_src': 'collection',
            '5_wkt': wkt
          }
          overlaps.append( dataOverlaps )

    overlaps = []
    c_status = 0
    for i in xrange( len( fids_geom ) ):
      fg = fids_geom[ i ]
      c_status += 1
      status( c_status )
      l_filter = getFidGeomsFilter( fg['geom'] )
      for f in l_filter:
        if fg['fid'] == f['fid'] or not fg['geom'].Overlaps( f['geom'] ):
          continue
        fids = ( fg['fid'], f['fid'] ) # Reverse
        if fids in self.overlaps_fids:
          continue
        fids = list( fids)
        fids.reverse()
        fids = tuple( fids )
        self.overlaps_fids.append( fids)
        geom = fg['geom'].Intersection( f['geom'] )
        geomType = geom.GetGeometryType()
        if geomType == ogr.wkbPolygon:
          wkt = geom.ExportToWkt()
          dataOverlaps = {
            '1_fid1': fg['fid'], '2_fid2': f['fid'],
            '3_area5880': getArea5880( geom ), '4_src': 'single',
            '5_wkt': wkt
          }
          overlaps.append( dataOverlaps )
          continue
        if geomType in ( ogr.wkbGeometryCollection, ogr.wkbMultiPolygon ):
          addPolygons( fg['fid'], f['fid'], geom )
        geom.Destroy()
    
    return overlaps

def getOverlapsSingleProcess(fids_geom, lyr):
  data = {
    'lyr': lyr,
    'overlaps_fids': [],
    'total': len( fids_geom ),
  }
  o = Overlaps( data )
  return o.getResult( fids_geom )

def apply_overlaps(data, fids_geom):
  o = Overlaps( data )
  return o.getResult( fids_geom )

def getOverlapsMultiProcess(l_fids_geom, pathfile):
  overlaps = []
  def addOverlaps(l):
     total = len( l ) 
     if total > 0:
       for i in xrange( total ):
         overlaps.append( l[i] )

  cpu_count = len( l_fids_geom )
  total = sum( [ len(l) for l in l_fids_geom ] )
  mgr = mp.Manager()
  data = { # Error for Function and object
    'pathfile': pathfile,
    'overlaps_fids': mgr.list(),
    'cpu_count': cpu_count,
    'total': total
  }
  pool = mp.Pool()
  for id in xrange( cpu_count ):
    pool.apply_async(
      func=apply_overlaps,
      args=( data, l_fids_geom[ id ]),
      callback=addOverlaps
    )
  pool.close()
  pool.join()
  
  return overlaps

def run(pathfile, has_multiproc):
  def summary(dataFids):
    t_v = len( dataFids['fids_geom'] )
    t_i = len( dataFids['fids_invalid'] )
    t_e = len( dataFids['fids_empty'] )
    msg = "\rValid {v}, Invalids {i} and Empty {e}\n".format( v=t_v, i=t_i, e=t_e )
    sys.stdout.write( msg )
    sys.stdout.flush()
    
  def saveFiles():
    def save(l_dic, nameFile):
      c_sep = ';'
      keys = sorted( l_dic[0].keys() )
      header = c_sep.join( [ l[2:] for l in keys ] )
      with open( nameFile, "w") as f:
        text = "{h}\n".format( h=header)
        f.write( text )
        for item in l_dic:
          values = map( lambda k: str( item[ k ] ), keys )
          text = "{v}\n".format( v=c_sep.join( values ) )
          f.write( text )

    savefiles = []
    if len( overlaps ) > 0:
      name = pathfile.replace( ".shp", "_overlap.csv" )
      savefiles.append( name )
      save( overlaps, name )
    if len( dataFids['fids_invalid'] ) > 0:
      name = pathfile.replace( ".shp", "_invalid.csv" )
      savefiles.append( name )
      save( dataFids['fids_invalid'], name )
    if len( dataFids['fids_empty'] ) > 0:
      name = pathfile.replace( ".shp", "_empty.csv" )
      savefiles.append( name )
      save( dataFids['fids_empty'], name )
    
    if len( savefiles ) == 0:
      msg = "\r{s:<80}\n".format(s="None save files")
      sys.stdout.write( msg )
    else:
      msg = "Save files: {f}".format( f=",".join( savefiles ) )
      msg = "\r{s:<80}\n".format( s=msg )
      sys.stdout.write( msg )

  def getPartsList(l, total_parts):
    return [l[i*len(l)//total_parts:(i+1)*len(l)//total_parts] for i in range(total_parts)]

  sys.stdout.write( "Calculating..." )
  sys.stdout.flush()
  
  tl = TemporaryLayer()
  r = tl.init(pathfile)
  if not r['isOk']:
    sys.stderr.write("\r{0}\n".format( r['msg'] ) )
    return 1 
  dataFids = tl.getFidGeoms()

  summary( dataFids )

  overlaps = None
  if not has_multiproc:
    overlaps = getOverlapsSingleProcess( dataFids['fids_geom'], tl.getLayerTemp() )
  else:
    del tl
    ll = getPartsList( dataFids['fids_geom'], mp.cpu_count() )
    del dataFids['fids_geom'][:]
    overlaps = getOverlapsMultiProcess( ll, pathfile )

  saveFiles()

  return 0

def main():
  d = "Check Overlaps Shapefile."
  parser = argparse.ArgumentParser(description=d )
  d = "Pathfile of shapefile"
  parser.add_argument('pathfile', metavar='pathfile', type=str, help=d )
  d = "Multiprocessing"
  parser.add_argument('--multiproc', action='store_true', help=d )
  args = parser.parse_args()
    
  return run( args.pathfile, args.multiproc )

if __name__ == "__main__":
  sys.exit( main() )
