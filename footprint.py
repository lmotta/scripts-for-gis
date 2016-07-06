#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : footprint
Description          : Create footprint from image
Arguments            : Image

                       -------------------
begin                : 2016-06-23
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

from osgeo import ( gdal, ogr, osr )
from gdalconst import ( GA_ReadOnly, GA_Update )

import os, sys, struct, json
from optparse import OptionParser

class Footprint():
  gdal_sctruct_types = {
    gdal.GDT_Byte: 'B',
    gdal.GDT_UInt16: 'H',
    gdal.GDT_Int16: 'h',
    gdal.GDT_UInt32: 'I',
    gdal.GDT_Int32: 'i',
    gdal.GDT_Float32: 'f',
    gdal.GDT_Float64: 'd'
  }

  def __init__(self, filenameImage):
    self.filename = filenameImage

  def getGeom_NumParts(self):
    def getDatasetMem(datatype):
      ds = drv_mem.Create( '', infoimage['xsize'], infoimage['ysize'], 1, datatype )
      ds.SetProjection( infoimage['wktSRS'] )
      ds.SetGeoTransform( infoimage['transform'] )
      return ds

    def populateMask_origin(datatype_mask):
      xoff, xsize, ysize = 0, infoimage['xsize'], 1
      format_struct_img = self.gdal_sctruct_types[ infoimage['datatype'] ] * xsize * ysize
      format_struct__mask = self.gdal_sctruct_types[ datatype_mask ] * xsize * ysize
      for row in xrange( infoimage['ysize'] ):
        line = band_img.ReadRaster( xoff, row, xsize, ysize, xsize, ysize, infoimage['datatype'] )
        value = list( struct.unpack( format_struct_img, line) )
        del line
        for col in xrange( infoimage['xsize'] ):
          value[ col ] = int( value[ col ] != 0 )
        line = struct.pack( format_struct__mask, *value )
        del value
        band_mask.WriteRaster( xoff, row, xsize, ysize, line )
        del line

    def populateMask1(datatype_mask):
      xoff, xsize, ysize = 0, infoimage['xsize'], 1
      format_struct_img = self.gdal_sctruct_types[ infoimage['datatype'] ] * xsize * ysize
      format_struct__mask = self.gdal_sctruct_types[ datatype_mask ] * xsize * ysize
      for row in xrange( infoimage['ysize'] ):
        line = band_img.ReadRaster( xoff, row, xsize, ysize, xsize, ysize, infoimage['datatype'] )
        value = list( struct.unpack( format_struct_img, line) )
        del line
        for col in xrange( infoimage['xsize'] ):
          value[ col ] = int( value[ col ] != 0 )
        line = struct.pack( format_struct__mask, *value )
        del value
        band_mask.WriteRaster( xoff, row, xsize, ysize, line )
        del line

    def populateMask2(datatype_mask):
      xoff, xsize, ysize = 0, infoimage['xsize'], 1
      format_struct_img = self.gdal_sctruct_types[ infoimage['datatype'] ] * xsize * ysize
      format_struct__mask = self.gdal_sctruct_types[ datatype_mask ] * xsize * ysize
      value_new = []
      for row in xrange( infoimage['ysize'] ):
        line = band_img.ReadRaster( xoff, row, xsize, ysize, xsize, ysize, infoimage['datatype'] )
        value =  list( struct.unpack( format_struct_img, line) )
        del line
        for index, item in enumerate(value):
          value[ index ] = int( value[ index ] != 0 )
        line = struct.pack( format_struct__mask, *value )
        del value
        band_mask.WriteRaster( xoff, row, xsize, ysize, line )
        del line

    def getGeomsSieve():
      srs = osr.SpatialReference()
      srs.ImportFromWkt( infoimage['wktSRS'] )
      drv_poly = ogr.GetDriverByName('MEMORY')
      ds_poly = drv_poly.CreateDataSource('memData')
      layer_poly = ds_poly.CreateLayer( 'memLayer', srs, ogr.wkbPolygon )
      field = ogr.FieldDefn("dn", ogr.OFTInteger)
      layer_poly.CreateField( field )
      idField = 0
      gdal.Polygonize( band_sieve, None, layer_poly, idField, [], callback=None )
      if gdal.GetLastErrorType() != 0:
        return { 'isOk': False, 'msg': gdal.GetLastErrorMsg() }
      geoms = []
      layer_poly.SetAttributeFilter("dn = 1")
      for feat in layer_poly:
        geoms.append( feat.GetGeometryRef().Clone() )
      ds_poly = layer_poly = None

      return { 'isOk': True, 'geoms': geoms }

    ds_img = gdal.Open( self.filename, GA_ReadOnly )
    band_img = ds_img.GetRasterBand( 1 )
    infoimage = { 
      'datatype': band_img.DataType,
      'wktSRS': ds_img.GetProjection(),
      'transform': ds_img.GetGeoTransform(),
      'xsize': ds_img.RasterXSize, 'ysize': ds_img.RasterYSize
    }

    if not infoimage['datatype'] in self.gdal_sctruct_types.keys():
      ds_img = None
      return { 'isOk': False, 'msg': "Type of image not supported"}

    drv_mem = gdal.GetDriverByName('MEM')
    datatype_out = gdal.GDT_Byte
    # Mask
    ds_mask = getDatasetMem( datatype_out )
    band_mask = ds_mask.GetRasterBand(1)
    populateMask2( datatype_out )
    ds_img = band_img = None
    # Sieve
    pSieve = { 'threshold': 100, 'connectedness': 8 }
    ds_sieve = getDatasetMem( datatype_out )
    band_sieve = ds_sieve.GetRasterBand(1)
    gdal.SieveFilter( band_mask, None, band_sieve, pSieve['threshold'], pSieve['connectedness'], [], callback=None )
    ds_mask = band_mask = None
    if gdal.GetLastErrorType() != 0:
      return { 'isOk': False, 'msg': gdal.GetLastErrorMsg() }
    # Geoms
    vreturn = getGeomsSieve()
    ds_sieve = band_sieve = None
    if not vreturn['isOk']:
      return { 'isOk': False, 'msg': vreturn['msg'] }
    geomsSieve = vreturn['geoms']
    numGeoms = len( geomsSieve )
    if numGeoms == 0:
      return { 'isOk': False, 'msg': "Not exist geometry from image '%s'" %  self.filename }

    geomUnion = ogr.Geometry( ogr.wkbMultiPolygon )
    for id in xrange( numGeoms ):
      geomUnion.AddGeometry( geomsSieve[ id ] )

    return { 
      'isOk': True,
      'geom': geomUnion.UnionCascaded(), 
      'numparts': numGeoms,
      'wktSRS': infoimage['wktSRS']
    }

def run( filename ):

  import time

  footprint = Footprint( filename )
  print time.ctime()
  vreturn = footprint.getGeom_NumParts()
  print time.ctime()

  if not vreturn['isOk']:
    print vreturn['msg']
    return
  data = {
     "type": "FeatureCollection",
     "features": [
        {
          "type": "Feature", "properties": {"numparts": vreturn['numparts'] },
          "geometry": json.loads( vreturn['geom'].ExportToJson() )
        }
     ]
  }

  # Json
  filename = os.path.splitext( filename )[0]
  filename = "%s.geojson" % filename
  with open( filename, 'w') as f:
    json.dumps( data, f )

def main():
  usage = "usage: %prog filename.tif"
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

# footprint.py '/home/lmotta/data/landsat_imgs/LC82270612015226LGN00_r6g5b4.tif'
