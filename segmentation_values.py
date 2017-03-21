#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : segmentation_values
Description          : Create CSV with values of Segmentation with others images

                       -------------------
Begin                : 2017-03-20
Copyright            : (C) 2016 by Luiz Motta
Email                : motta dot luiz at gmail.com
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

import os, sys, warnings, argparse, numpy as np
from osgeo import gdal, gdalconst, ogr, osr

class MessageProgressStdOut:
  def __init__(self, total, showValue=False):
    """
    total: total of elements
    showValue: If True, write value  
    """
    self.total = total
    self.count = 0
    if showValue:
      self.formatMsg = self._formatMsgValue
      self.formatValue = "{0:0%dd}" % len( str( total ) )
    else:
      self.formatMsg = self._formatMsg

  def _formatMsgValue(self, perc, value):
    svalue =  self.formatValue.format( value )
    return "{0}/{1} - {2:3.0f}%\r".format( svalue, self.total, perc )

  def _formatMsg(self, perc, value):
    return "{0:4.0f}%\r".format( perc )
  
  def write(self, value=None):
    self.count += 1
    perc = float( self.count ) / self.total * 100.00
    sys.stdout.write( self.formatMsg( perc, value ) )
    sys.stdout.flush()

  def reset(self):
    self.count = 0

class SegmentationValues:
  def __init__(self, pathfile):
    """
    pathfile: Path file of image of Segmentation
    """
    self.pathfile = pathfile
    self.arry, self.uniq_count, self.dsImg = [ None ] * 3
    self.nan_stats = {
      'min': np.nanmin, 'max': np.nanmax,
      'mean': np.nanmean, 'median': np.nanmedian
    }
    self.drvShp = ogr.GetDriverByName("ESRI Shapefile")
    self.drvMem = ogr.GetDriverByName("MEMORY")
    self.fieldValue, self.fieldCount = 'vpixel', 'cpixel'

  def __del__(self):
    self.arry, self.uniq_count, self.dsImg = [ None ] * 3

  def init(self):
    arry, ds = self._getArrayDS( self.pathfile )
