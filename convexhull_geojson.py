#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : convexhull_shp
Description          : Create convex hull
Arguments            : Geojson

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
from optparse import OptionParser
from osgeo import ogr

def printStatus(status, newLine=False):
  if newLine:
    ch = "\n"
  else:
    ch = ""
  sys.stdout.write( "\r%s" % ( status.ljust(100) + ch ) )
  sys.stdout.flush()


def run( inGeojson ):

  def getInLayer():
    inDriver = ogr.GetDriverByName( driveName )
    inDataSource = inDriver.Open( inGeojson, 0 )
    #
    if inDataSource is None:
      return None
    #
    inLayer = inDataSource.GetLayer()
    inDefn = inLayer.GetLayerDefn()
    #
    return ( inDataSource, inLayer, inDefn )

  def createOutLayer():
    ( path_file, ext ) = os.path.splitext( inGeojson )
    outGeojson = "%s_convexhull%s" % ( path_file, ext )
    outDriver = ogr.GetDriverByName( driveName )
    #
    if os.path.exists( outGeojson ):
        outDriver.DeleteDataSource( outGeojson )
    #
    outDataSource = outDriver.CreateDataSource( outGeojson )
    #
    if outDataSource is None:
      return None
    #
    outLayer = outDataSource.CreateLayer( outGeojson, inLayer.GetSpatialRef(), ogr.wkbPolygon )
    #
    if outLayer is None:
      return None
    #
    numFields = inDefn.GetFieldCount()
    for i in range( 0, numFields ):
      outLayer.CreateField( inDefn.GetFieldDefn( i ) )
    #
    return ( outGeojson, outDataSource, outLayer )

  def addConvexHull( inFeat ):
    outFeat = ogr.Feature( inDefn )
    outFeat.SetFrom( inFeat )
    outFeat.SetGeometry( inFeat.GetGeometryRef().ConvexHull() )
    #
    outLayer.CreateFeature( outFeat )
    #
    outFeat.Destroy()

  if not os.path.exists( inGeojson ):
    printStatus( "File '%s' not exist" % inGeojson, True )
    return 1

  driveName = "GeoJSON"

  data = getInLayer()
  if data is None:
    return 1
  ( inDataSource, inLayer, inDefn ) = data

  data = createOutLayer()
  if data is None:
    return 1
  ( outGeojson, outDataSource, outLayer ) = data
  # Populate out layer
  countFeat = 0
  totalFeat = inLayer.GetFeatureCount()
  # Populate convex hull layer
  for inFeat in inLayer:
    countFeat += 1
    printStatus( "%d/%d" % ( countFeat, totalFeat) )
    addConvexHull( inFeat )

  # Close DataSource
  inDataSource.Destroy()
  outDataSource.Destroy()
  #
  printStatus( "Create convex hull layer (convex hull for each feature): '%s'" % outGeojson, True )
  #
  return 0


def main():
  usage = "usage: %prog filename.shp"
  parser = OptionParser(usage)

  # define options
  (opts, args) = parser.parse_args()

  if len(sys.argv) == 1:
    parser.print_help()
    return 1
  elif len(args) == 0:
    print("No Geojson provided. Nothing to do!")
    parser.print_help()
    return 1
  else:
    return run( args[0] )

if __name__ == "__main__":
    sys.exit( main() )
