#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : Bounding box from WKT
Description          : Get region of scene
Arguments            : WKT of regin polygon(EPSG 4326)

                       -------------------
begin                : 2016-08-28
copyright            : (C) 2016 by Luiz Motta
email                : motta dot luiz at gmail.com

 ***************************************************************************/
"""

import sys, argparse

from osgeo import gdal, ogr
gdal.UseExceptions()
gdal.PushErrorHandler('CPLQuietErrorHandler')

def run(wkt):
  geom = ogr.CreateGeometryFromWkt( wkt )
  if geom is None:
    msg = '"%s"' % gdal.GetLastErrorMsg()
    print '{ "isOk": 0, "msg": %s }' % msg
    return 1
  
  ( minX, maxX, minY, maxY )= geom.GetEnvelope()
  geom.Destroy()
  
  #-projwin ulx uly lrx lry
  data = ( minX, maxY, maxX, minY )
  bbox = '"%f %f %f %f"' % data
  print '{ "isOk": 1, "bbox": %s }' % bbox
  
  return 0
  

def main():
  d = 'Print bounding box of WKT({ "isOk": 1, "bbox": "ulx uly lrx lry"}).'
  parser = argparse.ArgumentParser(description=d )
  d = "WKT of geometry"
  parser.add_argument('wkt', metavar='wkt', type=str, help=d )

  args = parser.parse_args()
  return run( args.wkt )

if __name__ == "__main__":
    sys.exit( main() )