#    if not np.issubdtype( arry.dtype, np.integer ):
#      msg = "Image '{0}' is not integer".format( self.pathfile )
#      return { 'isOk': False, 'msg': msg }
    if not len( arry.shape ) == 2:
      msg = "Image '{0}' have more ONE band".format( self.pathfile )
      return { 'isOk': False, 'msg': msg }
    
    self.arry, self.dsImg = arry, ds
    self.uniq_count = np.unique( arry, return_counts=True )
    
    return { 'isOk': True }
  
  def _getArrayDS(self, pathfile):
    ds = gdal.Open(pathfile)
    arry = ds.ReadAsArray()
    return arry, ds

  def saveStatisticsCSV(self, pathfile):
    def writeHeader(fOut, keys, nBands, sep):
      header = [ self.fieldValue ]
      for id in xrange( nBands ):
        for k in keys:
          header.append( "B{0}_{1}".format( id+1, k) )
      fOut.write( "{0}\n".format( sep.join( header ) ) )

    def writeStats(fOut, value, arry, keys, sep):
      def getStatsSegmentation(value, arryImage):
        def getStats(data):
          stats = {}
          for k in self.nan_stats.keys():
            stats[ k ] = self.nan_stats[ k ]( data )
          
          return stats

        stats= []
        dataValid = np.where( self.arry == value, 1, np.nan )
        if len( arryImage.shape ) == len( self.arry.shape ):
          data = dataValid * arryImage
          stats.append( getStats( data ) )
        else:
          for id in xrange( arryImage.shape[0] ):
            data = dataValid * arryImage[ id ]
            stats.append( getStats( data ) )

        return stats

      stats = getStatsSegmentation( value, arry )
      values = [ str( value ) ]
      for id in xrange( len( stats ) ):
        for k in keys:
          values.append( str( stats[ id ][ k ] ) )
      fOut.write( "{0}\n".format( sep.join( values ) ) )

    pathfileCSV = "{0}_segmentation.csv".format( os.path.splitext( pathfile )[0] )
    f = open( pathfileCSV, 'w' )
    arry, ds = self._getArrayDS( pathfile )
    keys = sorted( self.nan_stats.keys() )
    sep = ','
    writeHeader( f, keys, ds.RasterCount, sep )
    msgOut = MessageProgressStdOut( self.uniq_count[0].shape[0], True )
    for value in np.nditer( self.uniq_count[0] ):
      py_value = int( value.item(0) )
      msgOut.write( py_value )
      writeStats( f, py_value, arry, keys, sep )
    f.close()
    arry, ds = None, None
    return pathfileCSV

  def saveShapefile(self):
    def createValueMemoryLayer():
      def addFields():
        defns = [
          ogr.FieldDefn( self.fieldValue, ogr.OFTInteger64 ),
          ogr.FieldDefn( self.fieldCount, ogr.OFTInteger64 )
        ]
        layer.CreateFields ( defns )

      srs = osr.SpatialReference()
      srs.ImportFromWkt( self.dsImg.GetProjectionRef() )
      ds = self.drvMem.CreateDataSource( 'memory' )
      nameLayer = os.path.basename( pathfileSHP ).split('.')[0]
      layer = ds.CreateLayer( nameLayer, srs )
      addFields()
      return ds, layer

    def populateCountPixels():
      idFieldValue, idFieldCount = 0, 1 
      arry_value = self.uniq_count[ idFieldValue ]
      arry_count = self.uniq_count[ idFieldCount ] 
      for feat in layer:
        value = feat.GetField( idFieldValue )
        id = np.where( arry_value == value )[0][0]
        v_count = int( arry_count[ id ].item(0) )
        feat.SetField( idFieldCount, v_count )
        layer.SetFeature( feat )
      layer.SyncToDisk()

    pathfileSHP = "{0}.shp".format( os.path.splitext( self.pathfile )[0] )
    if os.path.exists( pathfileSHP ):
      self.drvShp.DeleteDataSource( pathfileSHP )
    dsLayer, layer = createValueMemoryLayer()
    band = self.dsImg.GetRasterBand(1)
    if gdal.Polygonize( band, band, layer, 0, [], callback=None ) == gdalconst.CE_Failure:
      return { 'isOk': False, 'msg': "Error Polygonize" }
    populateCountPixels()
    
    ds = self.drvShp.CopyDataSource( dsLayer, pathfileSHP )
    dsLayer.Destroy()
    ds.Destroy()

    return { 'isOk': True, 'pathfile': pathfileSHP }

def existsFiles(l_pathfiles):
  l_not_exists = []
  for f in l_pathfiles:
    if not os.path.isfile( f ):
      l_not_exists.append( f )
  if len( l_not_exists ) == 0:
    return { 'isOk': True }
  
  msg = "Not exists these files: {0}".format( ','.join( l_pathfiles ) )
  return { 'isOk': False, 'msg': msg }
 
def run(pathfileSegmentation, l_pathfiles, needCreateShape):
  r = existsFiles( [ pathfileSegmentation ] + l_pathfiles )
  if not r['isOk']:
    sys.stderr.write( "{0}\n".format( r['msg'] ) )
    return 1

  cSeg = SegmentationValues( pathfileSegmentation )
  r = cSeg.init()
  if not r['isOk']:
    sys.stderr.write( "{0}\n".format( r['msg'] ) )
    return 1

  for f in l_pathfiles:
    pathfileOut = cSeg.saveStatisticsCSV( f )
    sys.stdout.write("Created CSV '{0}'\n".format( pathfileOut ) )
  
  if needCreateShape:
    sys.stdout.write("Saving shapefile...\r")
    r = cSeg.saveShapefile()
    if not r['isOk']:
      sys.stderr.write( "{0}\n".format( r['msg'] ) )
      return 1
    sys.stdout.write("Created SHP '{0}'\n".format( r['pathfile'] ) )

  del cSeg
  return 0

def main():
  d = "Create CSV with statistics values of segmentation regions."
  parser = argparse.ArgumentParser(description=d )
  d = "Pathfile of segmentation image"
  parser.add_argument('segmentation_img', metavar='segmentation_img', type=str, help=d )
  d = "List of image for statistics"
  parser.add_argument('--images', nargs='+', type=str, required=True, help=d )
  d = "Create Shapefile of segmentation image"
  parser.add_argument('--shape', action="store_true", default=False, help=d )

  args = parser.parse_args()
  return run( args.segmentation_img, args.images, args.shape )

if __name__ == "__main__":
    sys.exit( main() )
