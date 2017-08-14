#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : Union neighbour
Description          : Union neighbour polygon
Arguments            : Shapefiles

                       -------------------
begin                : 2015-12-14
copyright            : (C) 2015 by Luiz Motta
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

#ogr2ogr -overwrite  example01_neighbour.shp example01_neighbour.geojson

import os, sys
import argparse

try:
    from osgeo import ogr
    from osgeo import osr
except ImportError:
    import ogr
    import osr

#DEBUG
pydev_path = '/home/lmotta/eclipse/plugins/org.python.pydev_3.9.2.201502050007/pysrc/'
def startPyDevClient():
  import sys
  sys.path.append(pydev_path)
  started = False
  try:
    import pydevd
    pydevd.settrace(port=5678, suspend=False)
    started = True
  except:
    pass
  return started
###

def run(name_file, quiet_status):

  def printStatus(status, newLine=False):
    if not newLine and quiet_status:
      return

    if newLine:
      ch = "\n"
    else:
      ch = ""
    sys.stdout.write( "\r%s" % ( status.ljust(100) + ch ) )
    sys.stdout.flush()

  def getLayer(name_file):
      inDataSource = driver.Open( name_file, 0 )
      #
      if inDataSource is None:
        printStatus( "File '%s' can't open" % name_file, True )
        return None
      #
      inLayer = inDataSource.GetLayer()
      #
      return ( inDataSource, inLayer)

  def getFeatures(layer, vbuf=0):
    feats = []
    feat = layer.GetNextFeature()
    while feat:
      geom = feat.GetGeometryRef().Clone()
      feats.append( 
        { 'fid': feat.GetFID(),
          'attributes': feat.items(), 
          'geom': geom,'geomBuffer': geom.Buffer( vbuf )
        }
       )
      feat.Destroy()
      feat = layer.GetNextFeature()

    layer.ResetReading()

    return feats

  def createOutLayer(spatialRef, suffix, fields, geomType):
    ( path_file, ext ) = os.path.splitext( name_file )
    outFile = "%s_%s%s" % ( path_file, suffix, ext )
    #
    if os.path.exists( outFile ):
      driver.DeleteDataSource( outFile )
    #
    outDataSource = driver.CreateDataSource( outFile )
    #
    if outDataSource is None:
      printStatus( "File '%s' not be created" % outFile, True )
      return None
    #
    outLayer = outDataSource.CreateLayer( outFile, srs=spatialRef, geom_type=geomType )
    #
    if outLayer is None:
      printStatus( "File '%s' not be created" % outFile, True )
      return None
    #
    for item in fields:
      f = ogr.FieldDefn( item['name'], item['type'] ) 
      if item.has_key( 'width' ):
        f.SetWidth( item[ 'width' ] )
      outLayer.CreateField( f )
    #
    return ( outFile, outDataSource, outLayer )

  def addFeaturesOut(f, fid, defnOut):
    feat = ogr.Feature( defnOut )
    feat.SetGeometry( f['geom'] )
    feat.SetFID( f['fid'] )
    for item in f['attributes']:
      feat.SetField( item[ 'name' ], item[ 'value' ])
    outLayer.CreateFeature( feat )
    feat.Destroy()

  def getCoordTransform7390( layer ):
    wkt7390 = 'PROJCS["Brazil / Albers Equal Area Conic (WGS84)",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.01745329251994328,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]],PROJECTION["Albers_Conic_Equal_Area"],PARAMETER["longitude_of_center",-50.0],PARAMETER["standard_parallel_1",10.0],PARAMETER["standard_parallel_2",-40.0],PARAMETER["latitude_of_center",-25.0],UNIT["Meter",1.0]]'
    sr7390 = osr.SpatialReference()
    sr7390.ImportFromWkt( wkt7390 )

    return osr.CreateCoordinateTransformation( layer.GetSpatialRef(), sr7390 )

  def processNeighbour(inFeats, layer, ct):
    def getFeaturesHasRelation(layer, geom, fids=[]):
      layer.SetSpatialFilter( geom )
      feats = []
      feat = layer.GetNextFeature()
      while feat:
        fid =  feat.GetFID()
        if not fid in fids:
          geomf = feat.GetGeometryRef()
          if geomf.Intersects( geom ):
            feats.append( { 'attributes': feat.items(), 'geom': geomf.Clone(), 'fid': fid } )
        feat.Destroy()
        feat = layer.GetNextFeature()

      layer.ResetReading()

      return feats

    def removeFeaturesInNotIntersects(inFeats):
      total = len( inFeats )
      removed = 0
      id = 0
      while True:
        feats = getFeaturesHasRelation( layer, inFeats[ id ]['geomBuffer'], [ inFeats[ id ]['fid'] ] )
        if len( feats ) == 0:
          inFeats[ id ]['geom'].Destroy()
          inFeats[ id ]['geomBuffer'].Destroy()
          inFeats[ id ]['geom'] = None
          inFeats[ id ]['geomBuffer'] = None
          del inFeats[ id ]
          removed += 1
          printStatus( "Removing features that hasn't neighbors (%d / %d)..." % ( removed, total ) )
        else:
          id += 1
        if id == (total - removed ):
          break

    def createOutFeatures(inFeats, ct):
      def getValueEvent(inFeat):
        vdate = inFeat['attributes']['date']
        geom = inFeat['geom'].Clone()
        geom.Transform( ct )
        area = geom.Area() / 10000.0
        geom.Destroy()

        return {'date': vdate, 'area_ha': area }

      def getInitValues(inFeat, id_group):
        outFeat = {}
        outFeat['id_group'] = id_group
        geom = inFeat['geom'].Clone()
        outFeat['geom'] = geom
        outFeat['geomBuffer'] = geom.Buffer( distBuf )
        outFeat['events'] = [ getValueEvent( inFeat ) ]
        outFeat['fids'] = [ inFeat['fid'] ]

        return outFeat

      def addValues(outFeat, inFeat):
        geomUnion =  outFeat['geom'].Union( inFeat['geom'])
        outFeat['geom'].Destroy()
        outFeat['geom'] = geomUnion
        outFeat['geomBuffer'].Destroy()
        outFeat['geomBuffer'] = geomUnion.Buffer( distBuf )
        outFeat['events'].append( getValueEvent( inFeat ) )
        outFeat['fids'].append( inFeat['fid'] )

      def destroyGeommetries(fids, inFeats):
        total = len( fids )
        i = 0
        for item in inFeats:
          if item['fid'] in fids:
            i += 0
            item['geom'].Destroy()
            item['geom'] = None
            if i == total:
              break

      def getSumSameDates( events ):
        new_events = []
        dates = map( lambda x: x['date'], events )
        dates = list( set( dates ) )
        for item1 in dates:
          f_dates = filter( lambda x: x['date'] == item1, events )
          if len( f_dates ) == 1:
            total_area_ha = f_dates[0]['area_ha']  
          else:
            total_area_ha = 0
            for item2 in f_dates:
              total_area_ha += item2['area_ha'] 
          event = { 'date': item1, 'area_ha': total_area_ha } 
          new_events.append( event )

        return new_events

      total = len( inFeats )
      outFeats = []
      id_group = 0
      loop = True
      while loop:
        loop = False
        for item in inFeats:
          feats = getFeaturesHasRelation( layer, item['geomBuffer'], [ item['fid'] ] )
          if len( feats ) == 0:  # Always has feats?
            break
          # Add from Query inFeats
          id_group += 1
          printStatus( "Interations: %d <> %d (Remaining Features)" % ( id_group, len( inFeats ) ) )
          outFeat = getInitValues( item, id_group )
          # FID's for remove inFeats
          for item2 in feats:
            addValues( outFeat, item2 )
          # Add from Query by outFeat
          while True:
            feats = getFeaturesHasRelation( layer, outFeat['geomBuffer'],  outFeat['fids'] )
            if len( feats ) == 0:
              break
            for item2 in feats:
              addValues( outFeat, item2 )
          #
          destroyGeommetries( outFeat['fids'], inFeats )
          outFeats.append( outFeat )
          inFeats = filter( lambda x: not x['geom'] is None, inFeats )
          current = len( inFeats )
          if current > 0:
            loop = True
          break # NEWs values of inFeats!

      # Remove duplicate date in events, if has only one day remove item 
      hasDestroy = False 
      for item in outFeats:
        events = getSumSameDates( item['events'])
        del item['events']
        if len( events ) == 1:
          hasDestroy = True
          item['geom'].Destroy()
          item['geom'] = None
        else:
          item['events'] = events
      if hasDestroy:
        outFeats = filter( lambda x: not x['geom'] is None, outFeats )

      return ( outFeats, inFeats )

    removeFeaturesInNotIntersects( inFeats )

    return createOutFeatures( inFeats, ct )

  def getSumEvents(outFeat):
    events = sorted( outFeat['events'], key=lambda x: x['date'] )
    num_events = len( events )
    date_ini = events[0]['date']
    date_end = events[num_events - 1]['date']
    area_ini_ha = events[0]['area_ha']
    #
    dates_events = date_ini
    area_end_ha = area_ini_ha
    area_events_ha = "%f" % area_ini_ha
    for item in events[1:]:
      dates_events = "%s;%s" % ( dates_events, item['date'] )
      area_end_ha += item['area_ha']
      area_events_ha = "%s;%f" % ( area_events_ha, item['area_ha'] )
    #
    s_fids = ';'.join( map( lambda item: str(item), outFeat['fids'] ) )
    #
    return { 
      'n_events': num_events,
      'ini_date': date_ini,
      'end_date': date_end,
      'ini_ha': area_ini_ha,
      'end_ha': area_end_ha,
      'n_fids': len( outFeat['fids'] ),
      'fids': s_fids,
      'dates_ev': dates_events,
      'ha_ev': area_events_ha
    }


  #startPyDevClient()

  ogr.RegisterAll()
  driver = ogr.GetDriverByName( "ESRI Shapefile" )

  if not os.path.exists( name_file ):
    printStatus( "File '%s' not exist" % name_file, True )
    return 1

  # Input
  data = getLayer( name_file )
  if data is None:
    return 1
  ( inDataSource, inLayer ) = data

  distBuf = 0.00014 # 1 sec(1/2) = (1 / (60*60) degree) / 2
  printStatus( "Reading features..." )
  inFeats = getFeatures( inLayer, distBuf )

  # Output
  fields = [
    { 'name': 'id_group', 'type': ogr.OFTInteger },
    { 'name': 'n_events', 'type': ogr.OFTInteger },
    { 'name': 'ini_date', 'type': ogr.OFTString, 'width': 10 },
    { 'name': 'end_date', 'type': ogr.OFTString, 'width': 10 },
    { 'name': 'ini_ha', 'type': ogr.OFTReal },
    { 'name': 'end_ha', 'type': ogr.OFTReal },
    { 'name': 'n_fids', 'type': ogr.OFTInteger },
    { 'name': 'fids', 'type': ogr.OFTString, 'width': 200 },
    { 'name': 'dates_ev', 'type': ogr.OFTString, 'width': 200 },
    { 'name': 'ha_ev', 'type': ogr.OFTString, 'width': 200 }
  ]
  data = createOutLayer( inLayer.GetSpatialRef(), 'neighbour', fields, ogr.wkbMultiPolygon )
  if data is None:
    return 1
  ( outName, outDataSource, outLayer ) = data
  defnOut = outLayer.GetLayerDefn()

  # Process
  data  = ( outName, len( inFeats ) )
  printStatus( "Processing '%s' (%d features)" % data )
  ( outFeats, inFeats )  = processNeighbour( inFeats, inLayer, getCoordTransform7390( inLayer ) )

  totalOutFeats = len( outFeats )

  # Clean
  for item in inFeats:
    item['geom'].Destroy()
    item['geomBuffer'].Destroy()
  del inFeats[:]

  # Save Features
  fid = 0
  for item in outFeats:
    fid += 1
    sumEvent = getSumEvents( item )
    f = { 'fid': fid, 'geom': item['geom'],
          'attributes': [
            { 'name': 'id_group', 'value': item['id_group'] },
            { 'name': 'n_events', 'value': sumEvent['n_events'] },
            { 'name': 'ini_date', 'value': sumEvent['ini_date'] },
            { 'name': 'end_date', 'value': sumEvent['end_date'] },
            { 'name': 'ini_ha', 'value': sumEvent['ini_ha'] },
            { 'name': 'end_ha', 'value': sumEvent['end_ha'] },
            { 'name': 'n_fids', 'value': sumEvent['n_fids'] },
            { 'name': 'fids', 'value': sumEvent['fids'] },
            { 'name': 'dates_ev', 'value': sumEvent['dates_ev'] },
            { 'name': 'ha_ev', 'value': sumEvent['ha_ev'] }
          ]
        }
    addFeaturesOut( f, fid, defnOut )
    del f['attributes']
    item['geom'].Destroy()
    item['geomBuffer'].Destroy()

  del outFeats[:]

  inDataSource.Destroy()
  outDataSource.Destroy()

  printStatus( "Finish! '%s' (%d features)" % ( outName, totalOutFeats ), True )

  return 0

def main():
  parser = argparse.ArgumentParser(description='Create union neighbour polygon.' )
  parser.add_argument( '-q', '--quiet', action="store_false", help='Hides the processing status' )
  parser.add_argument( 'shape', metavar='Shapefile', type=str, help='Name of shapefile' )

  args = parser.parse_args()
  return run( args.shape,not args.quiet )

if __name__ == "__main__":
    sys.exit( main() )
