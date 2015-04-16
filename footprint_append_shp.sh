#!/bin/bash
#
# ***************************************************************************
# Name                 : Footprint append shapefile
# Description          : Append feature of GeoJSON file to shapefile (if not exist create)
#
# Arguments: 
# $1: Shapefile
# $2: GeoJSON
#
# Dependencies         : gdal 1.10.1(ogr2ogr)
#
# ***************************************************************************
# begin                : 2015-03-02 (yyyy-mm-dd)
# copyright            : (C) 2015 by Luiz Motta
# email                : motta dot luiz at gmail.com
# ***************************************************************************
#
# Revisions
#
# 0000-00-00:
# - None
#
# ***************************************************************************
#
# Example:
#   footprint_append.sh LC8_229-066_20140724_LGN00_r6g5b4.footprint_geojson LC8_footprint.shp
#
# ***************************************************************************
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU General Public License as published by  *
# *   the Free Software Foundation; either version 2 of the License, or     *
# *   (at your option) any later version.                                   *
# *                                                                         *
# ***************************************************************************
#
msg_error(){
  local name_script=$(basename $0)
  echo "Usage: $name_script <footprint_geojson> <shapefile>" >&2
  echo "<shapefile> is the Shapefile with all footprint (NEED have extension 'shp')"
  echo "<footprint_geojson> is the GeoJSON with footprint" >&2
}
#
totalargs=2
#
if [ $# -ne $totalargs ] ; then
  msg_error
  exit 1
fi
#
footprint_geojson=$1
shapefile=$2
#
if [ ! -f "$footprint_geojson" ] ; then
  echo "The file '$footprint_geojson' not exist" >&2
  exit 1
fi
#
if [[ ! $shapefile == *.shp ]] ; then
  msg_error
  exit 1
fi
#
ogr2ogr -update -append -t_srs EPSG:4674 $shapefile $footprint_geojson
