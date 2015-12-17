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
import datetime

try:
    from osgeo import ogr
    from osgeo import osr
except ImportError:
    import ogr
    import osr

def printStatus(status, newLine=False):
  if newLine:
    ch = "\n"
  else:
    ch = ""
  sys.stdout.write( "\r%s" % ( status.ljust(100) + ch ) )
  sys.stdout.flush()

def run(name_file, year):

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

  def getFeatures(layer):
    feats = []
    feat = layer.GetNextFeature()
    while feat:
      geomf = feat.GetGeometryRef()
      feats.append( { 'attributes': feat.items(), 'geom': geomf.Clone() } )
      feat.Destroy()
      feat = layer.GetNextFeature()

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

  def processNeighbour(inFeats, year, ct):
    def removeFeaturesInNotConnect(inFeats):
      for item in inFeats:
        item['isConnect'] = False
      #
      idIni = 0
      for item1 in inFeats:
        idIni += 1
        for item2 in inFeats[idIni:]:
          if item1['isConnect'] and item2['isConnect']:
            continue
          if item1['geom'].Touches( item2['geom'] ):
            item1['isConnect'] = item2['isConnect'] = True
      #
      for item in inFeats:
        if not item['isConnect']:
          item['geom'].Destroy()
          item['geom'] = None
        del item['isConnect']
      #
      return filter( lambda x: not x['geom'] is None, inFeats )

    def unionFeaturesInSameDay(inFeats):
      hasUnion = True
      while hasUnion:
        hasUnion = False
        idIni = 0
        for item1 in inFeats:
          idIni += 1
          if item1['geom'] is None:
            continue
          for item2 in inFeats[idIni:]:
            if item2['geom'] is None:
              continue
            if item1['attributes']['day_of_year'] == item2['attributes']['day_of_year'] and item1['geom'].Touches( item2['geom'] ):
              hasUnion = True
              geom = item1['geom'].Union( item2['geom'] )
              item1['geom'].Destroy()
              item1['geom'] = geom.Clone()
              item2['geom'].Destroy()
              item2['geom'] = None
        if hasUnion:
          inFeats = filter( lambda x: not x['geom'] is None, inFeats )

      return inFeats

    def createOutFeatures(inFeats, ct):
      def getValueEvent(inFeat):
        day = inFeat['attributes']['day_of_year']
        geom = inFeat['geom'].Clone()
        geom.Transform( ct )
        area = geom.Area() / 10000.0
        geom.Destroy()

        return {'day_of_year': day, 'area_ha': area }

      def getInitValues(inFeat, id_connect):
        outFeat = {}
        outFeat['id_connect'] = id_connect
        outFeat['geom'] = inFeat['geom'].Clone()
        outFeat['events'] = [ getValueEvent( inFeat ) ]

        return outFeat

      def addValues(outFeat, inFeat):
        geomUnion =  outFeat['geom'].Union( inFeat['geom'])
        outFeat['geom'].Destroy()
        outFeat['geom'] = geomUnion
        outFeat['events'].append( getValueEvent( inFeat ) )

      # Create List Connect ( save First connection)
      outFeats = []
      id_connect = 0
      idIni = 0
      for item1 in inFeats:
        idIni += 1
        if item1['geom'] is None:
          continue
        for item2 in inFeats[idIni:]:
          if item2['geom'] is None:
            continue
          if item1['geom'].Touches( item2['geom'] ):
            id_connect += 1
            outFeat = getInitValues( item1, id_connect )
            addValues( outFeat, item2 )
            outFeats.append( outFeat )
            item1['geom'].Destroy()
            item1['geom'] = None
            item2['geom'].Destroy()
            item2['geom'] = None
            break
      #
      inFeats = filter( lambda x: not x['geom'] is None, inFeats )

      # 2) Add Neighbours
      hasUnion = True
      while hasUnion:
        hasUnion = False
        idIni = 0
        for item1 in outFeats:
          idIni += 1
          for item2 in inFeats:
            if item2['geom'] is None:
              continue
            if item1['geom'].Touches( item2['geom'] ):
              hasUnion = True
              addValues( item1, item2 )
              item2['geom'].Destroy()
              item2['geom'] = None
        if hasUnion:
          inFeats = filter( lambda x: not x['geom'] is None, inFeats )

      return ( outFeats, inFeats )

    def unionFeaturesOut(outFeats):
      def getSumSameDays( events ):
        new_events = []
        days = map( lambda x: x['day_of_year'], events )
        days = list( set( days ) )
        for item1 in days:
          f_days = filter( lambda x: x['day_of_year'] == item1, events )
          if len( f_days ) == 1:
            total_area_ha = f_days[0]['area_ha']  
          else:
            total_area_ha = 0
            for item2 in f_days:
              total_area_ha += item2['area_ha'] 
          event = { 'day_of_year': item1, 'area_ha': total_area_ha } 
          new_events.append( event )

        return new_events

      # Add Neighbours
      hasUnion = True
      while hasUnion:
        hasUnion = False
        idIni = 0
        for item1 in outFeats:
          idIni += 1
          if item1['geom'] is None:
            continue
          for item2 in outFeats[idIni:]:
            if item2['geom'] is None:
              continue
            if item1['geom'].Touches( item2['geom'] ):
              hasUnion = True
              geomUnion =  item1['geom'].Union( item2['geom'] )
              item1['geom'].Destroy()
              item1['geom'] = geomUnion.Clone()
              item1['events'] += item2['events']
              item2['geom'].Destroy()
              del item2['events']
              item2['geom'] = None
        if hasUnion:
          outFeats = filter( lambda x: not x['geom'] is None, outFeats )

      # Remove duplicate day_of_year in events
      for item in outFeats:
        events = getSumSameDays( item['events'])
        del item['events']
        item['events'] = events

      return outFeats

    inFeats = removeFeaturesInNotConnect( inFeats )
    inFeats = unionFeaturesInSameDay( inFeats )
    ( outFeats, inFeats ) = createOutFeatures( inFeats, ct )
    outFeats = unionFeaturesOut( outFeats )

    return ( outFeats, inFeats )

  def getSumEvents(outFeat):
    def getDate( day ):
      s_jd = "%.04d%.03d" % ( year, day)
      return datetime.datetime.strptime( s_jd, '%Y%j' ).strftime("%Y-%m-%d")

    events = sorted( outFeat['events'], key=lambda x: x['day_of_year'] )
    num_events = len( events )
    day = events[0]['day_of_year']
    date_ini = getDate( day )
    date_end = getDate( events[num_events - 1]['day_of_year'] )
    area_ini_ha = events[0]['area_ha']
    #
    days_events = "%03d" % day
    area_end_ha = area_ini_ha
    area_events_ha = "%f" % area_ini_ha
    for item in events[1:]:
      days_events = "%s;%03d" % ( days_events, item['day_of_year'] )
      area_end_ha += item['area_ha']
      area_events_ha = "%s;%f" % ( area_events_ha, item['area_ha'] )
    #
    return { 
      'num_events': num_events,
      'date_ini': date_ini,
      'date_end': date_end,
      'area_ini_ha': area_ini_ha,
      'area_end_ha': area_end_ha,
      'days_events': days_events,
      'area_events_ha': area_events_ha
    }

  ogr.RegisterAll()
  driver = ogr.GetDriverByName( "GeoJSON" )

  if not os.path.exists( name_file ):
    printStatus( "File '%s' not exist" % name_file, True )
    return 1

  # Input
  data = getLayer( name_file )
  if data is None:
    return 1
  ( inDataSource, inLayer ) = data

  inFeats = getFeatures( inLayer )

  # Output
  wkrSR = inLayer.GetSpatialRef().ExportToWkt() 
  spatialRef = osr.SpatialReference( )
  
  fields = [
    { 'name': 'id_connect', 'type': ogr.OFTInteger },
    { 'name': 'num_events', 'type': ogr.OFTInteger },
    { 'name': 'date_ini', 'type': ogr.OFTString, 'width': 10 },
    { 'name': 'date_end', 'type': ogr.OFTString, 'width': 10 },
    { 'name': 'area_ini_ha', 'type': ogr.OFTReal },
    { 'name': 'area_end_ha', 'type': ogr.OFTReal },
    { 'name': 'days_events', 'type': ogr.OFTString, 'width': 200 },
    { 'name': 'area_events_ha', 'type': ogr.OFTString, 'width': 200 }
  ]
  data = createOutLayer( spatialRef, 'neighbour', fields, ogr.wkbMultiPolygon )
  if data is None:
    return 1
  ( outName, outDataSource, outLayer ) = data
  defnOut = outLayer.GetLayerDefn()

  # Process
  data  = ( outName, inLayer.GetFeatureCount() )
  printStatus( "Processing '%s' (%d features)" % data , True )

  ( outFeats, inFeats )  = processNeighbour( inFeats, year, getCoordTransform7390( inLayer ) )

  totalOutFeats = len( outFeats )

  # Clean
  for item in inFeats:
    item['geom'].Destroy()
  del inFeats[:]

  # Save Features
  fid = 0
  for item in outFeats:
    fid += 1
    sumEvent = getSumEvents( item )
    f = { 'fid': fid, 'geom': item['geom'],
          'attributes': [
            { 'name': 'id_connect', 'value': item['id_connect'] },
            { 'name': 'num_events', 'value': sumEvent['num_events'] },
            { 'name': 'date_ini', 'value': sumEvent['date_ini'] },
            { 'name': 'date_end', 'value': sumEvent['date_end'] },
            { 'name': 'area_ini_ha', 'value': sumEvent['area_ini_ha'] },
            { 'name': 'area_end_ha', 'value': sumEvent['area_end_ha'] },
            { 'name': 'days_events', 'value': sumEvent['days_events'] },
            { 'name': 'area_events_ha', 'value': sumEvent['area_events_ha'] }
          ]
        }
    addFeaturesOut( f, fid, defnOut )
    del f['attributes']
    item['geom'].Destroy()

  del outFeats[:]

  inDataSource.Destroy()
  outDataSource.Destroy()

  printStatus( "Finish! '%s': Total %d features" % ( outName, totalOutFeats ), True )

  return 0

def main():
  parser = argparse.ArgumentParser(description='Create union neighbour polygon.')
  parser.add_argument('geojson', metavar='GeoJSON', type=str, help='Name of GeoJSON file')
  parser.add_argument('year', metavar='Year', type=int, help='Year for julian days')

  args = parser.parse_args()
  return run( args.geojson, args.year )

if __name__ == "__main__":
    sys.exit( main() )
