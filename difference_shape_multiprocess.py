#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : difference geom
Description          : Calculate the difference of shapes
Arguments            : Shapefiles

                       -------------------
begin                : 2015-04-08
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

import os, sys
import multiprocessing as mp
import argparse

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

# WORKER
# Use by pool.apply_async (NEED out of fucntion/class)
# pool.apply_async( workerDifference, args = ( (wkbs1, numCPU, wkbs2) ,), callback = worksDiff.append )
def workerDifference(data):
  def isEqualExteriorRing(g1, g2):
    r1 = g1.GetGeometryRef(0)
    r2 = g2.GetGeometryRef(0)

    return r1.Equals( r2 )

  ( wkbs1, numCPU, wkbs2 ) = data
  wkbsDiff = []
  id1 = 0
  geomBk = None
  for item1 in wkbs1:
    id1 += 1
    id2 = 0
    geomDiff = ogr.CreateGeometryFromWkb( item1 ) # Cut with all 'wkbs2'
    totalGeom1 = geomDiff.GetGeometryCount()

    if not geomDiff.IsEmpty():
      for item2 in wkbs2:
        geom = ogr.CreateGeometryFromWkb( item2 )
        id2 += 1
        data = ( numCPU, id1, totalGeom1, id2, geom.GetGeometryCount() )
        printStatus( "CPU %d: Layer 1 feature %d(%d geometries) x Layer 2 feature %d(%d geometries)" % data )

        if not geom.IsEmpty() and not geomDiff.Disjoint( geom ):
          geomBk = geomDiff.Difference( geom )
          geomDiff.Destroy()
          geomDiff = geomBk

        geom.Destroy()
      wkbsDiff.append( geomDiff.ExportToWkb() )

    geomDiff.Destroy()

  return wkbsDiff

def run(shp1, shp2):

  def existShapefiles():
    if not os.path.exists( shp1):
      printStatus( "File '%s' not exist" % shp1, True )
      return False

    if not os.path.exists( shp2):
      printStatus( "File '%s' not exist" % shp2, True )
      return False

    return True

  def getInLayer(shp):
      inDataSource = driver.Open( shp, 0 )
      #
      if inDataSource is None:
        printStatus( "File '%s' can't open" % shp, True )
        return None
      #
      inLayer = inDataSource.GetLayer()
      #
      return ( inDataSource, inLayer)

  def getWkbGeometries(layer):
    wkbs = []
    feat = layer.GetNextFeature()
    while feat:
      geomr = feat.GetGeometryRef()
      wkbs.append( geomr.ExportToWkb() )
      feat.Destroy()
      feat = layer.GetNextFeature()

    return wkbs

  def getPartsList(s, parts):
    return [s[i*len(s)//parts:(i+1)*len(s)//parts] for i in range(parts)]

  def createOutLayer(spatialRef):
    ( path_file, ext ) = os.path.splitext( shp1 )
    shpOut = "%s_diff%s" % ( path_file, ext )
    #
    if os.path.exists( shpOut ):
      driver.DeleteDataSource( shpOut )
    #
    outDataSource = driver.CreateDataSource( shpOut )
    #
    if outDataSource is None:
      printStatus( "File '%s' not be created" % shpOut, True )
      return None
    #
    outLayer = outDataSource.CreateLayer( shpOut, srs=spatialRef, geom_type=ogr.wkbMultiPolygon )
    #
    if outLayer is None:
      printStatus( "File '%s' not be created" % shpOut, True )
      return None
    #
    return ( shpOut, outDataSource, outLayer )

  def addGeomOut(geom, id, defnOut):
    feat = ogr.Feature( defnOut )
    feat.SetGeometry( geom )
    feat.SetFID( id )
    outLayer.CreateFeature( feat )
    feat.Destroy()

  ogr.RegisterAll()
  driver = ogr.GetDriverByName( "ESRI Shapefile" )

  if not existShapefiles():
    return 1

  # Input
  data = getInLayer( shp1 )
  if data is None:
    return 1
  ( inDataSource1, inLayer1 ) = data
  data = getInLayer( shp2 )
  if data is None:
    return 1
  ( inDataSource2, inLayer2 ) = data

  wkbs1 = getWkbGeometries( inLayer1 )
  wkbs2 = getWkbGeometries( inLayer2 )

  # Output
  spatialRef = osr.SpatialReference( inLayer1.GetSpatialRef().ExportToWkt() )
  data = createOutLayer( spatialRef )
  if data is None:
    return 1
  ( shpOut, outDataSource, outLayer ) = data
  defnOut = outLayer.GetLayerDefn()

  # Process
  totalCPU = mp.cpu_count()
  works = getPartsList( wkbs1, totalCPU )

  data  = ( inLayer1.GetName(), inLayer1.GetFeatureCount(), inLayer2.GetName(), inLayer2.GetFeatureCount())
  printStatus( "(1)'%s' (%d features) x (2)'%s' (%d features)" % data , True )
  data = ( outLayer.GetName(),  len( works[0] ) )
  printStatus( "Creating Difference layer '%s' - Processing by CPU: ~%d(1) x all(2)..." % data, True )

  pool = mp.Pool()
  worksDiff = []
  id = 0
  for item in works:
    numCPU = ( id % totalCPU ) + 1
    pool.apply_async( workerDifference, args = ( (item, numCPU, wkbs2) ,), callback = worksDiff.append )
    id += 1
  pool.close()
  pool.join()
  pool = None

  # 
  totalDiffs = 0
  for item1 in worksDiff:
    totalDiffs += len( item ) 

  # Save Difference
  id = 0
  for item1 in worksDiff:
    for item2 in item1:
      id += 1
      geom = ogr.CreateGeometryFromWkb( item2 )
      addGeomOut( geom, id, defnOut )
      geom.Destroy()
    del item1[:]

  # Clean
  del worksDiff
  for item in works:
    del item[:]
  del works
  del wkbs1
  del wkbs2

  inDataSource1.Destroy()
  inDataSource2.Destroy()
  outDataSource.Destroy()

  printStatus( "Finish! Total %d features" % totalDiffs, True )

  return 0

def main():
  parser = argparse.ArgumentParser(description='Calculate difference of GEOM (only One GEOM for layer).')
  parser.add_argument('shapefile1', metavar='Shapefile1', type=str, help='Name of First Shapefile')
  parser.add_argument('shapefile2', metavar='Shapefile2', type=str, help='Name of Second Shapefile')

  args = parser.parse_args()
  return run( args.shapefile1, args.shapefile2 )


if __name__ == "__main__":
    sys.exit( main() )
