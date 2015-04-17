#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : footprint_extent
Description          : Create extent from image
Arguments            : Image

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

from osgeo import ( gdal, ogr, osr )
import osgeo.gdalconst

def printStatus(status, newLine=False):
  if newLine:
    ch = "\n"
  else:
    ch = ""
  sys.stdout.write( "\r%s" % ( status.ljust(100) + ch ) )
  sys.stdout.flush()


def run( inImage ):

  def getInRaster():
    def getCoordinate( coef, line, col ):
      return { 'x': coef[0] + col * coef[1] + line * coef[2], 'y': coef[3] + col * coef[4] + line * coef[5] }
    #
    gdal.AllRegister()
    ds = gdal.Open( inImage, osgeo.gdalconst.GA_ReadOnly )
    if ds is None:
      return None
    # Spatial Reference
    pr = ds.GetProjectionRef()
    if pr == '':
      return None
    sr = osr.SpatialReference()
    sr.ImportFromWkt( pr )
    #
    coef = ds.GetGeoTransform()
    coordUL = getCoordinate( coef, 0, 0 )
    coordBR = getCoordinate( coef, ds.RasterYSize, ds.RasterXSize )
    #
    ds.FlushCache()
    #
    return ( sr, coordUL, coordBR )

  def createOutLayer():
    ( path_file, ext ) = os.path.splitext( inImage )
    outGeojson = "%s_extent%s" % ( path_file, ".geojson" )
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
    outLayer = outDataSource.CreateLayer( outGeojson, sr, ogr.wkbPolygon )
    if outLayer is None:
      return None
    # Fields
    fieldPath = ogr.FieldDefn( "path", ogr.OFTString)
    outLayer.CreateField( fieldPath )
    fieldImage = ogr.FieldDefn( "image", ogr.OFTString)
    outLayer.CreateField( fieldImage )
    #
    return ( outGeojson, outDataSource, outLayer )

  def createGeom():
    #
    # p2 -- p3
    # |     |
    # p1 -- p4
    #
    p1 = "%f %f" % ( coordUL['x'], coordBR['y'] )
    p2 = "%f %f" % ( coordUL['x'], coordUL['y'] )
    p3 = "%f %f" % ( coordBR['x'], coordUL['y'] )
    p4 = "%f %f" % ( coordBR['x'], coordBR['y'] )
    sWkt = "POLYGON ((%s))" % ", ".join( [ p1, p2, p3, p4, p1 ] )
    geom = ogr.CreateGeometryFromWkt( sWkt )
    geom.AssignSpatialReference( sr )
    return geom

  if not os.path.exists( inImage ):
    printStatus( "File '%s' not exist" % inImage, True )
    return 1

  data = getInRaster()
  if data is None:
    return 1
  ( sr, coordUL, coordBR ) = data

  driveName = "GeoJSON"
  data = createOutLayer()
  if data is None:
    return 1
  ( outGeojson, outDataSource, outLayer ) = data
  # Populate
  featureDefn = outLayer.GetLayerDefn()
  outFeat = ogr.Feature( featureDefn )
  #
  ( path, image) = os.path.split( inImage)
  outFeat.SetField( "path", path )
  outFeat.SetField2( "image", image )
  outFeat.SetGeometry( createGeom() )
  #
  outLayer.CreateFeature( outFeat )
  #
  outFeat.Destroy()
  outDataSource.Destroy()
  #
  printStatus( "Create extent layer: '%s'" % outGeojson, True )
  #
  return 0


def main():
  usage = "usage: %prog image"
  parser = OptionParser(usage)

  # define options
  (opts, args) = parser.parse_args()

  if len(sys.argv) == 1:
    parser.print_help()
    return 1
  elif len(args) == 0:
    print("No image provided. Nothing to do!")
    parser.print_help()
    return 1
  else:
    return run( args[0] )

if __name__ == "__main__":
    sys.exit( main() )
