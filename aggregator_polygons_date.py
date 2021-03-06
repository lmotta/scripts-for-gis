#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : Aggregator polygon date
Description          : Union neighbour polygon
Arguments            : Shapefile and date field

                       -------------------
begin                : 2018-08-24
copyright            : (C) 2018 by Luiz Motta
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

import os, sys, datetime, dateutil.relativedelta
import argparse

try:
    from osgeo import ogr, osr
except ImportError:
    import ogr, osr
     
def run(quiet_status):
  def printStatus(status, newLine=False):
    if not newLine and quiet_status:
      return

    if newLine:
      ch = "\n"
    else:
      ch = ""
    sys.stdout.write( "\r{}".format( status.ljust(100) + ch ) )
    sys.stdout.flush()

  def getLayerPostgres(str_conn, table):
    ds = ogr.Open( str_conn )
    if ds is None:
      return { isOk: False, 'message': "Connection '{}' can't open".format( str_conn ) }
    lyr = ds.GetLayerByName( table)
    if lyr is None:
      return { 'isOk': False, 'message': "Table '{}' from connection '{}' not found".format( table, str_conn ) }
    return { 'isOk': True, 'dataset': ds, 'layer': ds.GetLayer()}

  def checkFields(layer, fields):
    defn = layer.GetLayerDefn()
    for name in fields:
      if defn.GetFieldIndex( name ) == -1:
        return { 'isOk': False, 'message': "Layer '{}' don't have field '{}'".format( layer.GetName(),  name ) }
    return { 'isOk': True }

  def copyMemoryLayer(inLayer, outName):
    driver = ogr.GetDriverByName('MEMORY')
    ds = driver.CreateDataSource('memData')
    driver.Open('memData', 1 ) # Write access
    ds.CopyLayer( inLayer, outName, ['OVERWRITE=YES'] )
    layer = ds.GetLayerByName( outName )
    layer.ResetReading()
    return { 'dataset': ds, 'layer': layer }

  def getFeaturesOrderDate(layer):
    feats = []
    for feat in layer:
      items = feat.items()
      geom = feat.GetGeometryRef().Clone()
      if not geom.IsValid():
        geom = geom.Buffer(0)
      feats.append( 
        { 'fid': feat.GetFID(),
          field_date: datetime.datetime.strptime( items[field_date], '%Y-%m-%d').date(),
          field_type: items[ field_type ],
          field_stage: items[ field_stage ],
          'geom': geom,'geomBuffer': geom.Buffer( vbuffer )
        }
       )
    layer.ResetReading()
    feats.sort( key=lambda i: i[ field_date ] )

    return feats

  def createOutLayer(spatialRef, outFile, fields, geomType):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists( outFile ):
      driver.DeleteDataSource( outFile )
    #
    ds = driver.CreateDataSource( outFile )
    #
    if ds is None:
      return { isOk: False, 'message': "File '{}' not be created".format( outFile ) }
    #
    layer = ds.CreateLayer( outFile, srs=spatialRef, geom_type=geomType )
    #
    if layer is None:
      return { isOk: False, 'message': "File '{}' not be created".format( outFile ) }
    #
    for item in fields:
      f = ogr.FieldDefn( item['name'], item['type'] ) 
      if item.has_key( 'width' ):
        f.SetWidth( item[ 'width' ] )
      layer.CreateField( f )
    #
    return { 'isOk': True, 'dataset': ds, 'layer': layer }

  def addFeaturesOut(layer, f, fid, defnOut):
    feat = ogr.Feature( defnOut )
    feat.SetGeometry( f['geom'] )
    feat.SetFID( f['fid'] )
    for item in f['attributes']:
      feat.SetField( item[ 'name' ], item[ 'value' ])
    layer.CreateFeature( feat )
    feat.Destroy()

  def getCoordTransform7390( layer ):
    wkt7390 = 'PROJCS["Brazil / Albers Equal Area Conic (WGS84)",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.01745329251994328,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]],PROJECTION["Albers_Conic_Equal_Area"],PARAMETER["longitude_of_center",-50.0],PARAMETER["standard_parallel_1",10.0],PARAMETER["standard_parallel_2",-40.0],PARAMETER["latitude_of_center",-25.0],UNIT["Meter",1.0]]'
    sr7390 = osr.SpatialReference()
    sr7390.ImportFromWkt( wkt7390 )

    return osr.CreateCoordinateTransformation( layer.GetSpatialRef(), sr7390 )

  def getAreaHa(geom):
    g = geom.Clone()
    g.Transform( ct1390 )
    area = g.Area() / 10000.0
    g.Destroy()
    return area

  def processNeighbour(inFeats, layer):
    def getValidTypeStage(item):
      vtype  = item[ field_type ]  if not item[ field_type ]  is None else 'SEM Classificação'
      vstage = item[ field_stage ] if not item[ field_stage ] is None else 'SEM Classificação'
      return { 'type': vtype, 'stage': vstage }

    def isInsideLimitMonth( featAggregator, feat):
      dateLast = featAggregator['events'][-1][ field_date ]
      dateFeat = feat[ field_date ]
      date_months = dateLast - dateutil.relativedelta.relativedelta(months=limitMonth)
      return dateFeat > date_months

    def getFeaturesHasRelation(layer, dateReference, geom, fids=[]):
      layer.SetSpatialFilter( geom )
      feats = getFeaturesOrderDate(layer)
      featsRelation = []
      for feat in feats:
        date_months = dateReference + dateutil.relativedelta.relativedelta(months=limitMonth)
        if feat['fid'] in fids or feat[ field_date ] > date_months or not geom.Intersects( feat['geom'] ):
          continue
        dateReference = feat[ field_date ]
        t_s = getValidTypeStage( feat )
        item = {
          field_date: dateReference,
          field_type: t_s['type'], field_stage: t_s['stage'],
          'geom': feat['geom'].Clone(), 'fid': feat['fid'] 
        }
        featsRelation.append( item )

      return featsRelation

    def getInitValues(inFeat):
      outFeat = {}
      outFeat['id_group'] = id_group
      geom = inFeat['geom'].Clone()
      outFeat['geom'] = geom
      outFeat['geomBuffer'] = geom.Buffer( vbuffer )
      t_s = getValidTypeStage( inFeat )
      item = {
        field_date: inFeat[ field_date ],
        'area_ha': getAreaHa( geom ),
        field_type: t_s['type'], field_stage: t_s['stage']
      } 
      outFeat['events'] = [ item ]
      outFeat['fids'] = [ inFeat['fid'] ]

      return outFeat

    def addValues(outFeat, inFeat):
      # NEED use ogr.UseExceptions()
      isOk = True
      try:
        geomUnion =  outFeat['geom'].Union( inFeat['geom'])
      except Exception as e:
        msg = "Error make Union for ID Group {}(used ZERO for FID area): {}".format( id_group, e.message)
        lstExceptionFids[ inFeat['fid'] ] =  msg
        isOk = False
        
      if isOk: 
        if not geomUnion.IsValid():
          geomUnion = geomUnion.Buffer(0)
        outFeat['geom'].Destroy()
        outFeat['geom'] = geomUnion
        outFeat['geomBuffer'].Destroy()
        outFeat['geomBuffer'] = geomUnion.Buffer( vbuffer )
      item = {
        'area_ha': getAreaHa( inFeat['geom'] ) if isOk else 0.00,
        field_date: inFeat[ field_date ],
        field_type: inFeat[ field_type ], field_stage: inFeat[ field_stage ]
      } 
      outFeat['events'].append( item )
      outFeat['fids'].append( inFeat['fid'] )

    def destroyGeometries(fids, inFeats):
      # inFeats
      total = len( fids )
      i = 0
      for item in inFeats:
        if item['fid'] in fids:
          i += 0
          item['geom'].Destroy()
          item['geom'] = None
          if i == total:
            break

    def aggregateSameDates( events ):
      new_events = []
      dates = map( lambda x: x[field_date], events )
      dates = list( set( dates ) )
      for item1 in dates:
        types = []
        stages = []
        f_dates = filter( lambda x: x[field_date] == item1, events )
        if len( f_dates ) == 1:
          total_area_ha = f_dates[0]['area_ha']
          types.append( f_dates[0][ field_type] )
          stages.append( f_dates[0][ field_stage ] )
        else:
          total_area_ha = 0
          for item2 in f_dates:
            total_area_ha += item2['area_ha']
            types.append(  item2[ field_type  ] )
            stages.append( item2[ field_stage ] )
          types  = list( set( types  ) )
          stages = list( set( stages ) )
        event = { field_date: item1, 'area_ha': total_area_ha, field_type: types, field_stage: stages } 
        new_events.append( event )

      return new_events
    
    #  Layer WILL HAVE YOURS FEATURES DELETED !
    total = len( inFeats )
    outFeats = []
    id_group = 0
    loop = True
    while loop:
      loop = False
      for item in inFeats:
        # Add from Query inFeats
        id_group += 1
        printStatus( "Interations: {} <> {} (Remaining Features)".format( id_group, len( inFeats ) ) )
        outFeat = getInitValues( item )
        layer.DeleteFeature( item['fid'] )
        feats = getFeaturesHasRelation( layer, item[ field_date ], item['geomBuffer'], [ item['fid'] ] )
        #
        if len( feats ) > 0:
          for item2 in feats:
            addValues( outFeat, item2 )
            layer.DeleteFeature( item2['fid'] )
          # Add from Query by outFeat
          while True:
            dataRef = outFeat['events'][-1][ field_date ]
            feats = getFeaturesHasRelation( layer, dataRef, outFeat['geomBuffer'],  outFeat['fids'] )
            if len( feats ) == 0:
              break
            for item2 in feats:
              addValues( outFeat, item2 )
              layer.DeleteFeature( item2['fid'] )
        #
        destroyGeometries( outFeat['fids'], inFeats )
        outFeats.append( outFeat )
        inFeats = filter( lambda x: not x['geom'] is None, inFeats )
        if len( inFeats ) > 0:
          loop = True
        break # NEWs values of inFeats!

    for item in outFeats:
      events = aggregateSameDates( item['events'])
      del item['events']
      item['events'] = events
      
      #outFeats = filter( lambda x: not x['geom'] is None, outFeats )

    return ( outFeats, inFeats )

  def getSumEvents(outFeat):
    events = sorted( outFeat['events'], key=lambda x: x[field_date] )
    num_events = len( events )
    date_ini = str( events[0][field_date] )
    date_end = str( events[num_events - 1][field_date] )
    area_ini_ha = events[0]['area_ha']
    #
    dates_events = str( date_ini )
    total_fid_ha = area_ini_ha
    area_events_ha = str( area_ini_ha )
    tipos = list( events[0][ field_type ] )     # See createutFeatures/aggregateSameDates
    estagios = list( events[0][ field_stage ] ) #  Change string to array
    for item in events[1:]:
      dates_events   += ";{}".format( item[ field_date ] )
      total_fid_ha    += item['area_ha']
      area_events_ha += ";{}".format( item['area_ha'] )
      tipos    += item[ field_type ]  # List values
      estagios += item[ field_stage ] # List values
    #
    s_fids    = ';'.join( map( lambda item: str(item), outFeat['fids'] ) )
    s_tipos    = ';'.join( list( set( tipos ) ) )
    s_estagios = ';'.join( list( set( estagios ) ) )
    #
    return { 
      'n_events': num_events,
      'ini_date': date_ini,
      'end_date': date_end,
      'ini_ha': area_ini_ha,
      'fids_ha': total_fid_ha,
      'n_fids': len( outFeat['fids'] ),
      'fids': s_fids,
      'dates_ev': dates_events,
      'ha_ev': area_events_ha,
      'tipos': s_tipos,
      'estagios': s_estagios
    }

  def saveErrorFids(nameFile):
    f = open( nameFile ,"w")
    fids = sorted( lstExceptionFids.keys() )
    for fid in fids:
      line = "FID {}: {}\n".format( fid, lstExceptionFids[ fid ])
      f.write( line )
    f.close


  ogr.RegisterAll()
  ogr.UseExceptions()
  #
  user, pwd = '???', '???'
  str_conn = "PG: host={} dbname={} user={} password={}".format( '10.1.25.143', 'siscom', user, pwd )
  schema = 'temp'
  table = 'alerta_filter'
  d = getLayerPostgres(str_conn, "{}.{}".format( schema, table ) )
  if not d['isOk']:
    printStatus( d['message'], True )
    return 1
  dsPostgres, layer = d['dataset'], d['layer']
  # Variable all scope
  dirOut = "/home/lmotta/Documentos/cotig2018/Agregador_George_2018-08/shp"
  field_date = 'date_img'
  field_type = 'tipo'
  field_stage = 'estagio'
  vbuffer = 0.00014 # 1 sec(1/2) = (1 / (60*60) degree) / 2
  limitMonth = 6
  ct1390 = getCoordTransform7390( layer )
  lstExceptionFids = {}
  #
  d = checkFields( layer, ( field_date,field_type, field_stage ) )
  if not d['isOk']:
    printStatus( d['message'], True )
    return 1
  #
  printStatus( "Copying Database to Memory..." )
  d = copyMemoryLayer( layer, table )
  dsMemory, lyrMem = d['dataset'], d['layer']
  del dsPostgres
  layer = lyrMem
  #
  printStatus( "Reading features..." )
  inFeats = getFeaturesOrderDate( layer )
  msg = "Processing ({} features)...".format( len( inFeats ) )
  printStatus( msg )
  ( outFeats, inFeats )  = processNeighbour( inFeats, layer ) # MEMORY LAYER: it will have your features delete
  totalOutFeats = len( outFeats )
  # Output - Save Shapefile
  fields = [
    { 'name': 'id_group', 'type': ogr.OFTInteger },
    { 'name': 'n_events', 'type': ogr.OFTInteger },
    { 'name': 'ini_date', 'type': ogr.OFTString, 'width': 10 },
    { 'name': 'end_date', 'type': ogr.OFTString, 'width': 10 },
    { 'name': 'ini_ha', 'type': ogr.OFTReal },
    { 'name': 'end_ha', 'type': ogr.OFTReal },
    { 'name': 'fids_ha', 'type': ogr.OFTReal },
    { 'name': 'n_fids', 'type': ogr.OFTInteger },
    { 'name': 'fids', 'type': ogr.OFTString, 'width': 200 },
    { 'name': 'dates_ev', 'type': ogr.OFTString, 'width': 200 },
    { 'name': 'ha_ev', 'type': ogr.OFTString, 'width': 200 },
    { 'name': 'tipos', 'type': ogr.OFTString, 'width': 200 },
    { 'name': 'estagios', 'type': ogr.OFTString, 'width': 200 }
  ]
  outFile = "{}/{}_{}.shp".format( dirOut, table, 'aggregate' )
  d = createOutLayer( layer.GetSpatialRef(), outFile, fields, ogr.wkbMultiPolygon )
  if not d['isOk']:
    printStatus( d['message'], True )
    return 1
  dsShape, outLayer = d['dataset'], d['layer']
  defnOut = outLayer.GetLayerDefn()
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
            { 'name': 'end_ha', 'value': getAreaHa( item['geom'] ) },
            { 'name': 'fids_ha', 'value': sumEvent['fids_ha'] },
            { 'name': 'n_fids', 'value': sumEvent['n_fids'] },
            { 'name': 'fids', 'value': sumEvent['fids'] },
            { 'name': 'dates_ev', 'value': sumEvent['dates_ev'] },
            { 'name': 'ha_ev', 'value': sumEvent['ha_ev'] },
            { 'name': 'tipos', 'value': sumEvent['tipos'] },
            { 'name': 'estagios', 'value': sumEvent['estagios'] }
          ]
        }
    addFeaturesOut( outLayer, f, fid, defnOut )
    del f['attributes']
    item['geom'].Destroy()
    item['geomBuffer'].Destroy()

  del outFeats[:]

  dsShape.Destroy()
  dsMemory.Destroy()

  printStatus( "Finish! '%s' (%d features)" % ( outFile, totalOutFeats ), True )
  
  if len( lstExceptionFids ) > 0:
    nameFile = "{}/{}_{}_errors.txt".format( dirOut, table, 'aggregate' )
    saveErrorFids( nameFile )
    printStatus( "Error! '%s' (%d total)" % ( nameFile, len( lstExceptionFids ) ), True )

  return 0

def main():
  parser = argparse.ArgumentParser(description='Create aggregator polygon.' )
  parser.add_argument( '-q', '--quiet', action="store_false", help='Hides the processing status' )

  args = parser.parse_args()
  return run( not args.quiet )

if __name__ == "__main__":
  sys.exit( main() )
